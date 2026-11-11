# Cum folosești un LLM cu pipeline-ul ăsta

Scurt: **scriptul găsește firmele, LLM-ul scrie site-ul.** Dacă sari peste partea cu LLM-ul,
ies 40 de site-uri identice cu „Serviciu 1 / Serviciu 2 / Descriere." și nu închizi nimic.

Eu (Sol) folosesc Claude Code, dar merge orice LLM decent — contează promptul, nu unealta.

---

## Quickstart cu AI (pas cu pas) — citește asta primul

Presupune că ai făcut setup-ul din README (venv + `LEADS_WORKDIR` + `LEADS_PY` setate).
`T=~/leads-toolkit`. Fiecare pas: comanda de rulat **sau** promptul de dat AI-ului.

### Pasul 1 — alege nișa (întrebi AI-ul, nu ghicești)
Lecția plătită scump: nișa greșită = 0 vânzări din 110 apeluri. Întâi întrebi:

```
Vând site-uri de prezentare (~2000 lei) la afaceri mici din <ORAȘ> fără site.
Dă-mi 8 nișe UȘOR de închis (clientul lor caută online înainte să cumpere ȘI
afacerea e vizuală sau are ticket >500 lei) și 5 care par bune dar NU trec, cu motivul.
```

🟢 Ușoare: detailing, florării, tapițerie/mobilă la comandă, GSM.
🔴 Grele (evită): vulcanizare, spălătorie auto, cizmărie, ceasornicărie.

### Pasul 2 — caută firmele (scriptul, nu AI-ul)
```bash
$LEADS_PY $T/tools/pipeline_leads.py scrape --niches "detailing auto Bucuresti,florarii Bucuresti" --max-per-niche 4
```
Scrie `pending_leads.json` în `$LEADS_WORKDIR`. Dedup automat față de listele tale.

### Pasul 3 — pune AI-ul să curețe lista (dar verifici tu)
```
Atașat pending_leads.json. Pentru fiecare: PĂSTREZ / ARUNC + motiv de o linie.
Aruncă: lanțuri/francize, instituții, firme al căror nume sugerează alt business
decât niche_key, listări moarte. Nu modifica fișierul, dă-mi doar tabelul.
```
Ștergi tu manual din JSON ce a marcat ARUNC și ești de acord.

### Pasul 4 — publică (scriptul: generează + push + verifică live + scrie în listă)
```bash
$LEADS_PY $T/tools/pipeline_leads.py publish        # sau --dry-run întâi
```
Verifică întâi cu `--dry-run` cum arată o intrare, apoi rulează fără el.

### Pasul 5 — sună (AI-ul îți dă scriptul de apel)
Regula de aur descoperită: **NU trimite linkul ca temă — pune-l pe client să-l deschidă
LIVE cu tine pe apel**, plimbă-l prin site, TACI după „cum vi se pare?", și **cere banii
pe reacția caldă** (2000 lei, 30% avans, „2 zile live + ajustări"). Cere AI-ului:

```
Fă-mi un script de apel de vânzare pentru <nișă>, în română, în care clientul
deschide mockup-ul LIVE pe telefon cu mine, iar eu închid cerând 30% avans.
```

### Pasul 6 — după apel, mută leadul
```bash
$LEADS_PY $T/tools/pipeline_leads.py move 7 --status "CONTACTAT — se gândește"
```

### Ce face AI-ul vs ce face scriptul (rezumat)
- **AI:** alege nișe · curăță lista · **scrie textele per firmă** (Pasul cel mai important, vezi §3) · scriptul de apel
- **Script:** caută pe Maps · verifică că n-au site · generează HTML · push · listă
- **Tu:** decizi, arunci gunoiul, **suni** 🙂

> Regula #1: **nu se inventează NIMIC** (telefon/adresă/program vin din Maps). Dacă AI-ul
> „completează" un program lipsă, ai mințit clientul înainte să vorbești cu el. Vezi §2.

---

## Cine ce face, exact

| pas | cine | de ce |
|---|---|---|
| alegerea nișelor | **tu + LLM** | contează enorm — vezi secțiunea 1 |
| căutat firme pe Maps | **script** (`scrape`) | era manual în browser, acum e automat |
| verificat că n-au site | **script** | deschide pagina de detaliu și reconfirmă `web=null` |
| aruncat gunoiul din listă | **tu (ochii tăi)** | scriptul nu știe că „Panda Self-Service" nu-i lead |
| **scris textele per firmă** | **LLM** | ← **partea care face diferența** |
| ales pozele | LLM + verificare vizuală | vezi secțiunea 4 |
| generat HTML | **script** (`mockup_gen2.py`) | |
| push + verificat live | **script** (`publish`) | |
| sunat clientul | **tu** | 🙂 |

Istoric: la început făceam TOT manual cu LLM-ul — și găsirea firmelor pe Maps, și textele.
`scrape_maps_leads.py` a automatizat doar partea de căutare/verificare. Textele au rămas
la LLM pentru că acolo se câștigă vânzarea.

---

## 1. Alegerea nișelor (LLM ca sparring partner)

Cea mai scumpă lecție de până acum: **din 110 leaduri sunate → 0 închise**, pentru că erau
nișe greșite (auto, vulcanizare, ateliere mici). Istoric general ~1,5% (3 din 200).

Regula care separă: *„clientul lor caută online înainte de a cumpăra + afacerea e vizuală
sau are ticket mare?"*

| 🟢 ușor de închis | 🔴 greu |
|---|---|
| detailing auto (tineri, mândri, Instagram) | vulcanizare, spălătorie auto (ticket mic, walk-in) |
| florării (vizual, livrare, caută online) | cizmărie, ceasornicărie (proprietari vârstnici) |
| tapițerie / mobilă la comandă (ticket mare, portofoliul vinde) | |
| service GSM (searchable, tineri) | |

Prompt util:

```
Caut afaceri mici din <ORAȘ> cărora să le vând un site de prezentare (~2000 lei).
Criteriu: clientul lor caută online ÎNAINTE să cumpere, ȘI afacerea e vizuală
sau are ticket mare (>500 lei).
Dă-mi 10 nișe care trec filtrul și 5 care par bune dar NU trec, cu motivul.
Evită: tractări, electrician, instalator, lăcătuș, sticlari, vidanjare — saturate.
```

---

## 2. Periatul `pending_leads.json` (pasul „omul de la mijloc")

După `scrape`, deschizi fișierul și arunci ce nu e lead. Scriptul filtrează după
„n-are site + are telefon mobil", dar nu înțelege **ce fel de afacere** e.

Exemple reale scoase manual: o agenție de turism și un self-service auto — trecuseră
filtrul tehnic, dar presetul de nișă nu li se potrivea deloc.

Poți pune LLM-ul să facă prima trecere, dar **verifică-i decizia**:

```
Atașat pending_leads.json din scraperul meu de leads.
Pentru fiecare intrare spune-mi PĂSTREZ / ARUNC + un motiv de o linie.
Aruncă: lanțuri și francize, instituții, firme cu nume care sugerează
alt tip de business decât niche_key, orice pare listare moartă.
Nu modifica fișierul, dă-mi doar tabelul.
```

⚠️ **Regula #1 a proiectului: nu se inventează NIMIC.** Telefon, adresă, program, rating —
toate vin din Maps. Dacă LLM-ul „completează" un program lipsă, ai mințit un client
înainte să vorbești cu el. Ce nu se poate verifica, nu intră.

---

## 3. Scrisul textelor — partea care contează

Aici pui LLM-ul să transforme datele brute în `round<N>.json` (format v2), pe care apoi
îl dai la generator.

Varianta leneșă (`mockup_gen2.py --from-scraped`) folosește presetări pe nișă: iese
**decent, dar generic** — toate florăriile primesc același text. Bun ca schelet, prost ca pitch.

Varianta bună: îi dai LLM-ului datele lead-ului + schema și îl pui să scrie *pentru firma aia*.

```
Ești copywriter pentru afaceri mici din România. Scrii în română, natural,
fără limbaj corporatist ("soluții inovatoare", "excelență", "pasiune").

Datele firmei (REALE, din Google Maps — nu le modifica):
<lipește obiectul din leads_found.json>

Generează un obiect JSON în formatul v2 al lui mockup_gen2.py:
- archetype: alege dintre atelier / urgent / studio / cabinet (vezi mai jos)
- h1_a + h1_wonk + h1_b: titlul rupt în 3 (partea _wonk se afișează cu stil aparte)
- lead: 1-2 propoziții, ce câștigă clientul, nu ce face firma
- services: 4 servicii REALE pentru nișa asta, cu descrieri concrete
- composer.steps: 2-3 întrebări care compun mesajul WhatsApp
  (ex. la florărie: ocazia → buget → ridici sau livrăm)
- ticker: 6-8 termeni din meseria lor, care sună a om din branșă
- reviews: 3 recenzii SCURTE și oneste, la nivelul ratingului real (<rating>★)

Reguli: nu inventa servicii pe care nu le-ar avea; nu promite termene sau
prețuri; nu scrie recenzii entuziaste pentru un rating de 4.2.
```

Alegerea arhetipului:

| arhetip | când |
|---|---|
| `atelier` | meșteșug, lucru cu mâna, portofoliu — florărie, cizmărie, tapițerie, mobilă, croitorie |
| `urgent` | intervenție rapidă, clientul e în belea — parbrize, tractări, deblocări, electrică auto |
| `studio` | vizual premium, rezultatul se vede — detailing, vopsitorie, optică |
| `cabinet` | programare, încredere, calm — kineto, reparații electrocasnice, GSM |

Schema completă e în docstring-ul de sus din `tools/mockup_gen2.py`. Presetări gata scrise
pentru 16 nișe: `florarie, cizmarie, ceasornicarie, tapiterie, mobila, parbrize,
electrica_auto, detailing, vopsitorie, spalatorie, optica, kineto, reparatii_electro,
gsm, service_auto, generic`. Fură structura dintr-una când scrii o nișă nouă.

Fluxul, concret:

```bash
# 1. scraper → date brute (scrie în $LEADS_WORKDIR)
$LEADS_PY $T/tools/scrape_maps_leads.py --niches "florarii Bucuresti" --max-per-niche 5

# 2. dai leads_found.json la LLM cu promptul de mai sus → round11.json
# 3. generezi
python3 $T/tools/mockup_gen2.py round11.json

# 4. te uiți la ele în browser înainte de publish
```

---

## 4. Pozele — verifică-le cu ochii

Generatorul are un pool de imagini deja verificate (`IMG` în `mockup_gen2.py`). Dacă LLM-ul
propune poze noi de pe Unsplash, **HTTP 200 nu e suficient** — linkul poate merge și poza
să fie complet nepotrivită.

Deschide-le. Dacă LLM-ul tău poate citi imagini, pune-l să se uite la ele.

Pentru critica vizuală a paginii întregi: `file://` e blocat în multe unelte, deci:

```bash
cd "$LEADS_WORKDIR/mockupuri" && python3 -m http.server 8931
# apoi deschizi http://localhost:8931/<slug>.html
```

---

## 5. Capcane

- **Ghilimele românești** `„..."` cu `"` drept închid stringul în Python și strică fișierul.
  Folosește `"` peste tot în JSON.
- **LLM-ul completează golurile.** E cel mai periculos obicei aici. Program lipsă →
  „La programare", nu o oră inventată.
- **Recenzii pe măsura ratingului.** 3 recenzii extaziate pe o firmă cu 4.1★ se simt fals.
- **Nu template la indigo.** Variază între leaduri chiar în aceeași nișă — dacă suni 5
  florării cu același text, prima care compară îți arde toate cele 5.

---

## 6. Prompt de pornire, dacă vrei să pui un agent pe treabă

```
Repo: leads-toolkit. Citește README.md și docs/LLM.md.
Sarcină: găsește <N> leads REALI în <ORAȘ>, nișa <X>, fără site propriu.

Reguli nenegociabile:
1. Nimic inventat. Fiecare telefon/adresă/program vine din Google Maps.
   Ce nu poți verifica, nu intră.
2. Mockup-ul trebuie să FUNCȚIONEZE: wa.me cu numărul lor, tel:, hartă cu adresa lor.
3. Nu publica nimic: oprește-te la round<N>.json + generare locală. Publish-ul îl fac eu.
4. Arată-mi ce ai găsit înainte să scrii texte.
```

---

## 7. Prompt MARE — pune agentul pe TOT fluxul (autopilot cu checkpoint-uri)

Lipești ăsta într-un agent AI (Claude Code, într-un terminal deschis în orice folder — are
`LEADS_WORKDIR`/`LEADS_PY` setate). Rulează singur scrape → curățare → generare → publish,
dar **se oprește să ceri OK la momentele periculoase** (înainte de push live). Înlocuiește
`<ORAȘ>`, `<CÂTE>` și nișele.

```
Ești operatorul pipeline-ului leads-toolkit. Scopul: <CÂTE> leads REALE, publicabile,
în <ORAȘ>, gata de sunat. Lucrezi în terminal, ai voie să rulezi comenzi.

=== ÎNAINTE SĂ ÎNCEPI ===
1. Citește ~/leads-toolkit/README.md și ~/leads-toolkit/docs/LLM.md integral.
2. Confirmă că $LEADS_WORKDIR, $LEADS_PY, $LEADS_LIVE_BASE sunt setate (echo). Dacă nu,
   oprește-te și cere-mi-le — NU ghici, ca să nu publici în repo greșit.
3. T=~/leads-toolkit. Toate fișierele de date se creează în $LEADS_WORKDIR.

=== REGULI NENEGOCIABILE (dacă încalci una, ai stricat tot) ===
- NIMIC inventat: telefon/adresă/program/rating vin DOAR din Maps. Program lipsă ->
  "La programare", NU o oră inventată. Ce nu poți verifica, nu intră.
- Doar NIȘE UȘOARE (clientul caută online + vizual/ticket mare): detailing, florării,
  tapițerie, mobilă la comandă, GSM. NU vulcanizare/spălătorie auto/cizmărie/ceasornicărie.
- Mockup-ul TREBUIE să funcționeze: wa.me cu numărul lor, tel:, hartă cu adresa lor.
- Textele se scriu PER FIRMĂ (vezi §3 din LLM.md), nu template la indigo. Variază chiar
  în aceeași nișă — dacă 5 florării primesc același text, prima care compară le arde pe toate.
- NU suni și NU trimiți mesaje nimănui. Sunatul îl fac EU.

=== FLUXUL, CU OPRIRI ===
PAS A — Nișe: propune-mi 6-8 sub-căutări concrete (nișă + zonă), din cele ușoare. STOP,
  așteaptă "OK niște" de la mine.

PAS B — Scrape:
  $LEADS_PY $T/tools/pipeline_leads.py scrape --niches "<lista>" --max-per-niche 4 --min-reviews 20

PAS C — Curățare: deschide $LEADS_WORKDIR/pending_leads.json. Dă-mi un TABEL
  (nr | nume | nișă | rating/recenzii | PĂSTREZ/ARUNC + motiv). Aruncă lanțuri, instituții,
  nume care nu se potrivesc cu niche_key, listări moarte. Șterge din JSON ce e ARUNC.
  STOP, arată-mi tabelul, așteaptă "OK curat".

PAS D — Texte (opțional, dar recomandat): pentru fiecare lead rămas scrie copy v2 per firmă
  și regenerează. Dacă sari peste, folosești presetul generic (mai slab). Spune-mi ce alegi.

PAS E — Dry-run: rulează `publish --dry-run`, arată-mi cum arată prima intrare + câte mockup-uri.
  STOP. Publish-ul REAL (push live pe repo-ul meu) îl faci DOAR după ce scriu "GO PUBLISH".

PAS F — Publish: după "GO PUBLISH":
  $LEADS_PY $T/tools/pipeline_leads.py publish
  Confirmă că toate au dat live (HTTP 200) și că s-au scris în SITEURI_DE_TESTAT.txt.

PAS G — Raport final: câte leads publicate, la ce numere în listă, linkurile live, și
  ordinea de sunat (cele mai ușoare primele). Reamintește-mi tehnica de apel din §Quickstart
  (client deschide linkul LIVE cu mine, cer 30% avans pe reacție).

Pornește cu PAS A.
```

**De ce cu opriri și nu full-autopilot:** publish-ul face `git push` pe repo-ul tău public și
scrie linkuri live. Vrei să vezi ce iese ÎNAINTE, nu după. Agentul face 90% din muncă;
tu dai două "OK"-uri și un "GO". Dacă vrei mai agresiv, scoți STOP-urile de la PAS A/C — dar
lasă-l pe cel de la PAS E (publish), ăla te apără de 20 de site-uri proaste puse live.
