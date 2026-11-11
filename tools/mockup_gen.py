#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator mockup-uri leads-finder.
Un singur template (calitate florsimintex), parametrizat: paletă + date reale per business.
Butoane tel:/wa.me/Maps generate automat din telefonul & adresa reală.

Usage:
    python mockup_gen.py leads.json
unde leads.json = listă de obiecte (schema în DATA_SCHEMA de mai jos).
Scrie fiecare mockup în mockupuri/<slug>.html
"""
import json, sys, os
from string import Template
from urllib.parse import quote

_H=os.path.dirname(os.path.abspath(__file__))
# Directorul de lucru = repo-ul TĂU de publicare (mockupuri/ + listele).
# Setează LEADS_WORKDIR ca să NU lucrezi în repo-ul uneltei. Vezi README.
BASE = os.environ.get("LEADS_WORKDIR") or (_H if os.path.isdir(os.path.join(_H,"mockupuri")) else os.path.dirname(_H))
BASE = os.path.abspath(os.path.expanduser(BASE))
OUT_DIR = os.path.join(BASE, "mockupuri")

# ---------------------------------------------------------------- PALETE
# fiecare paletă definește aceleași nume de variabile → restul CSS e comun.
PALETTES = {
 "leather": dict(  # piele/tan — tâmplărie, mobilă, tapițerie, ateliere premium
   bg="#1b1510", bg2="#20190f", surface="#251d15", surface2="#2c2216",
   line="#3a2c1c", line2="#4d3b24", text="#f5ecdd", muted="#bdab90", muted2="#8e7c62",
   accent="#dd9a44", accent_soft="#f2c184", accent2="#c1602f", accent_ink="#241708", accent_deep="#8a5a22",
   font_display="'Fraunces',Georgia,serif", font_body="'Manrope',system-ui,sans-serif",
   fonts="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap",
   hero_grad="linear-gradient(180deg,rgba(14,11,7,.3) 0%,rgba(14,11,7,.55) 45%,rgba(14,11,7,.95) 100%)"),
 "cyber": dict(  # negru + albastru electric — detailing, auto tech
   bg="#0c0f14", bg2="#0f141b", surface="#141a22", surface2="#1a222c",
   line="#233040", line2="#33465c", text="#eaf1f8", muted="#9fb2c6", muted2="#6d8298",
   accent="#3aa0ff", accent_soft="#8bc6ff", accent2="#00d0c0", accent_ink="#04121f", accent_deep="#1d5fa8",
   font_display="'Sora',system-ui,sans-serif", font_body="'Inter',system-ui,sans-serif",
   fonts="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap",
   hero_grad="linear-gradient(180deg,rgba(6,9,13,.28) 0%,rgba(6,9,13,.55) 45%,rgba(6,9,13,.95) 100%)"),
 "clean": dict(  # alb/gri deschis + teal — studio, servicii curate
   bg="#f6f7f9", bg2="#eef1f4", surface="#ffffff", surface2="#f2f5f8",
   line="#e2e7ec", line2="#cfd7df", text="#141a20", muted="#566372", muted2="#8895a3",
   accent="#0fae9e", accent_soft="#12c7b4", accent2="#e0a53a", accent_ink="#ffffff", accent_deep="#0b8577",
   font_display="'Sora',system-ui,sans-serif", font_body="'Inter',system-ui,sans-serif",
   fonts="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap",
   hero_grad="linear-gradient(180deg,rgba(10,20,20,.15) 0%,rgba(10,20,20,.45) 50%,rgba(10,18,18,.86) 100%)"),
 "fresh": dict(  # albastru + verde fresh — reparații, servicii casă la domiciliu
   bg="#0e1620", bg2="#111c28", surface="#152232", surface2="#1b2c40",
   line="#24384f", line2="#345070", text="#eaf2fa", muted="#a2b6ca", muted2="#6f869d",
   accent="#2e8fe0", accent_soft="#7cc0f5", accent2="#37c86b", accent_ink="#04121f", accent_deep="#1c68a8",
   font_display="'Sora',system-ui,sans-serif", font_body="'Inter',system-ui,sans-serif",
   fonts="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap",
   hero_grad="linear-gradient(180deg,rgba(8,14,20,.3) 0%,rgba(8,14,20,.55) 45%,rgba(8,14,20,.95) 100%)"),
 "graphite": dict(  # grafit/argintiu + roșu siguranță — vopsitorie, service, industrial
   bg="#121417", bg2="#16181c", surface="#1b1e23", surface2="#22262c",
   line="#2c3138", line2="#3f4650", text="#eef1f4", muted="#a8b0ba", muted2="#727b86",
   accent="#e0483b", accent_soft="#ff7a6e", accent2="#f2b60c", accent_ink="#ffffff", accent_deep="#a52c22",
   font_display="'Sora',system-ui,sans-serif", font_body="'Inter',system-ui,sans-serif",
   fonts="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap",
   hero_grad="linear-gradient(180deg,rgba(8,9,11,.3) 0%,rgba(8,9,11,.55) 45%,rgba(8,9,11,.95) 100%)"),
}

# ---------------------------------------------------------------- ICONITE (viewBox 0 0 48 48, stroke)
ICONS = {
 "phone":'<path d="M14 6l6 1 2 9-5 4a24 24 0 0 0 11 11l4-5 9 2 1 6a4 4 0 0 1-4 4A34 34 0 0 1 10 10a4 4 0 0 1 4-4z"/>',
 "pin":'<path d="M24 44s14-12 14-24a14 14 0 1 0-28 0c0 12 14 24 14 24z"/><circle cx="24" cy="20" r="5"/>',
 "clock":'<circle cx="24" cy="24" r="18"/><path d="M24 13v11l8 5"/>',
 "shield":'<path d="M24 4l16 6v12c0 11-7 17-16 22-9-5-16-11-16-22V10z"/><path d="M17 24l5 5 9-11"/>',
 "bolt":'<path d="M26 4 10 28h10l-2 16 18-26H26z"/>',
 "seat":'<path d="M14 40V22a8 8 0 0 1 8-8h4a8 8 0 0 1 8 8v6h6a4 4 0 0 1 4 4v8"/><path d="M14 40h26"/><path d="M18 14v-4a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4"/>',
 "roof":'<path d="M6 30c0-10 8-18 18-18s18 8 18 18"/><path d="M6 30h36"/><path d="M14 30v-6M24 30v-9M34 30v-6"/>',
 "wheel":'<circle cx="24" cy="24" r="16"/><circle cx="24" cy="24" r="5"/><path d="M24 8v11M24 29v11M8 24h11M29 24h11"/>',
 "spray":'<rect x="16" y="16" width="16" height="26" rx="2"/><path d="M20 16v-4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4"/><path d="M10 20l4 2M9 26h5M10 32l4-2"/>',
 "car":'<path d="M6 32l4-10c1-3 4-5 7-5h14c3 0 6 2 7 5l4 10"/><path d="M6 32h36v4H6z"/><circle cx="14" cy="36" r="3"/><circle cx="34" cy="36" r="3"/>',
 "patch":'<path d="M12 12l24 24"/><path d="M14 20l6 6M20 14l6 6M26 26l6-6M20 32l6-6"/>',
 "sofa":'<path d="M8 26v-4a4 4 0 0 1 4-4h24a4 4 0 0 1 4 4v4"/><path d="M6 26a3 3 0 0 1 3 3v6h30v-6a3 3 0 0 1 3-3v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2z"/><path d="M14 35v4M34 35v4"/>',
 "kitchen":'<rect x="8" y="8" width="32" height="32" rx="2"/><path d="M8 24h32M20 8v16M28 24v16"/><circle cx="14" cy="16" r="1.5"/><circle cx="34" cy="16" r="1.5"/>',
 "wardrobe":'<rect x="12" y="6" width="24" height="36" rx="2"/><path d="M24 6v36"/><circle cx="21" cy="24" r="1.4"/><circle cx="27" cy="24" r="1.4"/>',
 "ruler":'<path d="M4 40h24v-9H8a4 4 0 0 0-4 4z"/><path d="M28 31v-7l9-10 4 3-7 9"/><path d="M4 36h24"/>',
 "washer":'<rect x="10" y="6" width="28" height="36" rx="3"/><circle cx="24" cy="26" r="9"/><circle cx="24" cy="26" r="4"/><circle cx="16" cy="12" r="1.5"/><circle cx="22" cy="12" r="1.5"/>',
 "wrench":'<path d="M32 8a8 8 0 0 0-9 12L8 35a3 3 0 0 0 0 4l1 1a3 3 0 0 0 4 0l15-15a8 8 0 0 0 10-9l-5 5-5-1-1-5z"/>',
 "sparkle":'<path d="M24 6c-6 8-10 13-10 18a10 10 0 0 0 20 0c0-5-4-10-10-18z"/><path d="M20 28a4 4 0 0 0 4 4"/>',
 "gem":'<path d="M14 8h20l8 10-18 22L6 18z"/><path d="M6 18h36M18 8l-4 10 10 22M30 8l4 10-10 22"/>',
 "star":'<path d="M12 2l3 6.5 7 .8-5.2 4.7L18.5 22 12 18.3 5.5 22l1.7-8L2 9.3l7-.8z"/>',
 "check":'<path d="M5 13l4 4 10-12"/>',
 "arrow":'<path d="M5 12h14M13 6l6 6-6 6"/>',
 "doc":'<path d="M14 6h14l8 8v28H14z"/><path d="M28 6v8h8M20 24h12M20 30h12"/>',
 "hammer":'<path d="M28 6l8 8-4 4-8-8z"/><path d="M24 14L8 30a3 3 0 0 0 0 4l2 2a3 3 0 0 0 4 0l16-16"/>',
 "tools":'<path d="M20 10a7 7 0 0 0-9 9l-5 5 4 4 5-5a7 7 0 0 0 9-9l-4 4-4-1-1-4z"/><path d="M28 28l10 10-4 4-10-10z"/>',
}
def icon(key, raw=None):
    return raw if raw else ICONS.get(key, ICONS["check"])

def wa(phone_wa, msg):
    return "https://wa.me/%s?text=%s" % (phone_wa, quote(msg))

STAR5 = ''.join('<svg viewBox="0 0 24 24" class="star" aria-hidden="true">%s</svg>' % ICONS["star"] for _ in range(5))

# ---------------------------------------------------------------- render bucăți
def render_services(d):
    out = []
    for s in d["services"]:
        msg = "Bună ziua! Doresc o ofertă / programare pentru: %s." % s["title"]
        out.append('''
        <article class="card reveal">
          <div class="card-media"><img src="%s" alt="%s — %s" width="800" height="500" loading="lazy"></div>
          <div class="card-body">
            <span class="card-ico"><svg viewBox="0 0 48 48" aria-hidden="true">%s</svg></span>
            <span class="card-tag">%s</span>
            <h3>%s</h3>
            <p>%s</p>
            <a class="card-link" href="%s" target="_blank" rel="noopener">%s <svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></a>
          </div>
        </article>''' % (s["img"], s["title"], d["name"], icon(s.get("icon","check"), s.get("icon_raw")),
                         s.get("tag",""), s["title"], s["desc"], wa(d["phone_wa"], msg),
                         d.get("cta","Cere ofertă"), ICONS["arrow"]))
    return "\n".join(out)

def render_hours(d):
    rows = []
    for label, val, cls in d["hours"]:
        rows.append('<tr><td>%s</td><td class="%s">%s</td></tr>' % (label, cls, val))
    return "\n".join(rows)

def render_areas(d):
    pills = []
    for a in d["areas"]:
        pills.append('<span class="area-pill"><svg viewBox="0 0 48 48" aria-hidden="true">%s</svg>%s</span>'
                     % (ICONS["pin"], a))
    return "\n".join(pills)

def render_ticker(d):
    items = d.get("ticker") or [s["title"] for s in d["services"]]
    one = ''.join('<span>%s</span>' % t for t in items)
    return one + one

def render_chips(d):
    return "\n".join('<li><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg> %s</li>' % (ICONS["check"], c)
                     for c in d["chips"])

def render_stats(d):
    return "\n".join('<div class="stat reveal"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in d["stats"])

def render_reviews(d):
    out = []
    initial = d.get("brand_short", d["name"])[0].upper()
    for q in d["reviews"]:
        out.append('''
        <figure class="review reveal">
          <span class="stars">%s</span>
          <blockquote>%s</blockquote>
          <figcaption><span class="avatar">%s</span><span><b>Client %s</b><i>Recenzie Google</i></span></figcaption>
        </figure>''' % (STAR5, q, initial, d.get("brand_short", d["name"])))
    return "\n".join(out)

def render_why(d):
    out = []
    for w in d["why"]:
        cls = "filled" if w.get("filled") else ""
        out.append('<li class="reveal"><span class="why-ico"><svg class="%s" viewBox="0 0 48 48" aria-hidden="true">%s</svg></span><div><b>%s</b><p>%s</p></div></li>'
                   % (cls, icon(w.get("icon","check"), w.get("icon_raw")), w["title"], w["desc"]))
    return "\n".join(out)

# ---------------------------------------------------------------- POOL IMAGINI (Unsplash, verificate 200)
IMAGE_POOLS = {
 "tapiterie": ["1503376780353-7e6692767b70","1552519507-da3b142c6e3d","1449965408869-eaa3f722e40d","1489824904134-891ab64532f1","1547038577-da80abbc4f19"],
 "mobila":    ["1503602642458-232111445657","1555041469-a586c61ea9bc","1616486338812-3dadae4b4ace","1524758631624-e2822e304c36","1600585154340-be6161a56a0c"],
 "detailing": ["1520340356584-f9917d1eea6f","1552519507-da3b142c6e3d","1605559424843-9e4c228bf1c2","1558618666-fcd25c85cd64","1503736334956-4c8f8e92946d"],
 "auto":      ["1486262715619-67b85e0b08d3","1492144534655-ae79c964c9d7","1493238792000-8113da705763","1503376780353-7e6692767b70","1558618666-fcd25c85cd64"],
 "vopsitorie":["1625047509168-a7026f36de04","1487754180451-c456f719a1fc","1493238792000-8113da705763","1492144534655-ae79c964c9d7","1605559424843-9e4c228bf1c2"],
 "reparatii": ["1581092160562-40aa08e78837","1607472586893-edb57bdc0e39","1620714223084-8fcacc6dfd8d","1558618666-fcd25c85cd64","1596461404969-9ae70f2830c1"],
 "casa":      ["1581578731548-c64695cc6952","1600585154340-be6161a56a0c","1556909212-d5b604d0c90d","1584622650111-993a426fbf0a","1493809842364-78817add7ffb"],
 "generic":   ["1497366216548-37526070297c","1486406146926-c627a92ad1ab","1521737604893-d14cc237f11d","1600585154340-be6161a56a0c","1497366811353-6870744d04b2"],
}
def img_url(photo_id, w=800, q=80):
    return "https://images.unsplash.com/photo-%s?auto=format&fit=crop&w=%d&q=%d" % (photo_id, w, q)

def pool_for(niche_key):
    return IMAGE_POOLS.get(niche_key, IMAGE_POOLS["generic"])

# ---------------------------------------------------------------- TEMPLATE HTML
TEMPLATE = Template(r'''<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${seo_title}</title>
<meta name="description" content="${seo_desc}">
<meta name="theme-color" content="${theme_color}">
<meta property="og:title" content="${og_title}">
<meta property="og:description" content="${seo_desc}">
<meta property="og:type" content="website">
<meta property="og:image" content="${og_image}">
<link rel="preload" as="image" href="${hero_img}" fetchpriority="high">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="${fonts}" rel="stylesheet">
<script type="application/ld+json">${schema_json}</script>
<style>
:root{
  --bg:${bg}; --bg2:${bg2}; --surface:${surface}; --surface2:${surface2};
  --line:${line}; --line2:${line2};
  --text:${text}; --muted:${muted}; --muted2:${muted2};
  --accent:${accent}; --accent-soft:${accent_soft}; --accent2:${accent2};
  --accent-ink:${accent_ink}; --accent-deep:${accent_deep};
  --wa:#25d366;
  --font-display:${font_display};
  --font-body:${font_body};
  --maxw:1180px; --pad:clamp(20px,5vw,44px);
  --r:16px; --r-sm:11px; --r-lg:26px;
  --shadow:0 26px 60px -28px rgba(0,0,0,.55);
  --ease:cubic-bezier(.2,.7,.2,1);
  --hero-grad:${hero_grad};
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{font-family:var(--font-body);background:var(--bg);color:var(--text);
  line-height:1.6;font-size:clamp(1rem,.97rem + .2vw,1.075rem);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;overflow-x:hidden}
img,svg{display:block;max-width:100%}
img{height:auto}
a{color:inherit;text-decoration:none}
ul{list-style:none}
h1,h2,h3{line-height:1.08;font-weight:600}
button{font:inherit;cursor:pointer;border:0;background:none;color:inherit}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:4px}
::selection{background:var(--accent);color:var(--accent-ink)}
.wrap{width:100%;max-width:var(--maxw);margin-inline:auto;padding-inline:var(--pad)}
.section{padding:clamp(64px,9vw,120px) 0}
.section-alt{background:var(--bg2)}
.kicker{font-family:var(--font-body);font-weight:700;text-transform:uppercase;letter-spacing:.24em;
  font-size:.72rem;color:var(--accent);margin-bottom:1rem;display:flex;align-items:center;gap:.7rem}
.kicker::before{content:"";width:26px;height:1px;background:var(--accent);opacity:.75}
.sec-head{max-width:60ch;margin-bottom:clamp(36px,5vw,60px)}
.sec-head h2,.feature-text h2,.contact-text h2{font-family:var(--font-display);font-size:clamp(2rem,1.3rem + 3.2vw,3.4rem);letter-spacing:-.01em;font-weight:600}
.sub{color:var(--muted);font-size:1.08rem;margin-top:1rem;max-width:56ch}
.skip{position:fixed;left:12px;top:-60px;z-index:200;background:var(--accent);color:var(--accent-ink);padding:10px 16px;border-radius:8px;font-weight:700;transition:top .2s}
.skip:focus{top:12px}
.btn{display:inline-flex;align-items:center;gap:.6rem;font-weight:700;font-size:1rem;padding:.85em 1.35em;border-radius:var(--r-sm);transition:transform .2s var(--ease),box-shadow .2s,background .2s,border-color .2s,color .2s;border:1px solid transparent;white-space:nowrap}
.btn svg{width:1.2em;height:1.2em;flex:none}
.btn:active{transform:translateY(1px)}
.btn-call{background:var(--accent);color:var(--accent-ink);box-shadow:0 10px 26px -10px var(--accent)}
.btn-call:hover{transform:translateY(-3px);box-shadow:0 16px 32px -12px var(--accent);background:var(--accent-soft)}
.btn-call svg{fill:currentColor;stroke:none}
.btn-wa{background:var(--wa);color:#053a1c}
.btn-wa svg{fill:currentColor;stroke:none}
.btn-wa:hover{transform:translateY(-3px);box-shadow:0 14px 28px -12px var(--wa)}
.btn-ghost{background:transparent;border-color:var(--line2);color:var(--text)}
.btn-ghost svg{fill:none;stroke:currentColor;stroke-width:2}
.btn-ghost:hover{border-color:var(--accent);color:var(--accent-soft)}
.site-head{position:sticky;top:0;z-index:100;background:color-mix(in srgb,var(--bg) 84%,transparent);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.head-inner{display:flex;align-items:center;justify-content:space-between;gap:20px;height:74px}
.brand{display:flex;align-items:center;gap:.75rem}
.brand-mark{display:grid;place-items:center;width:44px;height:44px;border-radius:12px;flex:none;background:linear-gradient(140deg,var(--accent),var(--accent-deep));color:var(--accent-ink);box-shadow:inset 0 1px 0 rgba(255,255,255,.35)}
.brand-mark svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.brand-txt{display:flex;flex-direction:column;line-height:1}
.brand-txt b{font-family:var(--font-display);font-size:1.4rem;letter-spacing:-.01em;font-weight:700}
.brand-txt i{font-style:normal;font-size:.66rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted2);margin-top:4px}
.nav{display:flex;gap:1.7rem}
.nav a{font-weight:600;font-size:.95rem;color:var(--muted);position:relative;padding:4px 0;transition:color .2s}
.nav a::after{content:"";position:absolute;left:0;right:100%;bottom:-2px;height:2px;background:var(--accent);transition:right .25s var(--ease)}
.nav a:hover{color:var(--text)}
.nav a:hover::after{right:0}
.head-cta{display:flex;align-items:center;gap:12px}
.head-cta .btn-ghost{padding:.6em 1em}
.burger{display:none;flex-direction:column;gap:5px;width:44px;height:44px;align-items:center;justify-content:center;border:1px solid var(--line2);border-radius:11px}
.burger span{width:20px;height:2px;background:var(--text);transition:.25s}
.site-foot{background:var(--bg2);border-top:1px solid var(--line);padding:clamp(40px,6vw,64px) 0 40px}
.foot-inner{display:grid;gap:26px}
.foot-brand{display:flex;align-items:center;gap:.85rem}
.foot-brand .brand-mark{width:48px;height:48px}
.foot-brand b{font-family:var(--font-display);font-size:1.35rem;letter-spacing:-.01em;display:block;font-weight:700}
.foot-brand span{color:var(--muted);font-size:.85rem}
.foot-nav{display:flex;gap:1.5rem;flex-wrap:wrap}
.foot-nav a{color:var(--muted);font-weight:600;font-size:.95rem}
.foot-nav a:hover{color:var(--accent-soft)}
.foot-legal{color:var(--muted2);font-size:.82rem;line-height:1.7;border-top:1px solid var(--line);padding-top:22px}
.reveal{opacity:0;transform:translateY(26px);transition:opacity .7s var(--ease),transform .7s var(--ease)}
.reveal.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}*{animation:none!important}}
.hero{position:relative;min-height:clamp(580px,92vh,880px);display:flex;align-items:flex-end;padding-block:clamp(40px,8vh,90px);overflow:hidden;isolation:isolate}
.hero-media{position:absolute;inset:0;z-index:-2}
.hero-media img{width:100%;height:100%;object-fit:cover;object-position:center 46%}
.hero-overlay{position:absolute;inset:0;z-index:-1;background:var(--hero-grad)}
.hero-inner{position:relative;max-width:780px}
.eyebrow{display:inline-flex;align-items:center;gap:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.16em;font-size:.76rem;color:var(--accent-ink);background:var(--accent);padding:.5em 1em;border-radius:999px;margin-bottom:1.4rem}
.ping{width:9px;height:9px;border-radius:50%;background:var(--accent-ink);animation:ping 1.9s infinite}
@keyframes ping{0%{box-shadow:0 0 0 0 rgba(0,0,0,.35)}70%{box-shadow:0 0 0 11px rgba(0,0,0,0)}100%{box-shadow:0 0 0 0 rgba(0,0,0,0)}}
.hero h1{font-family:var(--font-display);color:#fff;font-weight:700;font-size:clamp(2.6rem,1.3rem + 6vw,5.2rem);letter-spacing:-.02em;text-shadow:0 6px 34px rgba(0,0,0,.6)}
.hero h1 em{font-style:italic;color:var(--accent-soft)}
.hero .lead{color:#ece5d8;font-size:clamp(1.05rem,1rem + .5vw,1.28rem);max-width:58ch;margin:1.4rem 0 2rem;text-shadow:0 2px 12px rgba(0,0,0,.6)}
.hero-actions{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:1.9rem}
.hero-actions .btn{font-size:1.06rem;padding:1em 1.5em}
.hero-chips{display:flex;flex-wrap:wrap;gap:.6rem 1.5rem;color:#fff}
.hero-chips li{display:inline-flex;align-items:center;gap:.45rem;font-weight:600;font-size:.92rem;text-shadow:0 2px 10px rgba(0,0,0,.7)}
.hero-chips svg{width:18px;height:18px;fill:none;stroke:var(--accent-soft);stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
.ticker{background:var(--accent);color:var(--accent-ink);overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent);mask-image:linear-gradient(90deg,transparent,#000 6%,#000 94%,transparent)}
.ticker-track{display:flex;gap:0;width:max-content;animation:scroll 32s linear infinite}
.ticker:hover .ticker-track{animation-play-state:paused}
.ticker-track span{display:inline-flex;align-items:center;gap:.5rem;padding:.7em 1.5em;font-family:var(--font-display);font-size:1.1rem;font-weight:700;white-space:nowrap}
.ticker-track span::after{content:"";width:5px;height:5px;border-radius:50%;background:currentColor;opacity:.5;margin-left:1.3em}
@keyframes scroll{to{transform:translateX(-50%)}}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:clamp(14px,2vw,28px);margin-top:clamp(48px,7vw,76px)}
.stat{text-align:center;padding:18px 8px}
.stat b{display:block;font-family:var(--font-display);font-size:clamp(2.1rem,1.4rem + 3vw,3.6rem);line-height:1;color:var(--accent-soft);font-weight:700;letter-spacing:-.01em}
.stat span{display:block;color:var(--muted);font-size:.82rem;margin-top:.55rem;text-transform:uppercase;letter-spacing:.09em;font-weight:600}
.services{display:grid;gap:clamp(16px,2vw,24px);grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);overflow:hidden;display:flex;flex-direction:column;transition:transform .3s var(--ease),border-color .3s,box-shadow .3s;position:relative}
.card:hover{transform:translateY(-6px);border-color:color-mix(in srgb,var(--accent) 55%,var(--line));box-shadow:var(--shadow)}
.card-media{aspect-ratio:16/10;overflow:hidden;background:var(--surface2)}
.card-media img{width:100%;height:100%;object-fit:cover;transition:transform .6s var(--ease)}
.card:hover .card-media img{transform:scale(1.06)}
.card-body{padding:26px;display:flex;flex-direction:column;flex:1;gap:.5rem}
.card-ico{display:grid;place-items:center;width:52px;height:52px;border-radius:13px;margin-bottom:.4rem;background:color-mix(in srgb,var(--accent) 16%,transparent);color:var(--accent-soft)}
.card-ico svg{width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.card-tag{font-size:.68rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--accent2)}
.card h3{font-family:var(--font-display);font-size:1.4rem;font-weight:700;letter-spacing:-.01em}
.card p{color:var(--muted);font-size:.96rem;flex:1}
.card-link{display:inline-flex;align-items:center;gap:.45rem;font-weight:700;color:var(--text);margin-top:.5rem;align-self:flex-start}
.card-link svg{width:18px;height:18px;fill:none;stroke:var(--accent);stroke-width:2.4;transition:transform .25s var(--ease)}
.card-link:hover{color:var(--accent-soft)}
.card-link:hover svg{transform:translateX(5px)}
.feature{display:grid;grid-template-columns:1fr 1.05fr;gap:clamp(30px,5vw,70px);align-items:center}
.feature-media{position:relative;border-radius:var(--r-lg);overflow:hidden;box-shadow:var(--shadow)}
.feature-media img{width:100%;aspect-ratio:3/4;object-fit:cover}
.feature-badge{position:absolute;left:18px;bottom:18px;display:flex;align-items:center;gap:.7rem;background:var(--accent);color:var(--accent-ink);padding:.8rem 1.1rem;border-radius:14px;box-shadow:0 12px 30px rgba(0,0,0,.45)}
.feature-badge svg{width:28px;height:28px;fill:currentColor;stroke:none}
.feature-badge b{font-family:var(--font-display);font-size:1.4rem;font-weight:700;display:block;line-height:1}
.feature-badge span{font-size:.74rem;opacity:.85}
.why{display:grid;gap:1.3rem;margin:2rem 0}
.why li{display:flex;gap:1rem}
.why-ico{flex:none;display:grid;place-items:center;width:48px;height:48px;border-radius:12px;background:color-mix(in srgb,var(--accent) 15%,transparent);color:var(--accent-soft)}
.why-ico svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.why-ico svg.filled{fill:currentColor;stroke:none}
.why b{font-size:1.1rem;display:block;margin-bottom:.15rem;font-family:var(--font-body);font-weight:700}
.why p{color:var(--muted);font-size:.95rem}
.areas{display:flex;flex-wrap:wrap;gap:.7rem;margin-bottom:2.4rem}
.area-pill{display:inline-flex;align-items:center;gap:.45rem;padding:.6em 1.15em;border-radius:999px;border:1px solid var(--line2);background:var(--surface);font-weight:600;transition:.25s}
.area-pill:hover{border-color:var(--accent);color:var(--accent-soft);transform:translateY(-2px)}
.area-pill svg{width:16px;height:16px;fill:none;stroke:var(--accent);stroke-width:2}
.map-cta{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:18px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:clamp(20px,3vw,30px)}
.map-cta b{font-size:1.15rem}
.map-cta span{display:block;color:var(--muted);font-size:.92rem}
.rating-line{display:flex;align-items:center;gap:.6rem;margin-top:1rem;color:var(--muted);flex-wrap:wrap}
.rating-line b{color:var(--text)}
.stars{display:inline-flex;gap:2px}
.stars .star{width:18px;height:18px;fill:var(--accent);stroke:none}
.reviews{display:grid;gap:clamp(16px,2vw,22px);grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.review{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:28px;display:flex;flex-direction:column;gap:1rem}
.review .stars .star{width:20px;height:20px}
.review blockquote{font-size:1.08rem;line-height:1.55;flex:1;font-family:var(--font-display);font-weight:500;font-style:italic;color:var(--text)}
.review figcaption{display:flex;align-items:center;gap:.7rem}
.avatar{display:grid;place-items:center;width:44px;height:44px;border-radius:50%;background:linear-gradient(140deg,var(--accent),var(--accent-deep));color:var(--accent-ink);font-weight:800;font-size:1.05rem;flex:none}
.review figcaption b{display:block}
.review figcaption i{font-style:normal;color:var(--muted);font-size:.85rem}
.review-note{margin-top:1.6rem;color:var(--muted2);font-size:.86rem;display:flex;align-items:center;gap:.5rem}
.review-note svg{width:16px;height:16px;fill:var(--accent);stroke:none;flex:none}
.contact-inner{display:grid;grid-template-columns:1.1fr .9fr;gap:clamp(30px,5vw,60px);align-items:start}
.contact-actions{display:flex;flex-wrap:wrap;gap:14px;margin:1.8rem 0}
.contact-actions .btn{font-size:1.06rem;padding:1em 1.5em}
.contact-list{display:grid;gap:.9rem}
.contact-list li{display:flex;align-items:center;gap:.8rem;color:var(--muted)}
.contact-list svg{width:22px;height:22px;fill:none;stroke:var(--accent);stroke-width:2;flex:none}
.hours{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:clamp(22px,3vw,32px)}
.hours h3{font-family:var(--font-display);font-size:1.5rem;font-weight:700;margin-bottom:1rem}
.hours table{width:100%;border-collapse:collapse}
.hours td{padding:.85rem 0;border-bottom:1px solid var(--line);font-size:.96rem;vertical-align:top}
.hours td:last-child{text-align:right;color:var(--muted);font-weight:600;white-space:nowrap;padding-left:14px}
.hours td.hl{color:var(--accent-soft);font-weight:700}
.hours td.closed{color:var(--muted2)}
.hours tr:last-child td{border-bottom:0}
.hours-note{display:flex;align-items:center;gap:.6rem;margin-top:1.1rem;color:var(--muted);font-size:.88rem}
.hours-note svg{width:20px;height:20px;fill:none;stroke:var(--accent);stroke-width:2;flex:none}
.dock{position:fixed;right:18px;bottom:18px;z-index:90;display:flex;flex-direction:column;gap:12px}
.dock-btn{position:relative;display:grid;place-items:center;width:58px;height:58px;border-radius:50%;box-shadow:0 12px 30px rgba(0,0,0,.5);transition:transform .2s var(--ease)}
.dock-btn svg{width:28px;height:28px;fill:currentColor}
.dock-btn:hover{transform:scale(1.08)}
.dock-call{background:var(--accent);color:var(--accent-ink)}
.dock-call svg{width:25px;height:25px}
.dock-wa{background:var(--wa);color:#fff;animation:bob 2.6s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@media (min-width:881px){.dock{right:24px;bottom:24px}}
@media (max-width:880px){
  .nav{position:fixed;inset:74px 0 auto 0;flex-direction:column;gap:0;background:var(--bg);border-bottom:1px solid var(--line);padding:8px var(--pad) 18px;transform:translateY(-130%);transition:transform .35s var(--ease);box-shadow:var(--shadow)}
  .nav.open{transform:none}
  .nav a{padding:14px 0;border-bottom:1px solid var(--line);font-size:1.05rem}
  .nav a::after{display:none}
  .burger{display:flex}
  .head-cta .btn-ghost span{display:none}
  .head-cta .btn-ghost{padding:.6em}
  .stats{grid-template-columns:repeat(2,1fr)}
  .feature{grid-template-columns:1fr}
  .feature-media{max-width:440px;margin-inline:auto;order:-1}
  .contact-inner{grid-template-columns:1fr}
}
@media (max-width:480px){.hero-actions .btn{width:100%;justify-content:center}}
</style>
</head>
<body>
<a class="skip" href="#main">Sari la conținut</a>
<header class="site-head" id="top">
  <div class="wrap head-inner">
    <a class="brand" href="#top" aria-label="${brand_short} — acasă">
      <span class="brand-mark"><svg viewBox="0 0 48 48" aria-hidden="true">${brand_svg}</svg></span>
      <span class="brand-txt"><b>${brand_short}</b><i>${brand_sub}</i></span>
    </a>
    <nav class="nav" aria-label="Principal">
      <a href="#servicii">Servicii</a><a href="#dece">De ce noi</a><a href="#acoperire">Acoperire</a><a href="#recenzii">Recenzii</a><a href="#contact">Contact</a>
    </nav>
    <div class="head-cta">
      <a class="btn btn-ghost" href="${tel_href}"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_phone}</svg><span>${phone_display}</span></a>
      <button class="burger" aria-label="Meniu" aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<main id="main">
  <section class="hero">
    <div class="hero-media"><img src="${hero_img}" alt="${hero_alt}" width="1600" height="1067" fetchpriority="high"></div>
    <div class="hero-overlay"></div>
    <div class="wrap hero-inner">
      <p class="eyebrow reveal"><span class="ping"></span> ${eyebrow}</p>
      <h1 class="reveal">${h1}</h1>
      <p class="lead reveal">${lead}</p>
      <div class="hero-actions reveal">
        <a class="btn btn-call" href="${tel_href}"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_phone}</svg><span>Sună acum · ${phone_display}</span></a>
        <a class="btn btn-wa" href="${wa_main}" target="_blank" rel="noopener"><svg viewBox="0 0 32 32" aria-hidden="true">${ic_wa}</svg><span>Scrie pe WhatsApp</span></a>
      </div>
      <ul class="hero-chips reveal">${chips}</ul>
    </div>
  </section>
  <div class="ticker" aria-label="Ce facem"><div class="ticker-track">${ticker}</div></div>
  <section class="stats wrap">${stats}</section>
  <section class="section" id="servicii">
    <div class="wrap">
      <header class="sec-head reveal"><p class="kicker">${serv_kicker}</p><h2>${serv_title}</h2><p class="sub">${serv_sub}</p></header>
      <div class="services">${services}</div>
    </div>
  </section>
  <section class="section section-alt" id="dece">
    <div class="wrap feature">
      <div class="feature-media reveal">
        <img src="${feature_img}" alt="${feature_alt}" width="1000" height="1333" loading="lazy">
        <div class="feature-badge"><svg viewBox="0 0 24 24" aria-hidden="true">${ic_star}</svg><div><b>${rating}★</b><span>din ${reviews_count} recenzii</span></div></div>
      </div>
      <div class="feature-text">
        <p class="kicker reveal">${why_kicker}</p>
        <h2 class="reveal">${why_title}</h2>
        <ul class="why">${why}</ul>
        <a class="btn btn-call reveal" href="${tel_href}"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_phone}</svg><span>${phone_display}</span></a>
      </div>
    </div>
  </section>
  <section class="section" id="acoperire">
    <div class="wrap">
      <header class="sec-head reveal"><p class="kicker">Unde lucrăm</p><h2>${areas_title}</h2><p class="sub">${areas_sub}</p></header>
      <div class="areas reveal">${areas}</div>
      <div class="map-cta reveal">
        <div><b>${addr_line1}</b><span>${addr_city}</span></div>
        <a class="btn btn-ghost" href="${maps_href}" target="_blank" rel="noopener"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_pin}</svg><span>Deschide în Google Maps</span></a>
      </div>
    </div>
  </section>
  <section class="section section-alt" id="recenzii">
    <div class="wrap">
      <header class="sec-head reveal"><p class="kicker">Ce spun clienții</p><h2>${rev_title}</h2>
        <div class="rating-line reveal"><span class="stars">${stars5}</span> <b>${rating}</b> pe Google · ${reviews_count} recenzii</div>
      </header>
      <div class="reviews">${reviews}</div>
      <p class="review-note"><svg viewBox="0 0 24 24" aria-hidden="true">${ic_star}</svg> Rating real ${rating}★ din ${reviews_count} recenzii pe Google. Testimonialele de mai sus sunt ilustrative.</p>
    </div>
  </section>
  <section class="section contact" id="contact">
    <div class="wrap contact-inner">
      <div class="contact-text">
        <p class="kicker reveal">Contact</p>
        <h2 class="reveal">${contact_h2}</h2>
        <p class="sub reveal">${contact_sub}</p>
        <div class="contact-actions reveal">
          <a class="btn btn-call" href="${tel_href}"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_phone}</svg><span>${phone_display}</span></a>
          <a class="btn btn-wa" href="${wa_main}" target="_blank" rel="noopener"><svg viewBox="0 0 32 32" aria-hidden="true">${ic_wa}</svg><span>WhatsApp</span></a>
        </div>
        <ul class="contact-list reveal">
          <li><svg viewBox="0 0 48 48" aria-hidden="true">${ic_pin}</svg><span>${addr_full}</span></li>
          <li><svg viewBox="0 0 48 48" aria-hidden="true">${ic_phone}</svg><span>${phone_display}</span></li>
        </ul>
      </div>
      <div class="hours reveal">
        <h3>Program</h3>
        <table>${hours}</table>
        <p class="hours-note"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_clock}</svg> ${hours_note}</p>
      </div>
    </div>
  </section>
</main>
<footer class="site-foot">
  <div class="wrap foot-inner">
    <div class="foot-brand"><span class="brand-mark"><svg viewBox="0 0 48 48" aria-hidden="true">${brand_svg}</svg></span>
      <div><b>${name}</b><span>${foot_tagline}</span></div></div>
    <nav class="foot-nav" aria-label="Footer"><a href="#servicii">Servicii</a><a href="#dece">De ce noi</a><a href="#acoperire">Acoperire</a><a href="#recenzii">Recenzii</a><a href="#contact">Contact</a></nav>
    <p class="foot-legal">© <span id="y"></span> ${name} · ${addr_full} · Tel: ${phone_display}<br>${foot_legal}</p>
  </div>
</footer>
<div class="dock">
  <a class="dock-btn dock-call" href="${tel_href}" aria-label="Sună acum la ${phone_display}"><svg viewBox="0 0 48 48" aria-hidden="true">${ic_phone}</svg></a>
  <a class="dock-btn dock-wa" href="${wa_main}" target="_blank" rel="noopener" aria-label="Scrie pe WhatsApp"><svg viewBox="0 0 32 32" aria-hidden="true">${ic_wa}</svg></a>
</div>
<script>
(function(){var y=document.getElementById('y');if(y)y.textContent=new Date().getFullYear();
var b=document.querySelector('.burger'),n=document.querySelector('.nav');
if(b&&n){b.addEventListener('click',function(){var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false');});
n.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){n.classList.remove('open');b.setAttribute('aria-expanded','false');});});}
var els=document.querySelectorAll('.reveal');
if('IntersectionObserver'in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12,rootMargin:'0px 0px -8% 0px'});els.forEach(function(el){io.observe(el);});}else{els.forEach(function(el){el.classList.add('in');});}
})();
</script>
</body>
</html>''')

WA_SVG = '<path d="M16 3a13 13 0 0 0-11 19.6L3 29l6.6-2a13 13 0 1 0 6.4-24zm0 23.6a10.6 10.6 0 0 1-5.4-1.5l-.4-.2-4 1 1-3.9-.3-.4A10.6 10.6 0 1 1 16 26.6zm6-7.9c-.3-.2-2-1-2.3-1.1-.3-.1-.5-.2-.8.2s-.9 1.1-1.1 1.3-.4.2-.8 0a8.6 8.6 0 0 1-4.3-3.7c-.3-.6.3-.5.9-1.8.1-.2 0-.4 0-.6s-.8-1.9-1-2.6c-.3-.7-.6-.6-.8-.6h-.7a1.3 1.3 0 0 0-1 .4 4 4 0 0 0-1.2 2.9 6.9 6.9 0 0 0 1.4 3.6 15.7 15.7 0 0 0 6 5.3c2.2 1 3 1 4.1.9a3.5 3.5 0 0 0 2.3-1.6 2.9 2.9 0 0 0 .2-1.6c0-.2-.3-.3-.6-.5z"/>'

DEFAULT_AREAS = ["Sector 1","Sector 2","Sector 3","Sector 4","Sector 5 & 6","Ilfov"]

def build_mockup(d):
    pal = PALETTES[d.get("palette","leather")]
    pool = pool_for(d.get("niche_key","generic"))
    # default stats derivate din rating/recenzii dacă nu sunt date
    if not d.get("stats"):
        d["stats"] = [(str(d["rating"]).replace(".",",")+"★","rating pe Google"),
                      (str(d["reviews_count"]),"recenzii de clienți"),
                      ("100%","lucru de calitate"),
                      ("1","echipă dedicată")]
    # imagini: din date sau din pool
    hero_img = d.get("hero_img") or img_url(pool[0], 1600)
    feat_img = d.get("feature_img") or img_url(pool[3 % len(pool)], 1000)
    for i, s in enumerate(d["services"]):
        s.setdefault("img", img_url(pool[i % len(pool)], 800))
    phone_wa = d["phone_wa"]; d["phone_wa"] = phone_wa
    tel = "tel:+" + phone_wa
    wa_main = wa(phone_wa, d.get("wa_msg","Bună ziua! Am văzut site-ul %s și vreau o programare." % d["name"]))
    maps_href = "https://www.google.com/maps/search/?api=1&query=" + quote("%s %s" % (d["name"], d["address"]))
    schema = json.dumps({
      "@context":"https://schema.org","@type":d.get("schema_type","LocalBusiness"),
      "name":d["name"],"image":hero_img,"telephone":"+"+phone_wa,
      "address":{"@type":"PostalAddress","streetAddress":d["addr_line1"],"addressLocality":d.get("addr_city","București"),"addressCountry":"RO"},
      "areaServed":["București","Ilfov"],
      "aggregateRating":{"@type":"AggregateRating","ratingValue":str(d["rating"]),"reviewCount":str(d["reviews_count"])}
    }, ensure_ascii=False)
    m = dict(pal)
    m.update(dict(
      seo_title=d["seo_title"], seo_desc=d["seo_desc"], og_title=d.get("og_title",d["seo_title"]),
      og_image=hero_img, theme_color=pal["bg"], fonts=pal["fonts"], schema_json=schema,
      hero_img=hero_img, hero_alt=d.get("hero_alt", d["name"]), feature_img=feat_img,
      feature_alt=d.get("feature_alt", d["name"]),
      brand_short=d.get("brand_short", d["name"]), brand_sub=d.get("brand_sub","București"),
      brand_svg=d.get("brand_svg", ICONS["sparkle"]),
      name=d["name"], tel_href=tel, phone_display=d["phone_display"], wa_main=wa_main,
      ic_phone=ICONS["phone"], ic_wa=WA_SVG, ic_star=ICONS["star"], ic_pin=ICONS["pin"], ic_clock=ICONS["clock"],
      eyebrow=d["eyebrow"], h1=d["h1"], lead=d["lead"], chips=render_chips(d),
      ticker=render_ticker(d), stats=render_stats(d),
      serv_kicker=d.get("serv_kicker","Ce facem"), serv_title=d["serv_title"], serv_sub=d["serv_sub"],
      services=render_services(d),
      why_kicker=d.get("why_kicker","De ce noi"), why_title=d["why_title"], why=render_why(d),
      rating=str(d["rating"]).replace(".",","), reviews_count=str(d["reviews_count"]),
      areas_title=d["areas_title"], areas_sub=d["areas_sub"], areas=render_areas(d),
      addr_line1=d["addr_line1"], addr_city=d.get("addr_city","București"), addr_full=d["address"], maps_href=maps_href,
      rev_title=d.get("rev_title","Ce spun clienții noștri"), stars5=STAR5, reviews=render_reviews(d),
      contact_h2=d.get("contact_h2","Sună-ne. Restul rezolvăm noi."), contact_sub=d["contact_sub"],
      hours=render_hours(d), hours_note=d.get("hours_note","Scrie-ne oricând pe WhatsApp — revenim în timpul programului."),
      foot_tagline=d.get("foot_tagline", d["serv_title"]), foot_legal=d.get("foot_legal", d["serv_sub"]),
    ))
    return TEMPLATE.substitute(m)

def main():
    if len(sys.argv) < 2:
        print("Usage: python mockup_gen.py leads.json"); sys.exit(1)
    leads = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)
    for d in leads:
        html = build_mockup(d)
        path = os.path.join(OUT_DIR, d["slug"] + ".html")
        open(path, "w", encoding="utf-8").write(html)
        print("✓ %s (%d octeți)" % (d["slug"], len(html.encode("utf-8"))))

if __name__ == "__main__":
    main()
