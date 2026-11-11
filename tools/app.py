#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app — interfața grafică locală pentru tot fluxul leads-toolkit.

Pornire:
  python3 tools/app.py          # deschide http://127.0.0.1:7788 în browser

Ce face: îmbracă uneltele existente (pipeline_leads.py) într-o pagină web cu tab-uri,
ca fluxul să poată fi folosit și de cineva non-tehnic:

  1. Caută leads   — formularul scraperului (nișe, oraș, filtre) → rulează scrape
  2. Revizuire     — pending_leads.json ca listă editabilă (omul de la mijloc)
  3. Publicare     — dry-run / publicare live, cu log în pagină
  4. De sunat      — SITEURI_DE_TESTAT.txt ca fișe de apel: telefon, WhatsApp cu
                     mesajul precompletat, buton de copiat pitch-ul, statusuri rapide
  5. Istoric       — tested_leads.txt

Nu adaugă dependențe: doar biblioteca standard. Serverul ascultă DOAR pe localhost.
"""
import json, os, re, subprocess, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pipeline_leads as pl
import mockup_gen2 as g2

PORT = int(os.environ.get("LEADS_GUI_PORT", "7788"))
PIPE = os.path.join(HERE, "pipeline_leads.py")

# ── un singur job pe rând (scrape sau publish), cu log în memorie ──────────────
JOB = {"running": False, "name": "", "log": [], "rc": None}
_lock = threading.Lock()

def start_job(name, cmd):
    with _lock:
        if JOB["running"]:
            return False
        JOB.update(running=True, name=name, log=["$ " + " ".join(cmd)], rc=None)
    def run():
        try:
            p = subprocess.Popen(cmd, cwd=pl.BASE, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in p.stdout:
                JOB["log"].append(line.rstrip("\n"))
            p.wait()
            JOB["rc"] = p.returncode
            JOB["log"].append("── gata (cod %s) ──" % p.returncode)
        except Exception as e:
            JOB["rc"] = -1
            JOB["log"].append("[eroare] %s" % e)
        finally:
            JOB["running"] = False
    threading.Thread(target=run, daemon=True).start()
    return True

# ── citirea listelor ───────────────────────────────────────────────────────────
def read_pending():
    if not os.path.exists(pl.PENDING): return []
    try:
        return json.load(open(pl.PENDING, encoding="utf-8"))
    except Exception:
        return []

def parse_lista():
    """SITEURI_DE_TESTAT.txt → fișe de apel structurate."""
    if not os.path.exists(pl.LISTA): return []
    txt = open(pl.LISTA, encoding="utf-8").read()
    out = []
    pat = re.compile(r"-{20,}\n(\S+)\s+(\d+)\.\s+(.+?)\s*\(([^/]*?)\s*/\s*([^)]*)\)\n-{20,}\n(.*?)(?=\n-{20,}\n\S+\s+\d+\.|\n=+\n|\Z)", re.S)
    for m in pat.finditer(txt):
        emoji, nr, name, cat, zona, body = m.groups()
        def fld(label):
            mm = re.search(r"\*\s+%s:\s*(.+)" % label, body)
            return mm.group(1).strip() if mm else ""
        pitch = ""
        pm = re.search(r"\*\s+Pitch \(Mesaj WhatsApp de trimis\):\n(.*)", body, re.S)
        if pm: pitch = pm.group(1).strip()
        tel = fld("Telefon")
        out.append(dict(nr=int(nr), emoji=emoji, name=name.strip(), cat=cat.strip(), zona=zona.strip(),
                        address=fld("Locație"), tel=tel, tel_wa="40" + g2.norm_phone(tel),
                        program=fld("Program de Lucru"), link=fld("Link Prototip Live"), pitch=pitch))
    return out

def read_tested():
    if not os.path.exists(pl.TESTED): return []
    rows = []
    for line in open(pl.TESTED, encoding="utf-8"):
        m = re.match(r"(\d+)\.\s+(.+?)\s*\|\s*Tel:\s*(.+?)\s*\|\s*Status:\s*(.+)", line.strip())
        if m: rows.append(dict(nr=int(m.group(1)), name=m.group(2).strip(),
                               tel=m.group(3).strip(), status=m.group(4).strip()))
    return rows

# ── pagina ────────────────────────────────────────────────────────────────────
HTML = r"""<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>leads-toolkit</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400..700&display=swap" rel="stylesheet">
<style>
:root{--ink:#121A22;--mut:#5C6670;--line:#E7E5DF;--bg:#FBFBFA;--bg2:#F3F3F0;--card:#fff;
  --acc:#1a6c7a;--wa:#1BA050;--bad:#C2452D;--ok:#1E9E56;--r:12px;
  --sh:0 1px 2px rgba(15,18,16,.05),0 10px 28px -20px rgba(15,18,16,.25)}
*{box-sizing:border-box;margin:0;padding:0}
body{font:400 15px/1.55 'Geist',system-ui,sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:14px;flex-wrap:wrap;
  padding:12px clamp(16px,3vw,32px);background:rgba(251,251,250,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
header b{font-size:1.05rem;letter-spacing:-.02em}
header .st{font-size:.8rem;color:var(--mut);margin-left:auto}
header .st .dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#bbb;margin-right:6px}
header .st.run .dot{background:var(--ok);animation:p 1.2s infinite}
@keyframes p{50%{opacity:.35}}
nav{display:flex;gap:6px;flex-wrap:wrap}
nav button{font:600 .88rem 'Geist';padding:.6em 1.15em;border:1px solid var(--line);border-radius:999px;
  background:var(--card);color:var(--mut);cursor:pointer}
nav button.on{background:var(--ink);border-color:var(--ink);color:#fff}
nav button .n{display:inline-block;min-width:1.3em;text-align:center;background:var(--acc);color:#fff;
  border-radius:999px;font-size:.72rem;padding:.1em .35em;margin-left:.35em}
main{max-width:1080px;margin:0 auto;padding:clamp(16px,3vw,32px)}
.tab{display:none}.tab.on{display:block}
h2{font-size:1.3rem;letter-spacing:-.02em;margin-bottom:.35rem}
.sub{color:var(--mut);font-size:.9rem;margin-bottom:1.2rem;max-width:70ch}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:20px;box-shadow:var(--sh)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
label{display:block;font-size:.78rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--mut);margin:0 0 .35rem}
input,select,textarea{width:100%;font:inherit;padding:.65em .9em;border:1px solid var(--line);border-radius:9px;background:var(--bg)}
input:focus,textarea:focus{outline:2px solid var(--acc);outline-offset:1px}
.f{margin-bottom:14px}
.btn{display:inline-flex;align-items:center;gap:.5rem;font:600 .95rem 'Geist';padding:.7em 1.3em;
  border-radius:999px;border:1px solid transparent;cursor:pointer;text-decoration:none;background:var(--ink);color:#fff}
.btn:hover{opacity:.92}
.btn.ghost{background:var(--card);border-color:var(--line);color:var(--ink)}
.btn.wa{background:var(--wa)}
.btn.warn{background:var(--bad)}
.btn:disabled{opacity:.45;cursor:not-allowed}
pre.log{background:#101418;color:#cfd8dc;border-radius:var(--r);padding:16px;font:12.5px/1.6 ui-monospace,monospace;
  max-height:320px;overflow:auto;margin-top:16px;white-space:pre-wrap}
.lead{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:start;border:1px solid var(--line);
  border-radius:var(--r);background:var(--card);padding:18px;margin-bottom:12px;box-shadow:var(--sh)}
.lead h3{font-size:1.06rem;letter-spacing:-.01em}
.lead .meta{color:var(--mut);font-size:.86rem;margin:.15rem 0 .6rem}
.lead .pitch{font-size:.88rem;background:var(--bg2);border-radius:9px;padding:10px 12px;margin:.5rem 0;white-space:pre-wrap}
.lead .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:.4rem}
.badge{font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--acc);
  background:#1a6c7a14;border-radius:999px;padding:.35em .9em}
.stbtns{display:flex;flex-direction:column;gap:6px;min-width:150px}
.stbtns button{font:600 .8rem 'Geist';padding:.55em .9em;border-radius:8px;border:1px solid var(--line);background:var(--card);cursor:pointer;text-align:left}
.stbtns button:hover{border-color:var(--ink)}
.empty{border:1.5px dashed var(--line);border-radius:var(--r);padding:34px;text-align:center;color:var(--mut)}
.empty b{display:block;color:var(--ink);margin-bottom:.3rem}
table{width:100%;border-collapse:collapse;font-size:.9rem}
td,th{padding:.6rem .5rem;border-bottom:1px solid var(--line);text-align:left}
th{font-size:.74rem;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
.pl-item{border:1px solid var(--line);border-radius:var(--r);background:var(--card);padding:16px;margin-bottom:10px}
.pl-item .grid3{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px;margin-top:8px}
.toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:var(--ink);color:#fff;
  padding:.7em 1.3em;border-radius:999px;font-size:.9rem;opacity:0;transition:opacity .25s;pointer-events:none}
.toast.on{opacity:1}
@media(max-width:720px){.grid2,.pl-item .grid3{grid-template-columns:1fr}.lead{grid-template-columns:1fr}.stbtns{flex-direction:row;flex-wrap:wrap}}
</style>
</head>
<body>
<header>
  <b>leads-toolkit</b>
  <nav id="nav"></nav>
  <span class="st" id="jobst"><span class="dot"></span><span id="jobtxt">inactiv</span></span>
</header>
<main id="main"></main>
<div class="toast" id="toast"></div>
<script>
"use strict";
const TABS=[["scrape","Caută leads"],["review","Revizuire"],["publish","Publicare"],["call","De sunat"],["done","Istoric"]];
let S={pending:[],lista:[],tested:[],job:{running:false,name:"",log:[],rc:null},live_base:""};
let cur=localStorage.getItem("tab")||"call";
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/"/g,"&quot;");

function toast(m){const t=$("#toast");t.textContent=m;t.classList.add("on");setTimeout(()=>t.classList.remove("on"),2200);}
async function api(path,body){
  const r=await fetch(path,body?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}:{});
  if(!r.ok){toast(await r.text()||("Eroare "+r.status));throw 0;}
  return r.json();
}
async function refresh(){S=await api("/api/state");render();}

function nav(){
  $("#nav").innerHTML=TABS.map(([id,t])=>{
    let n=id==="review"?S.pending.length:id==="call"?S.lista.length:0;
    return `<button class="${id===cur?'on':''}" onclick="go('${id}')">${t}${n?`<span class="n">${n}</span>`:""}</button>`;
  }).join("");
  const st=$("#jobst");st.classList.toggle("run",S.job.running);
  $("#jobtxt").textContent=S.job.running?("rulează: "+S.job.name):"inactiv";
}
function go(t){cur=t;localStorage.setItem("tab",t);render();}

function logBlock(){
  if(!S.job.log.length)return"";
  return `<pre class="log" id="log">${esc(S.job.log.join("\n"))}</pre>`;
}

function vScrape(){
  const d=S.job.running;
  return `<h2>Caută leads noi</h2>
  <p class="sub">Scrie nișele (cu oraș), una pe rând sau despărțite prin punct și virgulă. Scraperul caută pe Google Maps
  firme <b>fără site</b>, cu telefon mobil, și le pune în tab-ul <b>Revizuire</b>.</p>
  <div class="card">
    <div class="f"><label>Nișe + oraș</label>
      <textarea id="niches" rows="3" placeholder="vulcanizare Bucuresti; detailing auto Cluj; cabinet stomatologic Brasov">${esc(localStorage.getItem("niches")||"")}</textarea></div>
    <div class="grid2">
      <div class="f"><label>Maxim leads per nișă</label><input id="maxn" type="number" value="3" min="1" max="10"></div>
      <div class="f"><label>Rating minim</label><input id="minr" type="number" value="4.0" step="0.1" min="0" max="5"></div>
    </div>
    <button class="btn" ${d?"disabled":""} onclick="doScrape()">🔎 Pornește căutarea</button>
    <span class="sub" style="display:inline;margin-left:10px">durează câteva minute — vezi progresul mai jos</span>
    ${logBlock()}
  </div>`;
}
async function doScrape(){
  const n=$("#niches").value.trim();if(!n)return toast("Scrie măcar o nișă");
  localStorage.setItem("niches",n);
  await api("/api/scrape",{niches:n,max_per_niche:+$("#maxn").value,min_rating:+$("#minr").value});
  toast("Căutarea a pornit");poll();
}

function vReview(){
  if(!S.pending.length)return `<h2>Revizuire</h2><div class="empty"><b>Niciun lead de revizuit</b>
    Rulează întâi o căutare în tab-ul „Caută leads”.</div>`;
  return `<h2>Revizuire — omul de la mijloc</h2>
  <p class="sub">Verifică fiecare lead înainte de publicare: nume corect, telefon, adresă. Ce nu e bun — șterge.
  Apoi apasă <b>Salvează</b> și treci la <b>Publicare</b>.</p>
  ${S.pending.map((l,i)=>`<div class="pl-item">
    <div style="display:flex;justify-content:space-between;gap:10px;align-items:center">
      <span class="badge">${esc(l.niche_key||"?")}</span>
      <button class="btn warn" style="padding:.4em 1em;font-size:.8rem" onclick="delPending(${i})">Șterge</button>
    </div>
    <div class="grid3">
      <div><label>Nume firmă</label><input value="${esc(l.name)}" onchange="S.pending[${i}].name=this.value"></div>
      <div><label>Telefon</label><input value="${esc(l.phone_display)}" onchange="S.pending[${i}].phone_display=this.value"></div>
      <div><label>Rating</label><input value="${esc(l.rating)}" onchange="S.pending[${i}].rating=this.value"></div>
    </div>
    <div class="grid3" style="grid-template-columns:2fr 1fr 1fr">
      <div><label>Adresă</label><input value="${esc(l.address)}" onchange="S.pending[${i}].address=this.value"></div>
      <div><label>Recenzii</label><input value="${esc(l.reviews_count)}" onchange="S.pending[${i}].reviews_count=this.value"></div>
      <div><label>Slug (fișier)</label><input value="${esc(l.slug)}" disabled></div>
    </div>
  </div>`).join("")}
  <button class="btn" onclick="savePending()">💾 Salvează modificările</button>`;
}
function delPending(i){S.pending.splice(i,1);render();}
async function savePending(){await api("/api/save-pending",{leads:S.pending});toast("Salvat");refresh();}

function vPublish(){
  const d=S.job.running,n=S.pending.length;
  return `<h2>Publicare</h2>
  <p class="sub">Generează site-urile pentru cele <b>${n}</b> leaduri revizuite, le urcă pe GitHub Pages,
  verifică linkurile live și abia apoi le adaugă în lista <b>De sunat</b>.</p>
  <div class="card">
    <div class="row" style="display:flex;gap:10px;flex-wrap:wrap">
      <button class="btn ghost" ${d||!n?"disabled":""} onclick="doPublish(true)">🧪 Test (fără publicare)</button>
      <button class="btn" ${d||!n?"disabled":""} onclick="doPublish(false)">🚀 Publică live</button>
    </div>
    ${logBlock()}
  </div>`;
}
async function doPublish(dry){await api("/api/publish",{dry_run:dry});toast(dry?"Test pornit":"Publicarea a pornit");poll();}

function waLink(l){return "https://wa.me/"+l.tel_wa+"?text="+encodeURIComponent(l.pitch||"");}
function vCall(){
  if(!S.lista.length)return `<h2>De sunat</h2><div class="empty"><b>Lista e goală</b>
    Leadurile apar aici după „Publicare”. Verifică pasul de publicare dacă crezi că lipsește ceva.</div>`;
  return `<h2>De sunat — ${S.lista.length} ${S.lista.length===1?"firmă":"firme"}</h2>
  <p class="sub">Pentru fiecare firmă: <b>1)</b> trimite mesajul pe WhatsApp (e gata scris) · <b>2)</b> dacă a citit /
  a intrat pe link, sun-o azi · <b>3)</b> apasă statusul potrivit — firma se mută la Istoric.</p>
  ${S.lista.map(l=>`<div class="lead">
    <div>
      <h3>${l.emoji} ${l.nr}. ${esc(l.name)}</h3>
      <div class="meta">${esc(l.cat)} · ${esc(l.zona)} · ${esc(l.program)}</div>
      <div class="row">
        <a class="btn ghost" href="tel:+${l.tel_wa}">📞 ${esc(l.tel)}</a>
        <a class="btn wa" href="${waLink(l)}" target="_blank">Trimite pe WhatsApp</a>
        <a class="btn ghost" href="${esc(l.link)}" target="_blank">Vezi site-ul de probă ↗</a>
      </div>
      <div class="pitch">${esc(l.pitch)}</div>
      <button class="btn ghost" style="padding:.5em 1em;font-size:.82rem" onclick="copyPitch(this,${l.nr})">📋 Copiază mesajul</button>
    </div>
    <div class="stbtns">
      <button onclick="move(${l.nr},'CONTACTAT — așteaptă răspuns')">📨 Am trimis mesajul</button>
      <button onclick="move(${l.nr},'INTERESAT — de revenit')">🔥 Interesat</button>
      <button onclick="move(${l.nr},'CLIENT ✔')">✅ A zis DA</button>
      <button onclick="move(${l.nr},'REFUZ')">✖ A refuzat</button>
      <button onclick="move(${l.nr},'FĂRĂ RĂSPUNS')">😶 Fără răspuns</button>
    </div>
  </div>`).join("")}`;
}
function copyPitch(btn,nr){
  const l=S.lista.find(x=>x.nr===nr);
  navigator.clipboard.writeText(l.pitch).then(()=>toast("Mesaj copiat — lipește-l în WhatsApp"));
}
async function move(nr,status){
  if(!confirm("Mut firma #"+nr+" la Istoric cu statusul:\n„"+status+"”?"))return;
  await api("/api/move",{numar:nr,status});toast("Mutat ✔");refresh();
}

function vDone(){
  if(!S.tested.length)return `<h2>Istoric</h2><div class="empty"><b>Încă nimic aici</b>
    Firmele apar aici după ce le dai un status din tab-ul „De sunat”.</div>`;
  return `<h2>Istoric — ${S.tested.length} contactate</h2>
  <div class="card" style="padding:6px 18px"><table>
    <tr><th>#</th><th>Firmă</th><th>Telefon</th><th>Status</th></tr>
    ${S.tested.slice().reverse().map(r=>`<tr><td>${r.nr}</td><td>${esc(r.name)}</td>
      <td><a href="tel:${esc(r.tel)}">${esc(r.tel)}</a></td><td>${esc(r.status)}</td></tr>`).join("")}
  </table></div>`;
}

function render(){
  nav();
  const v={scrape:vScrape,review:vReview,publish:vPublish,call:vCall,done:vDone}[cur];
  $("#main").innerHTML=`<div class="tab on">${v()}</div>`;
  const lg=$("#log");if(lg)lg.scrollTop=lg.scrollHeight;
}

let polling=false;
async function poll(){
  if(polling)return;polling=true;
  while(true){
    await refresh();
    if(!S.job.running)break;
    await new Promise(r=>setTimeout(r,1500));
  }
  polling=false;
}
refresh().then(()=>{if(S.job.running)poll();});
</script>
</body>
</html>"""

# ── server ────────────────────────────────────────────────────────────────────
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _err(self, msg, code=400):
        b = msg.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            b = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        elif self.path == "/api/state":
            self._json(dict(pending=read_pending(), lista=parse_lista(), tested=read_tested(),
                            job=dict(running=JOB["running"], name=JOB["name"],
                                     log=JOB["log"][-400:], rc=JOB["rc"]),
                            live_base=pl.LIVE_BASE))
        else:
            self._err("nu există", 404)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._err("JSON invalid")
        if self.path == "/api/scrape":
            niches = (data.get("niches") or "").replace("\n", "; ").strip()
            if not niches: return self._err("Scrie măcar o nișă")
            cmd = [sys.executable, PIPE, "scrape", "--niches", niches,
                   "--max-per-niche", str(int(data.get("max_per_niche") or 3)),
                   "--min-rating", str(float(data.get("min_rating") or 4.0))]
            if not start_job("căutare leads", cmd):
                return self._err("Rulează deja un job — așteaptă să termine", 409)
            self._json(dict(ok=True))
        elif self.path == "/api/publish":
            cmd = [sys.executable, PIPE, "publish"]
            if data.get("dry_run"): cmd.append("--dry-run")
            if not start_job("publicare" + (" (test)" if data.get("dry_run") else ""), cmd):
                return self._err("Rulează deja un job — așteaptă să termine", 409)
            self._json(dict(ok=True))
        elif self.path == "/api/save-pending":
            leads = data.get("leads")
            if not isinstance(leads, list): return self._err("format greșit")
            json.dump(leads, open(pl.PENDING, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            self._json(dict(ok=True))
        elif self.path == "/api/move":
            try:
                nr, status = int(data["numar"]), str(data["status"]).strip() or "TESTAT"
            except Exception:
                return self._err("cere numar + status")
            r = subprocess.run([sys.executable, PIPE, "move", str(nr), "--status", status],
                               cwd=pl.BASE, capture_output=True, text=True)
            if r.returncode != 0:
                # fără git/push (ex. offline) → măcar mută local, ca lista să rămână corectă
                r2 = subprocess.run([sys.executable, PIPE, "move", str(nr), "--status", status, "--no-push"],
                                    cwd=pl.BASE, capture_output=True, text=True)
                if r2.returncode != 0:
                    return self._err((r.stdout + r.stderr).strip()[-400:] or "move a eșuat", 500)
            self._json(dict(ok=True))
        else:
            self._err("nu există", 404)

def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    url = "http://127.0.0.1:%d" % PORT
    print("leads-toolkit GUI · %s  (Ctrl+C pentru oprire)" % url)
    print("Director de lucru: %s" % pl.BASE)
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nla revedere 👋")

if __name__ == "__main__":
    main()
