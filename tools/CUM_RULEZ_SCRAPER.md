# Scraper Google Maps — leads fără site

## Setup (o singură dată)
```
python3 -m venv ~/.venvs/leads
~/.venvs/leads/bin/pip install playwright
# browserele Chromium sunt deja în ~/.cache/ms-playwright (le găsește automat)
```

## Rulare
```
~/.venvs/leads/bin/python scrape_maps_leads.py --niches-file niches.txt \
    --min-rating 4.3 --min-reviews 20 --max-per-niche 5 --out leads_found.json
```
Sau nișe inline:
```
~/.venvs/leads/bin/python scrape_maps_leads.py \
    --niches "tapiterie auto Bucuresti,vulcanizare Bucuresti" --max-per-niche 5
```

## Ce face
- caută fiecare nișă, derulează feed-ul, ia firmele FĂRĂ buton Website, cu telefon MOBIL
- deschide fiecare candidat și confirmă web=null (site real) — Facebook = lead valid (fb_only)
- deduplică față de listele existente (SITEURI_DE_TESTAT.txt etc.)
- scoate leads_found.json (nume, telefon, adresă, program, rating, recenzii, niche_key, palette)

## Parametri utili
--min-rating 4.3   --min-reviews 20   --max-per-niche 5   --scroll 7
--all-phones (acceptă și fixe)   --no-verify (mai rapid, mai puțin sigur)
--headed (vezi browserul)   --emit-round 11 (scrie și round11.json schelet pt mockup_gen.py)

## Apoi mockup-uri
`leads_found.json` are datele. Pentru site-uri bune, un LLM rescrie textele per lead în
round<N>.json (paletă+servicii+copy), apoi: `python mockup_gen.py round<N>.json`.
`--emit-round` scoate un schelet automat, dar cu text GENERIC (calitate mai slabă).
