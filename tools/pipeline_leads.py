#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline_leads — cap-coadă: scrape → (om la mijloc) → generare v2 → git push + verificare live
→ intrare în SITEURI_DE_TESTAT.txt → (după testare) mutare în tested_leads.txt.

Comenzi:
  scrape   caută leads noi (deduplicate față de toate listele) și scrie pending_leads.json
           gata de generat (cu hours_s structurat + preset pe nișă).
             python3 pipeline_leads.py scrape --niches "vulcanizare Bucuresti" --max-per-niche 3
             python3 pipeline_leads.py scrape --niches-file niches.txt
           → REVIZUIEȘTE pending_leads.json (omul de la mijloc), apoi:

  publish  generează mockup-urile v2, face push, așteaptă HTTP 200 live și abia apoi
           scrie intrările (format standard, numerotare continuată) în SITEURI_DE_TESTAT.txt + push.
             python3 pipeline_leads.py publish                 # ia pending_leads.json
             python3 pipeline_leads.py publish alt_fisier.json
             python3 pipeline_leads.py publish --dry-run       # generează local, fără push/listă

  move     după ce ai sunat/testat un lead: mută intrarea din SITEURI_DE_TESTAT.txt
           în tested_leads.txt (cu status) și comite.
             python3 pipeline_leads.py move 23 --status "CONTACTAT — așteaptă răspuns"
             python3 pipeline_leads.py move 23 --status "CLIENT ✔" --no-push
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
# Directorul de lucru = repo-ul TĂU de publicare (mockupuri/ + listele).
# Setează LEADS_WORKDIR ca să NU lucrezi în repo-ul uneltei. Vezi README.
BASE = os.environ.get("LEADS_WORKDIR") or (HERE if os.path.isdir(os.path.join(HERE,"mockupuri")) else os.path.dirname(HERE))
BASE = os.path.abspath(os.path.expanduser(BASE))
LISTA = os.path.join(BASE, "SITEURI_DE_TESTAT.txt")
TESTED = os.path.join(BASE, "tested_leads.txt")
PENDING = os.path.join(BASE, "pending_leads.json")
# --- CONFIG (suprascrie cu variabile de mediu, vezi README) ---
# URL-ul public unde ajung mockup-urile după push (GitHub Pages al repo-ului TĂU).
LIVE_BASE = os.environ.get("LEADS_LIVE_BASE",
                           "https://sol111-afk.github.io/leads-finder/mockupuri").rstrip("/")
if "<" in LIVE_BASE or ">" in LIVE_BASE:
    sys.exit("[!] LEADS_LIVE_BASE pare să conțină placeholder-uri sau caractere greșite:\n"
             "    %s\n"
             "    Exemplu corect: https://utilizator.github.io/leads-numele-tau/mockupuri" % LIVE_BASE)
# Python-ul din venv-ul cu playwright instalat.
VENV_PY = os.environ.get("LEADS_PY", os.path.expanduser("~/.venvs/leads/bin/python"))
if not os.path.exists(VENV_PY):
    VENV_PY = sys.executable

sys.path.insert(0, HERE)
import mockup_gen2 as g2

EMOJI = {"florarie":"💐","cizmarie":"👞","ceasornicarie":"⏱️","tapiterie":"🚗","mobila":"🪑",
         "parbrize":"🚙","vulcanizare":"🛞","electrica_auto":"⚡","detailing":"✨","vopsitorie":"🎨",
         "spalatorie":"💦","optica":"👓","kineto":"💆","reparatii_electro":"🧺","masini_spalat":"🧺",
         "frigidere":"🧺","gsm":"📱","service_auto":"🔧","psihologie":"🧠","stomatologie":"🦷",
         "fotografie":"📷","avocatura":"⚖️","consultanta":"📊"}
CAT_SCURT = {"florarie":"Florărie","cizmarie":"Cizmărie","ceasornicarie":"Ceasornicărie",
             "tapiterie":"Tapițerie auto","mobila":"Mobilă la comandă","parbrize":"Parbrize auto",
             "vulcanizare":"Vulcanizare","electrica_auto":"Electrică auto","detailing":"Detailing auto",
             "vopsitorie":"Vopsitorie auto","spalatorie":"Spălătorie auto","optica":"Optică",
             "kineto":"Kinetoterapie","reparatii_electro":"Reparații electrocasnice","gsm":"Service GSM",
             "service_auto":"Service auto","psihologie":"Psihologie","stomatologie":"Stomatologie",
             "fotografie":"Fotografie de eveniment","avocatura":"Avocatură","consultanta":"Consultanță"}

# ── Mesaje de deschidere per nișă (sursa: docs/MESAJE.md — ține-le sincronizate).
# Placeholder-e: {firma} {link} {rating} {zona}. Dacă un mesaj cere {rating} și
# lead-ul n-are rating valid, cade pe PITCH_FALLBACK.
PITCH_NISA = {
 "parbrize": "Bună ziua! Când îi crapă cuiva parbrizul, caută pe Google și sună primul site care apare. {firma} nu are site, așa că am făcut eu unul de probă, cu telefonul și programul vostru reale: {link}. Dacă vă e util, vorbim. Dacă nu, îl șterg — nicio problemă.",
 "detailing": "Bună ziua! Clienții care plătesc detailing serios se uită întâi cum arăți online. Am văzut că {firma} nu are site și v-am făcut unul de probă — cu recenziile voastre reale de pe Google: {link}. Vă place? Vorbim. Nu? Îl șterg, fără supărare.",
 "vopsitorie": "Bună ziua! O vopsitorie se vinde cu poze — iar {firma} are recenzii excelente și niciun loc unde să le arate. V-am făcut un site de probă cu datele voastre reale: {link}. Dacă vă place, punem pozele lucrărilor voastre. Dacă nu, îl șterg.",
 "spalatorie": "Bună ziua! Am văzut că {firma} nu are site — v-am făcut unul de probă unde clienții văd pachetele și scriu direct pe WhatsApp, fără telefoane pierdute: {link}. Vă e util? Vorbim. Nu? Îl șterg, nicio problemă.",
 "electrica_auto": "Bună ziua! Când rămâne cineva cu mașina moartă, caută pe telefon „electrician auto” și sună ce găsește. {firma} nu apare — n-are site. V-am făcut unul de probă cu numărul vostru real: {link}. Dacă ajută, vorbim; dacă nu, îl șterg.",
 "service_auto": "Bună ziua! {firma} are {rating}★ pe Google — dar un client nou nu vede asta decât dacă vă caută special. V-am făcut un site de probă care pune recenziile în față: {link}. Vă place? Vorbim. Nu? Îl șterg, fără discuții.",
 "cizmarie": "Bună ziua! Oamenii caută „reparații pantofi {zona}” pe Google și nu vă găsesc, deși aveți {rating}★. V-am făcut un site de probă pentru {firma}, cu programul și telefonul vostru: {link}. Dacă vă place, vorbim. Dacă nu, îl șterg — nicio obligație.",
 "ceasornicarie": "Bună ziua! O ceasornicărie cu recenziile voastre merită să fie găsită și de cei care caută pe Google, nu doar de cei care trec prin fața vitrinei. V-am făcut un site de probă pentru {firma}: {link}. Vă place — vorbim. Nu — îl șterg.",
 "tapiterie": "Bună ziua! Tapițeria se vinde cu poze înainte/după — iar {firma} n-are unde să le arate online. V-am făcut un site de probă cu datele voastre reale: {link}. Dacă vă e util, adăugăm lucrările voastre. Dacă nu, îl șterg.",
 "mobila": "Bună ziua! Cine comandă mobilă la comandă vrea întâi să vadă ce ai făcut. {firma} nu are site unde să arate asta — v-am făcut eu unul de probă: {link}. Vă place? Îl umplem cu lucrările voastre. Nu? Îl șterg, nicio problemă.",
 "florarie": "Bună ziua! Florile se comandă pe telefon, în ultimul moment — iar cine nu vă găsește online comandă de la altcineva. V-am făcut un site de probă pentru {firma}, cu buton direct de WhatsApp: {link}. Util? Vorbim. Nu? Îl șterg.",
 "kineto": "Bună ziua! Cineva cu spatele blocat caută „kinetoterapie {zona}” și alege cabinetul care inspiră încredere online. {firma} are {rating}★ și niciun site. V-am făcut unul de probă: {link}. Dacă vă ajută, vorbim. Dacă nu, îl șterg.",
 "reparatii_electro": "Bună ziua! Pe „reparații mașini de spălat” clientul găsește ori anunțuri dubioase, ori firme cu site serios. {firma} are recenzii bune dar nu apare deloc. Site de probă, cu datele voastre: {link}. Util? Vorbim. Nu? Îl șterg.",
 "gsm": "Bună ziua! Cine își sparge ecranul caută service pe telefonul spart 😄 și alege în 2 minute. {firma} nu are site — v-am făcut unul de probă unde clientul întreabă prețul direct pe WhatsApp: {link}. Vă place? Vorbim. Nu? Îl șterg.",
 "optica": "Bună ziua! Am văzut că {firma} nu are site, deși aveți recenzii foarte bune. V-am făcut unul de probă, cu program și programare pe WhatsApp: {link}. Dacă vă e util, vorbim. Dacă nu, îl șterg — fără nicio obligație.",
 "stomatologie": "Bună ziua! Un cabinet cu recenziile dumneavoastră merită o prezență online pe măsură. Mi-am permis să pregătesc o propunere de site pentru {firma}, cu datele publice ale cabinetului: {link}. Dacă vă interesează, discutăm. Dacă nu, o retrag imediat.",
 "psihologie": "Bună ziua! Cine caută un psiholog se uită întâi online, în liniște. Am observat că {firma} nu are site și am pregătit o propunere discretă, doar cu datele publice: {link}. Dacă vă e de folos, vorbim. Dacă nu, o șterg imediat.",
 "fotografie": "Bună ziua! Un fotograf fără site pierde exact clienții care caută „fotograf nuntă”. V-am făcut o propunere pentru {firma}, gândită în jurul galeriei voastre: {link}. Vă place? O umplem cu pozele voastre. Nu? O șterg.",
 "avocatura": "Bună ziua! Un client care caută avocat compară online înainte să sune — iar {firma} nu are site, deși are {rating}★ pe Google. Mi-am permis să pregătesc o propunere, doar cu datele publice ale cabinetului: {link}. Dacă prezintă interes, vă stau la dispoziție pentru o discuție. Dacă nu, o retrag imediat.",
 "consultanta": "Bună ziua! Firmele care caută contabil nou se uită întâi online — iar {firma} nu apare, deși are recenzii excelente. Am pregătit o propunere de site cu datele dumneavoastră publice: {link}. Dacă vă interesează, discutăm pe cifre. Dacă nu, o retrag — fără nicio obligație.",
}
PITCH_NISA["vulcanizare"] = PITCH_NISA["parbrize"]
PITCH_NISA["masini_spalat"] = PITCH_NISA["frigidere"] = PITCH_NISA["reparatii_electro"]
PITCH_FALLBACK = ("Bună ziua! Am văzut că {firma} nu are site, deși are recenzii foarte bune pe Google. "
                  "V-am făcut unul de probă cu datele voastre reale — telefon, program, recenzii: {link}. "
                  "Dacă vă place, vorbim. Dacă nu, îl șterg — nicio problemă.")

def pitch_for(lead, link, zona):
    """Mesajul de deschidere, completat cu datele lead-ului (vezi docs/MESAJE.md)."""
    tpl = PITCH_NISA.get(lead.get("niche_key", ""), PITCH_FALLBACK)
    rating = str(lead.get("rating", "")).replace(".", ",")
    if "{rating}" in tpl and rating in ("", "—", "None"):
        tpl = PITCH_FALLBACK   # mesajul cere rating, lead-ul n-are → varianta sigură
    return tpl.format(firma=lead["name"], link=link, rating=rating, zona=zona)

def run(cmd, **kw):
    print("   $", " ".join(cmd))
    return subprocess.run(cmd, cwd=BASE, **kw)

def _git_out(*a):
    r = subprocess.run(["git"] + list(a), cwd=BASE, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""

def current_branch():
    """Branch-ul curent (nu presupune 'master' — GitHub creează repo-uri cu 'main')."""
    return _git_out("rev-parse", "--abbrev-ref", "HEAD") or "master"

def check_workdir():
    """Verifică unde urmează să comitem. Oprește dacă e repo-ul uneltei sau nu e repo deloc."""
    if not _git_out("rev-parse", "--is-inside-work-tree"):
        sys.exit("[!] %s nu e un repo git.\n"
                 "    Setează LEADS_WORKDIR spre repo-ul TĂU de publicare. Vezi README, secțiunea 1." % BASE)
    origin = _git_out("remote", "get-url", "origin")
    if "leads-toolkit" in origin or "leads-mockup-toolkit" in origin:
        sys.exit("[!] origin = %s\n"
                 "    Ăsta e repo-ul UNELTEI, nu al tău — n-ai ce publica aici.\n"
                 "    Fă-ți un repo public cu Pages și pornește cu:\n"
                 "      export LEADS_WORKDIR=/calea/spre/repo-ul-tau\n"
                 "      export LEADS_LIVE_BASE=https://<user>.github.io/<repo>/mockupuri" % origin)
    return origin

def git_push():
    run(["git", "push", "origin", current_branch()])

def pretty_hours(hours_s, fallback="La programare"):
    if not hours_s: return fallback
    if hours_s == "nonstop": return "NON-STOP (24/7)"
    ZI = {"mon":"Luni","tue":"Marți","wed":"Miercuri","thu":"Joi","fri":"Vineri","sat":"Sâmbătă","sun":"Duminică"}
    ORD = ["mon","tue","wed","thu","fri","sat","sun"]
    def hhmm(x):
        h = int(x); return "%02d:%s" % (h, "30" if (x - h) >= 0.5 else "00")
    def cell(v):
        if v is None: return "Închis"
        if v == [0, 24]: return "Non-Stop"
        return "%s - %s" % (hhmm(v[0]), hhmm(v[1]))
    segs, i = [], 0
    while i < 7:
        j = i
        while j + 1 < 7 and hours_s.get(ORD[j+1]) == hours_s.get(ORD[i]): j += 1
        lbl = ZI[ORD[i]] if i == j else ZI[ORD[i]] + " - " + ZI[ORD[j]]
        segs.append("%s: %s" % (lbl, cell(hours_s.get(ORD[i])))); i = j + 1
    return " | ".join(segs)

def next_number():
    txt = open(LISTA, encoding="utf-8").read()
    nums = [int(m) for m in re.findall(r"^\S+\s+(\d+)\.\s", txt, re.M)]
    return (max(nums) + 1) if nums else 1

def entry_block(nr, lead):
    nk = lead.get("niche_key", "")
    emoji = EMOJI.get(nk, "📍")
    cat = CAT_SCURT.get(nk, nk)
    zona = (re.search(r"Sector\s*\d", lead.get("address", "")) or [None])
    zona = zona.group(0) if hasattr(zona, "group") else (lead.get("addr_city") or "București")
    link = "%s/%s.html" % (LIVE_BASE, lead["slug"])
    rating = str(lead.get("rating", "")).replace(".", ",")
    fb = " (are DOAR pagină de Facebook)" if lead.get("fb_only") else ""
    program = pretty_hours(lead.get("hours_s"), lead.get("program_text") or "La programare")
    azi = date.today().strftime("%Y-%m-%d")
    pitch = pitch_for(lead, link, zona)
    return """
--------------------------------------------------------------------------------
%s %d. %s (%s / %s)
--------------------------------------------------------------------------------
*   Locație: %s
*   Telefon: %s
*   Program de Lucru: %s
*   Link Prototip Live: %s
*   Stare: Activ, NU deține site web propriu%s. Reputație %s★ (%s recenzii Google). Verificat Google Maps %s. Mockup v2 (%s).
*   Pitch (Mesaj WhatsApp de trimis):
%s
""" % (emoji, nr, lead["name"], cat, zona, lead.get("address",""), lead["phone_display"],
       program, link, fb, rating, lead.get("reviews_count",""), azi,
       lead.get("archetype") or g2.NICHE_PRESETS.get(nk,{}).get("archetype","v2"), pitch)

# ─────────────────────────────────────────────── scrape
def cmd_scrape(args):
    out_raw = os.path.join(BASE, "leads_found.json")
    cmd = [VENV_PY, os.path.join(HERE, "scrape_maps_leads.py"),
           "--min-rating", str(args.min_rating), "--min-reviews", str(args.min_reviews),
           "--max-per-niche", str(args.max_per_niche), "--scroll", str(args.scroll),
           "--city", args.city,
           "--out", "leads_found.json"]
    if args.niches: cmd += ["--niches", args.niches]
    elif args.niches_file: cmd += ["--niches-file", args.niches_file]
    else: sys.exit("dă --niches sau --niches-file")
    r = run(cmd)
    if r.returncode != 0: sys.exit("scraper a eșuat")
    leads = g2.from_scraped(out_raw)
    # completează fb_only din raw
    raw = {g2.norm_phone(x["phone"]): x for x in json.load(open(out_raw, encoding="utf-8"))}
    for l in leads:
        src = raw.get(l["phone_wa"][2:])
        if src: l["fb_only"] = src.get("fb_only", False)
    if args.append and os.path.exists(PENDING):
        existing = json.load(open(PENDING, encoding="utf-8"))
        seen = {g2.norm_phone(lead.get("phone_wa", "")[2:]) for lead in existing}
        added = [lead for lead in leads if g2.norm_phone(lead["phone_wa"][2:]) not in seen]
        leads = existing + added
        print("\n[✓] %d leaduri noi adăugate (%d total)" % (len(added), len(leads)))
    json.dump(leads, open(PENDING, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[✓] %d leaduri pregătite → %s" % (len(leads), PENDING))
    print("    Revizuiește copy-ul (omul de la mijloc), apoi: python3 pipeline_leads.py publish")

# ─────────────────────────────────────────────── publish
def wait_live(slugs, tries=30, sleep_s=10):
    import urllib.request
    left = set(slugs)
    for i in range(tries):
        for slug in list(left):
            url = "%s/%s.html" % (LIVE_BASE, slug)
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    if resp.status == 200: left.discard(slug)
            except Exception:
                # Framework Python pe macOS poate pica pe CA certs, deși URL-ul e live.
                # curl folosește trust store-ul sistemului și e mai robust pentru GitHub Pages.
                r = subprocess.run(["curl", "-fsSI", url],
                                   cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if r.returncode == 0: left.discard(slug)
        if not left:
            print("   [✓] toate live (~%ds)" % ((i+1)*sleep_s)); return True
        time.sleep(sleep_s)
    print("   [!] încă ne-live:", ", ".join(left)); return False

def cmd_publish(args):
    if not args.dry_run: check_workdir()
    src = args.json_in or PENDING
    if not os.path.exists(src):
        hint = (
            "[!] Nu găsesc fișierul de publicat:\n"
            "    %s\n\n"
            "    Mai întâi generează-l în repo-ul de lucru:\n"
            "      python3 ~/leads-toolkit/tools/pipeline_leads.py scrape --niches-file ~/leads-toolkit/niches/niches.txt --max-per-niche 3\n\n"
            "    Sau publică explicit un JSON existent:\n"
            "      python3 ~/leads-toolkit/tools/pipeline_leads.py publish /cale/catre/leads.json\n\n"
            "    Repo curent de lucru: %s\n"
            "    Dacă e greșit, setează LEADS_WORKDIR spre repo-ul tău de publicare."
        ) % (src, BASE)
        sys.exit(hint)
    leads = json.load(open(src, encoding="utf-8"))
    if not leads: sys.exit("niciun lead în " + src)
    print("═══ generez %d mockup-uri v2 ═══" % len(leads))
    files = []
    for lead in leads:
        html = g2.build2(lead)
        p = os.path.join(g2.OUT_DIR, lead["slug"] + ".html")
        open(p, "w", encoding="utf-8").write(html)
        files.append("mockupuri/%s.html" % lead["slug"])
        print("✓ %-46s %6d octeți" % (lead["slug"], len(html.encode("utf-8"))))
    if args.dry_run:
        print("\n[dry-run] fără push/listă. Preview intrare pentru primul lead:")
        print(entry_block(next_number(), leads[0]))
        return
    # 1) commit mockupuri (+ push, dacă nu e blocat)
    print("═══ commit mockupuri ═══")
    run(["git", "add"] + files)
    run(["git", "commit", "-q", "-m", "Pipeline: %d mockupuri v2 noi" % len(leads)])
    if args.no_push:
        print("\n[--no-push] comis local, fără push. Verificarea live și lista se sar —\n"
              "            rulează 'publish' fără --no-push când vrei să publici.")
        return
    git_push()
    # 2) verific live
    print("═══ verific live ═══")
    ok = wait_live([l["slug"] for l in leads])
    if not ok and not args.force:
        sys.exit("[!] opresc înainte de listă — rulează din nou publish după ce Pages e ok (sau --force)")
    # 3) abia acum scriu în listă + push
    print("═══ scriu intrările în SITEURI_DE_TESTAT.txt ═══")
    nr = next_number()
    with open(LISTA, "a", encoding="utf-8") as f:
        f.write("\n================================================================================\n")
        f.write("PIPELINE %s\n" % date.today().strftime("%d-%m-%Y"))
        f.write("================================================================================\n")
        for i, lead in enumerate(leads):
            f.write(entry_block(nr + i, lead))
            print("   + %d. %s" % (nr + i, lead["name"]))
    run(["git", "add", "SITEURI_DE_TESTAT.txt"])
    run(["git", "commit", "-q", "-m", "Pipeline: intrari %d-%d in lista" % (nr, nr + len(leads) - 1)])
    git_push()
    os.rename(src, src + ".published") if os.path.exists(src) else None
    print("\n═══ GATA: %d leaduri live + în listă (nr. %d-%d) ═══" % (len(leads), nr, nr + len(leads) - 1))

# ─────────────────────────────────────────────── move
def cmd_move(args):
    if not args.no_push: check_workdir()
    txt = open(LISTA, encoding="utf-8").read()
    # blocul = separatorul dinainte de header-ul cu numărul + tot până la următorul separator/heading
    pat = re.compile(
        r"\n?-{20,}\n\S+\s+%d\.\s[^\n]*\n-{20,}\n.*?(?=\n-{20,}\n\S+\s+\d+\.|\n=+\n|\Z)" % args.numar,
        re.S)
    m = pat.search(txt)
    if not m: sys.exit("nu găsesc intrarea nr. %d în listă" % args.numar)
    block = m.group(0)
    name_m = re.search(r"\d+\.\s+(.+?)(?:\s*\(|\n)", block)
    tel_m = re.search(r"Telefon:\s*([\d\s/]+)", block)
    name = name_m.group(1).strip() if name_m else "?"
    tel = tel_m.group(1).strip() if tel_m else "?"
    txt = txt.replace(block, "")
    open(LISTA, "w", encoding="utf-8").write(txt)
    line = "%03d. %-60s |  Tel: %-22s | Status: %s\n" % (args.numar, name[:60], tel, args.status)
    with open(TESTED, "a", encoding="utf-8") as f:
        f.write(line)
    print("[✓] mutat #%d %s → tested_leads.txt (%s)" % (args.numar, name, args.status))
    if not args.no_push:
        run(["git", "add", "SITEURI_DE_TESTAT.txt", "tested_leads.txt"])
        run(["git", "commit", "-q", "-m", "Pipeline move: #%d %s -> tested (%s)" % (args.numar, name, args.status)])
        git_push()

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scrape")
    s.add_argument("--niches"); s.add_argument("--niches-file")
    s.add_argument("--min-rating", type=float, default=4.0)
    s.add_argument("--min-reviews", type=int, default=10)
    s.add_argument("--max-per-niche", type=int, default=5)
    s.add_argument("--scroll", type=int, default=7)
    s.add_argument("--city", default="Bucuresti",
                   help="oraș adăugat când nișele nu îl includ deja; folosește --city '' pentru nișe cu oraș explicit")
    s.add_argument("--append", action="store_true",
                   help="păstrează pending_leads.json și adaugă numai leadurile noi")
    s.set_defaults(fn=cmd_scrape)
    p = sub.add_parser("publish")
    p.add_argument("json_in", nargs="?")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-push", action="store_true",
                   help="generează + comite local, fără push (și fără listă)")
    p.set_defaults(fn=cmd_publish)
    m = sub.add_parser("move")
    m.add_argument("numar", type=int)
    m.add_argument("--status", default="TESTAT")
    m.add_argument("--no-push", action="store_true")
    m.set_defaults(fn=cmd_move)
    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
