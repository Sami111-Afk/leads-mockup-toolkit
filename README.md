# leads-mockup-toolkit

Pipeline semi-automat pentru găsit clienți mici (afaceri locale **fără site**) și trimis
un **mockup live, funcțional, cu datele lor reale** — ca pitch.

```
scrape (Google Maps)  →  revizuire umană  →  generare site  →  push + GitHub Pages  →  sunat/WhatsApp
```

Ideea: firmele fără site nu se pot compara cu nimic. Când le trimiți un link cu numele lor,
telefonul lor, programul lor, poza lor de nișă — conversia e mult mai bună decât un mesaj generic.

---

## 1. Setup (o singură dată)

```bash
git clone <URL-ul-acestui-repo> leads-toolkit
cd leads-toolkit

python3 -m venv ~/.venvs/leads
~/.venvs/leads/bin/pip install -r requirements.txt
~/.venvs/leads/bin/playwright install chromium
```

Ai nevoie și de `git` configurat cu contul tău GitHub (`gh auth login` e cel mai simplu).

### Repo-ul de lucru (citește, e important)

**`leads-toolkit` e doar unealta — nu lucrezi în el și nu comiți în el.**
Ai nevoie de un **repo al tău, public, cu GitHub Pages activat**, unde ajung
mockup-urile și listele. Îi spui uneltei unde e prin `LEADS_WORKDIR`.

```bash
# 1. unealta (o clonezi oriunde, o lași în pace)
git clone https://github.com/Sol111-Afk/leads-mockup-toolkit.git ~/leads-toolkit

# 2. repo-ul TĂU de publicare
gh repo create leads-<numele-tau> --public --clone
cd leads-<numele-tau>
mkdir mockupuri
cp ~/leads-toolkit/{SITEURI_DE_TESTAT.txt,tested_leads.txt} .
git add -A && git commit -m "setup" && git push

# 3. Settings → Pages → branch-ul principal, folder / (root)
```

Apoi în `~/.bashrc` (sau `~/.config/fish/config.fish` cu `set -gx`):

```bash
export LEADS_WORKDIR="$HOME/leads-<numele-tau>"
export LEADS_LIVE_BASE="https://<user-ul-tau>.github.io/leads-<numele-tau>/mockupuri"
export LEADS_PY="$HOME/.venvs/leads/bin/python"
export LEADS_CONTACT_NAME="Prenumele Numele"
# opțional, dar valoros: analytics per mockup (vezi mai jos)
export LEADS_ANALYTICS="<codul-tau-goatcounter>"
```

### Interfața grafică — pentru cine nu vrea terminal

Tot fluxul are și o pagină web locală, gândită pentru cineva non-tehnic (persoana care dă telefoane):

```bash
python3 tools/app.py        # deschide singur http://127.0.0.1:7788
```

Tab-uri: **Caută leads** (formularul scraperului) → **Revizuire** (editezi/ștergi leadurile
înainte de publicare) → **Publicare** (test sau live, cu log în pagină) → **De sunat**
(fișe de apel: telefon, buton WhatsApp cu mesajul per nișă gata scris, link mockup,
statusuri rapide care mută firma la Istoric) → **Istoric**. Serverul ascultă doar pe
localhost și folosește pe dedesubt exact `pipeline_leads.py` — nimic nu se schimbă în flux.

### Analytics: află CINE ți-a deschis linkul (GitHub Pages nu-ți spune)

Pages nu are loguri de acces. Fă-ți un cont gratuit pe [goatcounter.com](https://www.goatcounter.com)
(fără card, fără cookies — nu-ți trebuie cookie banner), alege un cod (ex. `leads-numele-tau`)
și setează `LEADS_ANALYTICS=leads-numele-tau`. Din acel moment, orice mockup generat
raportează vizitele, iar dashboard-ul `leads-numele-tau.goatcounter.com` arată
**vizitele per pagină = per lead**. Cine ți-a deschis linkul azi = lista de sunat azi
(cadența completă în `docs/VANZARI.md`). Nesetat → mockup-urile nu includ niciun tracking.

Din momentul ăsta rulezi uneltele de oriunde și tot ce generează, comite și pushează
merge în repo-ul **tău**:

```bash
python3 ~/leads-toolkit/tools/pipeline_leads.py publish
```

Dacă uiți să setezi `LEADS_WORKDIR`, unealta refuză să pornească — nu-ți lasă mockup-urile
în repo greșit:

```
[!] origin = https://github.com/Sol111-Afk/leads-mockup-toolkit.git
    Ăsta e repo-ul UNELTEI, nu al tău — n-ai ce publica aici.
```

Branch-ul e detectat automat (`main` sau `master`, cum îl ai). `publish --no-push`
generează și comite local, fără să publice.

⚠️ Repo-ul de lucru trebuie **public** — Pages nu merge pe privat la conturi free. Deci
`SITEURI_DE_TESTAT.txt`, cu telefoanele leadurilor, devine public. Dacă te deranjează,
adaugi listele în `.gitignore` și le ții local.

Setează unde publici (pune-le în `~/.bashrc` / `~/.config/fish/config.fish`):

```bash
export LEADS_LIVE_BASE="https://<user-ul-tau>.github.io/<repo-ul-tau>/mockupuri"
export LEADS_PY="$HOME/.venvs/leads/bin/python"
```

> `LEADS_LIVE_BASE` trebuie să fie exact URL-ul Pages al repo-ului tău, altfel linkurile
> din listă arată spre alt site.

---

## 2. Fluxul complet (varianta scurtă)

```bash
# (T = ~/leads-toolkit, unde ai clonat unealta)
# 1. caută leads noi
python3 $T/tools/pipeline_leads.py scrape --niches-file $T/niches/niches.txt --max-per-niche 3

# 2. DESCHIDE pending_leads.json și verifică-l cu ochii tăi  ← pasul care contează
#    (tu ești „omul de la mijloc": arunci gunoiul, corectezi textele)

# 3. generează site-urile + push + confirmă că sunt live + adaugă în listă
python3 $T/tools/pipeline_leads.py publish

# 4. după ce ai sunat un lead, mută-l din lista de testat în cea testată
python3 $T/tools/pipeline_leads.py move 23 --status "CONTACTAT — așteaptă răspuns"
```

Fișierele se creează în `$LEADS_WORKDIR` (repo-ul tău), nu în cel al uneltei:

| fișier | ce e |
|---|---|
| `pending_leads.json` | leads proaspete, **de revizuit manual** înainte de publish |
| `mockupuri/*.html` | site-urile generate (ce se publică pe Pages) |
| `SITEURI_DE_TESTAT.txt` | leads publicate, de sunat — cu telefon, program, link live |
| `tested_leads.txt` | leads deja contactate + status |

---

## 3. Uneltele, una câte una

### `tools/scrape_maps_leads.py` — găsește firmele

Caută pe Google Maps (Playwright, browser real) și scoate doar firmele **fără site propriu**,
cu **telefon mobil** (ca butonul WhatsApp să meargă).

```bash
$LEADS_PY tools/scrape_maps_leads.py --niches-file niches/niches.txt \
    --min-rating 4.3 --min-reviews 20 --max-per-niche 5 --out leads_found.json
```

sau nișe inline:

```bash
$LEADS_PY tools/scrape_maps_leads.py \
    --niches "tapiterie auto Bucuresti,vulcanizare Bucuresti" --max-per-niche 5
```

Ce face, pe bune:
- derulează feed-ul rezultatelor și ia firmele **fără buton „Website"**
- **deschide fiecare candidat** și reconfirmă `web=null` — feed-ul minte uneori
- dacă „site-ul" e o pagină de Facebook → e tot lead valid, marcat `fb_only`
- deduplică față de listele existente (`SITEURI_DE_TESTAT.txt`, `tested_leads.txt`, …)
- filtrează după rating și număr de recenzii

Parametri utili:

| flag | efect |
|---|---|
| `--min-rating 4.3` | doar firme bine cotate (au clienți, au bani) |
| `--min-reviews 20` | ignoră listările moarte |
| `--max-per-niche 5` | câte leads pe nișă |
| `--scroll 7` | cât de adânc derulează feed-ul |
| `--all-phones` | acceptă și telefoane fixe (fără WhatsApp) |
| `--no-verify` | mai rapid, dar mai puțin sigur (sare confirmarea pe detaliu) |
| `--headed` | vezi browserul lucrând — util când Google schimbă layout-ul |

### `tools/mockup_gen2.py` — construiește site-ul

Un motor + **4 arhetipuri** de layout, fiecare cu identitate proprie:

| arhetip | ton | pentru |
|---|---|---|
| `atelier` | meșteșug editorial, hârtie + serif | florărie, cizmărie, ceasornicărie, tapițerie, croitorie, mobilă |
| `urgent` | asfalt întunecat, telefon uriaș | parbrize, tractări, deblocări, electrică auto la domiciliu |
| `studio` | vizual premium, galerie, minimal | detailing, vopsitorie, optică |
| `cabinet` | calm, programare, program în față | kineto, reparații electrocasnice, GSM |

Toate includ: compozitor WhatsApp (mesaj precompletat din câțiva pași),
stare „Deschis/Închis acum" pe fusul București calculată din programul real,
ticker tematic, recenzii cu rating real, JSON-LD, `prefers-reduced-motion`.

```bash
python3 tools/mockup_gen2.py leads_v2.json                                  # generează în mockupuri/
python3 tools/mockup_gen2.py --from-scraped leads_found.json --out-json round_v2.json
```

A doua comandă convertește output-ul scraperului în format v2 folosind presetări pe nișă.
Rezultatul e **decent, dar generic** — vezi secțiunea 4.

Vezi `examples/demos/` pentru 4 rezultate reale, deschide-le în browser.

### `tools/pipeline_leads.py` — leagă totul

```bash
python3 tools/pipeline_leads.py scrape   [--niches-file …] [--max-per-niche N]
python3 tools/pipeline_leads.py publish  [fisier.json] [--dry-run] [--no-push] [--force]
python3 tools/pipeline_leads.py move  23 --status "CLIENT ✔" [--no-push]
```

Ordinea din `publish`, ca să știi ce se întâmplă când: generează HTML → **commit + push
mockup-uri** → așteaptă HTTP 200 pe linkul live → **commit + push listă**. Deci face
**două** push-uri, iar primul se întâmplă înainte de orice verificare.

Dacă Pages nu răspunde, se oprește înainte de pasul cu lista (`--force` sare peste).
Mockup-urile rămân pushate, dar lista rămâne curată — adică
`publish` nu scrie în `SITEURI_DE_TESTAT.txt` decât **după** ce a primit
HTTP 200 pe linkul live. Adică lista nu conține niciodată linkuri moarte pe care să le
trimiți unui client. Folosește `--dry-run` cât înveți — generează local, fără push.

### `tools/mockup_gen.py` — generatorul v1 (NU-L FOLOSI)

Prima versiune: **un singur template** parametrizat doar prin paletă de culori. Toate
site-urile ieșeau la fel, se vedea că-s turnate în serie. v2 l-a înlocuit complet —
`pipeline_leads.py` importă doar `mockup_gen2`.

E păstrat pentru referință (uneori mai furi din el o paletă sau o secțiune), dar nu-l
băga în flux. **Schemele JSON sunt incompatibile** între v1 și v2:

| | v1 | v2 |
|---|---|---|
| titlu | `h1` | `h1_a` + `h1_wonk` + `h1_b` |
| layout | `palette` (doar culori) | `archetype` (4 layout-uri diferite) + `accent` |
| program | `hours` (listă de text) | `hours_s` (structurat → stare „Deschis acum") |
| WhatsApp | link simplu | `composer` (mesaj precompletat din pași) |
| povestea firmei | — | `story`, `ticker` |

⚠️ **Capcană:** flag-ul `--emit-round` din scraper scrie schelet în **format v1**, nu v2.
Dacă vrei să pornești de la scraper spre v2, folosește:
`python3 tools/mockup_gen2.py --from-scraped leads_found.json --out-json round_v2.json`

---

## 4. Partea care cere cap, nu script

> 📖 **Ghid separat: [`docs/LLM.md`](docs/LLM.md)** — cine ce face (script vs LLM vs tu),
> prompturi gata de copiat pentru fiecare pas, și lecția cu nișele care nu convertesc.

`--from-scraped` scoate texte generice. Site-urile care chiar conving au fost făcute așa:
iei `leads_found.json`, și pentru fiecare lead **rescrii tu textele** în `round<N>.json` —
titlu, servicii reale ale firmei ăleia, pașii din compozitorul WhatsApp, paleta. Un LLM
(Claude) face treaba asta bine dacă îi dai datele lead-ului și schema din docstring-ul
lui `mockup_gen2.py`.

Diferența dintre „un site generat" și „site-ul lor" e exact pasul ăsta. Nu-l sări.

---

## 5. Reguli (din experiență, nu teoretice)

> 📖 **Ghid separat: [`docs/VANZARI.md`](docs/VANZARI.md)** — cum închizi dealuri:
> mesaj vs. telefon, cadența de follow-up, structura de preț, nișe/orașe, resurse.

- **Doar firme reale, verificate.** Fiecare lead trebuie confirmat pe Google Maps sau
  Facebook că există și că n-are site. Un mockup trimis unei firme care are deja site
  te arde instant.
- **Datele lor, corecte.** Telefon, adresă, program — copiate exact. Butoanele Sună /
  WhatsApp / Hartă trebuie să funcționeze când dai click.
- **Verifică linkul live înainte să-l trimiți.** `publish` o face automat; dacă publici
  manual, deschide-l tu.
- **Mockup-ul e o propunere, nu o publicare.** Nu e site-ul lor oficial, nu-l indexa
  agresiv, nu folosi logo-uri pe care nu ai dreptul să le folosești.
- **Ritm sănătos de scraping.** Nu porni 20 de nișe în paralel — Google îți dă captcha
  și pierzi o zi. Runde de 3–5 nișe.
- **Nu insista.** Un „nu" la telefon e un „nu". Treci la următorul.

---

## 6. Nișe

În `niches/` sunt listele folosite până acum. O nișă pe linie, orașul se adaugă automat
dacă lipsește. Ce a mers cel mai bine: meserii cu client fizic și marjă bună —
tapițerie auto, vulcanizare, detailing, cizmărie, ceasornicărie, reparații electrocasnice,
croitorie, kineto, service GSM.

Copiază `niches/niches.txt` într-un fișier nou și schimbă orașul dacă lucrezi în alt oraș —
`Cluj-Napoca`, `Timisoara`, `Brasov` sunt neexploatate.

---

## 7. Probleme frecvente

| simptom | cauză / fix |
|---|---|
| scraperul scoate 0 leads | Google a schimbat layout-ul sau ai primit captcha. Rulează cu `--headed` și uită-te. |
| „chromium not found" | `~/.venvs/leads/bin/playwright install chromium` |
| `publish` zice că linkul nu e live | GitHub Pages are 1–2 min de build. Mai rulează o dată. |
| linkurile arată spre alt user | n-ai setat `LEADS_LIVE_BASE` (vezi secțiunea 1) |
| firma din listă are totuși site | feed-ul Maps a mințit; nu rula cu `--no-verify` |

---

## 8. Cum contribui

Repo privat. Lucrează pe branch și deschide PR, sau commit direct pe `master` dacă e o
listă de nișe / un lead nou — nu blocăm treaba pentru formalități.

Ce ar ajuta cel mai mult, în ordine:
1. **Nișe și orașe noi** — testate, cu rată de răspuns notată.
2. **Un al 5-lea arhetip** în `mockup_gen2.py` (retail/magazin lipsește).
3. **Robustețe la scraper** — selectoarele Google se schimbă des.
4. **Un scor pe lead** (rating × recenzii × lipsă site) ca să știi pe cine suni întâi.
5. **Prompturi mai bune** în `docs/LLM.md` — dacă găsești o formulare care scoate copy
   mai bun, pune-o acolo. E cel mai ieftin câștig din tot pipeline-ul.
