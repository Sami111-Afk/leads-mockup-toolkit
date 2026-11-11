#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper Google Maps pentru leads fără site (leads-finder).
Caută automat, după parametri, firme FĂRĂ site web propriu cu telefon mobil real
și scoate un JSON gata de folosit (opțional și un round<N>.json pentru mockup_gen.py).

Necesită: playwright (venv) + un chromium (îl caută automat în ~/.cache/ms-playwright).

Exemple:
  python scrape_maps_leads.py --niches "tapiterie auto Bucuresti,vulcanizare Bucuresti" \
      --min-rating 4.3 --min-reviews 20 --max-per-niche 5 --out leads_found.json
  python scrape_maps_leads.py --niches-file niches.txt --emit-round 11

Reguli aplicate:
  - exclude firme care au buton Website (feed) ȘI confirmă web=null pe pagina de detaliu
    (feed-ul minte uneori — de-aia verificăm detaliul). Un site = Facebook => marcat fb_only (lead valid).
  - păstrează doar numere MOBILE (07x) implicit -> butonul WhatsApp funcționează
  - deduplică față de listele existente (SITEURI_DE_TESTAT.txt etc.) și intern
  - filtre: rating minim, nr. recenzii minim
"""
import argparse, glob, json, os, re, sys, time

_H=os.path.dirname(os.path.abspath(__file__))
# Directorul de lucru = repo-ul TĂU de publicare (mockupuri/ + listele).
# Setează LEADS_WORKDIR ca să NU lucrezi în repo-ul uneltei. Vezi README.
BASE = os.environ.get("LEADS_WORKDIR") or (_H if os.path.isdir(os.path.join(_H,"mockupuri")) else os.path.dirname(_H))
BASE = os.path.abspath(os.path.expanduser(BASE))

# --- cookie-uri de consimțământ ca să sărim ecranul GDPR (profil nou) ---
CONSENT_COOKIES = [
    {"name":"SOCS","value":"CAISHAgBEhJnd3NfMjAyMzExMjgtMF9SQzIaAmVuIAEaBgiA_LyaBg","domain":".google.com","path":"/"},
    {"name":"CONSENT","value":"YES+cb.20210720-07-p0.en+FX+410","domain":".google.com","path":"/"},
]

def find_chromium():
    pats = [
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome"),
        os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/headless_shell"),
    ]
    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits: return hits[-1]
    return None  # lasă playwright să decidă (dacă are browser propriu)

# --- niche_key + paletă pt mockup_gen (mapare pe cuvinte cheie) ---
NICHE_MAP = [
    (r"stomatolog|dent|implant|ortodont", "stomatologie", "clean"),
    (r"psiholog|psihoterap", "psihologie", "calm"),
    (r"fotograf|foto[ -]?video|nunta|botez", "fotografie", "studio"),
    (r"tapiter",        "tapiterie", "leather"),
    (r"mobil|mobil[ăa]|bucatarie|dressing", "mobila", "leather"),
    (r"detailing|spalatorie auto|car wash|polish", "detailing", "cyber"),
    (r"vopsitorie|tinichigerie|daune",  "vopsitorie", "graphite"),
    (r"electr|diagnoz|mecanic|service auto|parbriz|volan|anvelop|vulcaniz", "auto", "cyber"),
    (r"frigider|masina de spalat|electrocasnic|reparatii",  "reparatii", "fresh"),
    (r"zugrav|amenajari|rigips|gresie|faianta|instalator|casa", "casa", "clean"),
]
def guess_niche(query):
    q = query.lower()
    for rx, nk, pal in NICHE_MAP:
        if re.search(rx, q): return nk, pal
    return "generic", "clean"

def norm_phone(s):
    d = re.sub(r"\D", "", s or "")
    return d[-9:] if len(d) >= 9 else d

def load_existing_phones():
    phones = set()
    for fn in ["SITEURI_DE_TESTAT.txt", "siteuri_clienti.txt", "tested_leads.txt",
               "pending_leads.json", "leads_found.json", "SITEURI.TXT", "agy_lista1"]:
        p = os.path.join(BASE, fn)
        if not os.path.exists(p): continue
        txt = open(p, encoding="utf-8", errors="ignore").read()
        for m in re.findall(r"0[0-9][0-9\s]{7,12}[0-9]", txt):
            phones.add(norm_phone(m))
    return phones

# --- JS extracție feed (rulat în pagină) ---
FEED_JS = r"""
async (opts) => {
  const feed = document.querySelector('[role="feed"]');
  const sleep = ms => new Promise(r=>setTimeout(r,ms));
  for (let i=0;i<opts.scroll;i++){ if(feed){ feed.scrollTop = feed.scrollHeight; } await sleep(1200); }
  const seen = new Set(); const out = [];
  for (const it of document.querySelectorAll('[role="feed"] > div')) {
    const a = it.querySelector('a.hfpxzc'); if(!a) continue;
    const hasWebsite = !!it.querySelector('a[data-value="Website"]');
    const txt = it.innerText.replace(/\n+/g,' | ');
    if (/Sponsored/i.test(txt)) continue;
    const phoneM = txt.match(/0[0-9][0-9\s]{7,12}[0-9]/);
    if(!phoneM) continue;
    const ph = phoneM[0].trim();
    if (opts.mobileOnly && !/^07/.test(ph.replace(/\s/g,''))) continue;
    if (seen.has(ph)) continue; seen.add(ph);
    const rm = txt.match(/([0-9.]+)\((\d[\d,]*)\)/);
    out.push({
      name: (a.getAttribute('aria-label')||'').replace(' · Visited link',''),
      phone: ph, url: a.href, feedHasWebsite: hasWebsite,
      rating: rm?parseFloat(rm[1]):null,
      reviews: rm?parseInt(rm[2].replace(/,/g,'')):0
    });
  }
  return out;
}
"""

DETAIL_JS = r"""
() => {
  const g = s => document.querySelector(s);
  const tbl = g('table');
  return {
    addr: (g('button[data-item-id="address"]')?.getAttribute('aria-label')||'').replace(/^Address:\s*/,'').trim(),
    phone: (g('button[data-item-id^="phone"]')?.getAttribute('aria-label')||'').replace(/^Phone:\s*/,'').trim(),
    web: g('a[data-item-id="authority"]')?.href || null,
    cat: g('button[jsaction*="category"]')?.innerText || null,
    rating: g('div.F7nice')?.innerText.replace(/\n/g,' ') || null,
    hours: tbl ? tbl.innerText.replace(/\n{2,}/g,'\n') : null
  };
}
"""

DAYS = {"Monday":"Luni","Tuesday":"Marți","Wednesday":"Miercuri","Thursday":"Joi",
        "Friday":"Vineri","Saturday":"Sâmbătă","Sunday":"Duminică"}
def fmt_hours(raw):
    if not raw: return "La programare"
    # raw ex: "Wednesday9 am–6 pmThursday9 am–6 pm..."; extragem perechi zi->interval
    DY="Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
    parts = re.findall(rf"({DY})(.*?)(?=(?:{DY})|$)", raw)
    if not parts: return "La programare"
    def conv(t):
        t=t.strip().replace("–","-").replace(" "," ")
        if not t or "Closed" in t: return "Închis"
        if "24 hours" in t or "Open 24" in t: return "Non-Stop"
        def t24(m):
            hh=int(m.group(1)); mm=m.group(2) or "00"; ap=m.group(3).lower()
            if ap=="pm" and hh!=12: hh+=12
            if ap=="am" and hh==12: hh=0
            return f"{hh:02d}:{mm}"
        t=re.sub(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)", t24, t, flags=re.I)
        t=re.sub(r"\s*[–—\-−]\s*", " - ", t)   # normalizează orice liniuță de interval
        return re.sub(r"\s+", " ", t).strip()
    order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    d={k:conv(v) for k,v in parts}
    keys=[k for k in order if k in d]; segs=[]; i=0
    while i<len(keys):
        j=i
        while j+1<len(keys) and d[keys[j+1]]==d[keys[i]]: j+=1
        lbl=DAYS[keys[i]] if i==j else DAYS[keys[i]]+"–"+DAYS[keys[j]]
        segs.append(f"{lbl}: {d[keys[i]]}"); i=j+1
    return " | ".join(segs)


EN2KEY={"Monday":"mon","Tuesday":"tue","Wednesday":"wed","Thursday":"thu","Friday":"fri","Saturday":"sat","Sunday":"sun"}
def parse_hours_struct(raw):
    """'Wednesday9 am-6 pmThursday...' -> {"mon":[9,18],...} | "nonstop" | None.
    Jumătățile de oră devin x.5 (gen2 le afișează HH:30)."""
    if not raw: return None
    DY="Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
    parts=re.findall(rf"({DY})(.*?)(?=(?:{DY})|$)", raw)
    if not parts: return None
    def t24(m):
        hh=int(m.group(1)); mm=int(m.group(2) or 0); ap=m.group(3).lower()
        if ap=="pm" and hh!=12: hh+=12
        if ap=="am" and hh==12: hh=0
        return hh + (0.5 if mm>=30 else 0)
    out={}
    for day,spec in parts:
        k=EN2KEY[day]
        if "Closed" in spec: out[k]=None; continue
        if "24 hours" in spec or "Open 24" in spec: out[k]=[0,24]; continue
        times=[t24(m) for m in re.finditer(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)", spec, re.I)]
        out[k]=[times[0],times[-1]] if len(times)>=2 else None
    if len(out)<7: return None
    if all(v==[0,24] for v in out.values()): return "nonstop"
    return out

def scrape(args):
    from playwright.sync_api import sync_playwright
    exe = find_chromium()
    exclude = load_existing_phones() if args.dedup else set()
    print(f"[i] telefoane excluse (deja în liste): {len(exclude)}")
    seen_global = set(exclude)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed, executable_path=exe)
        ctx = browser.new_context(locale="en-US",
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/1217.0.0.0 Safari/537.36")
        ctx.add_cookies(CONSENT_COOKIES)
        page = ctx.new_page()
        for niche in args.niches:
            nk, pal = guess_niche(niche)
            q = niche if "bucuresti" in niche.lower() or "bucurești" in niche.lower() else f"{niche} {args.city}"
            print(f"\n=== NIȘĂ: {niche}  (niche_key={nk}) ===")
            try:
                page.goto(f"https://www.google.com/maps/search/{q.replace(' ','+')}?hl=en",
                          wait_until="domcontentloaded", timeout=45000)
                page.wait_for_function(
                    "() => document.querySelectorAll('[role=\"feed\"] > div').length > 3",
                    timeout=25000)
            except Exception as e:
                print(f"  [!] nu s-a încărcat feed-ul: {e}"); continue
            cands = page.evaluate(FEED_JS, {"scroll": args.scroll, "mobileOnly": args.mobile})
            # filtre feed
            cands = [c for c in cands
                     if not c["feedHasWebsite"]
                     and (c["rating"] is None or c["rating"] >= args.min_rating)
                     and c["reviews"] >= args.min_reviews
                     and norm_phone(c["phone"]) not in seen_global]
            # sortare: rating*log(reviews) desc
            cands.sort(key=lambda c:( (c["rating"] or 0), c["reviews"]), reverse=True)
            print(f"  candidați feed (fără site, mobil, filtrați): {len(cands)}")
            kept = 0
            for c in cands:
                if kept >= args.max_per_niche: break
                ph = norm_phone(c["phone"])
                if ph in seen_global: continue
                lead = dict(c, niche=niche, niche_key=nk, palette=pal)
                if args.verify:
                    try:
                        page.goto(c["url"], wait_until="domcontentloaded", timeout=40000)
                        page.wait_for_timeout(1200)
                        d = page.evaluate(DETAIL_JS)
                    except Exception as e:
                        print(f"    [skip] detaliu eșuat: {c['name'][:40]} ({e})"); continue
                    web = d.get("web")
                    fb_only = bool(web and "facebook.com" in web)
                    if web and not fb_only:
                        print(f"    [-] ARE site ({web[:40]}): {c['name'][:40]}"); continue
                    lead.update({
                        "address": d.get("addr") or "", "web": web, "fb_only": fb_only,
                        "category": d.get("cat"), "program": fmt_hours(d.get("hours")),
                        "hours_s": parse_hours_struct(d.get("hours")),
                    })
                seen_global.add(ph); kept += 1; results.append(lead)
                tag = " [doar FB]" if lead.get("fb_only") else ""
                print(f"    [+] {c['name'][:50]}  {c['phone']}  {c['rating']}({c['reviews']}){tag}")
        browser.close()
    return results

def emit_round(results, n):
    """Schelet round<N>.json pentru mockup_gen.py (copy generic — pt calitate folosește un LLM)."""
    out=[]
    for r in results:
        slug=re.sub(r"[^a-z0-9]+","_", (r["niche_key"]+"_"+r["name"]).lower()).strip("_")[:60]
        wa="40"+norm_phone(r["phone"]); disp=r["phone"]
        out.append({
            "slug":slug, "palette":r.get("palette","clean"), "niche_key":r["niche_key"],
            "name":r["name"], "brand_short":r["name"][:22], "brand_sub":"București",
            "phone_wa":wa, "phone_display":disp,
            "address":r.get("address") or "București", "addr_line1":(r.get("address") or "").split(",")[0] or "București",
            "addr_city":"București",
            "seo_title":f"{r['name']} — {r['niche']}", "seo_desc":f"{r['name']}, {r['niche']}. {disp}.",
            "eyebrow":r["niche"], "h1":f"{r['name']}", "lead":"Servicii de calitate. Sună sau scrie pe WhatsApp.",
            "chips":["Servicii rapide","Calitate","București & Ilfov"],
            "serv_title":"Servicii", "serv_sub":"Alege serviciul și cere o ofertă pe WhatsApp.",
            "services":[{"title":"Serviciu 1","desc":"Descriere.","tag":"","icon":"check"},
                        {"title":"Serviciu 2","desc":"Descriere.","tag":"","icon":"check"},
                        {"title":"Serviciu 3","desc":"Descriere.","tag":"","icon":"check"},
                        {"title":"Serviciu 4","desc":"Descriere.","tag":"","icon":"check"}],
            "why_title":"De ce noi", "why":[{"title":"Reputație","desc":"Clienți mulțumiți.","icon":"star","filled":True},
                        {"title":"Rapiditate","desc":"Intervenim rapid.","icon":"bolt"},
                        {"title":"Local","desc":"În București.","icon":"pin"}],
            "rating":str(r.get("rating") or "5.0"), "reviews_count":str(r.get("reviews") or 0),
            "areas":["Sector 1","Sector 2","Sector 3","Sector 4","Sector 5 & 6","Ilfov"],
            "areas_title":"Unde lucrăm","areas_sub":"București și Ilfov.",
            "reviews":["Recomand!","Servicii de calitate.","Profesioniști."],
            "contact_sub":"Sună-ne sau scrie pe WhatsApp.",
            "hours":[["Program", r.get("program","La programare"), ""]],
        })
    fn=os.path.join(BASE,f"round{n}.json")
    json.dump(out, open(fn,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n[✓] schelet scris: {fn}  (copy GENERIC — pt calitate rescrie textele cu un LLM înainte de mockup_gen.py)")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--niches", help="listă separată prin virgulă")
    ap.add_argument("--niches-file", help="fișier cu o nișă pe linie")
    ap.add_argument("--city", default="Bucuresti")
    ap.add_argument("--min-rating", type=float, default=4.0)
    ap.add_argument("--min-reviews", type=int, default=10)
    ap.add_argument("--max-per-niche", type=int, default=5)
    ap.add_argument("--scroll", type=int, default=7)
    ap.add_argument("--mobile", action="store_true", default=True, help="doar numere mobile 07x")
    ap.add_argument("--all-phones", dest="mobile", action="store_false")
    ap.add_argument("--no-verify", dest="verify", action="store_false", default=True,
                    help="nu deschide pagina de detaliu (mai rapid, dar mai puțin sigur)")
    ap.add_argument("--no-dedup", dest="dedup", action="store_false", default=True)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--out", default="leads_found.json")
    ap.add_argument("--emit-round", type=int, help="schelet round<N>.json în format v1 (mockup_gen.py, DEPRECAT — pt v2 folosește mockup_gen2.py --from-scraped)")
    args=ap.parse_args()
    if args.niches_file:
        args.niches=[l.strip() for l in open(args.niches_file,encoding="utf-8") if l.strip() and not l.startswith("#")]
    elif args.niches:
        args.niches=[x.strip() for x in args.niches.split(",") if x.strip()]
    else:
        ap.error("dă --niches sau --niches-file")
    res=scrape(args)
    json.dump(res, open(os.path.join(BASE,args.out),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n═══ TOTAL leads găsiți: {len(res)} → {args.out} ═══")
    if args.emit_round and res: emit_round(res, args.emit_round)

if __name__=="__main__":
    main()
