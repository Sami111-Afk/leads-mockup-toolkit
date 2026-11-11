# VANZARI.md — cum închizi dealuri cu pipeline-ul ăsta

Unealta găsește leads și generează site-uri. Partea care aduce banii e ce urmează:
contactul, oferta și follow-up-ul. Ghidul ăsta e procesul, în ordinea în care îl execuți.

---

## 0. Regula de aur: mesaj întâi, apoi telefon

**Trimite WhatsApp-ul cu linkul înainte să suni.** De ce:

- **Linkul e pitch-ul.** Un telefon fără link e „un tip care vinde site-uri" — spam.
  Un telefon după link e „ăla care mi-a făcut site-ul ăla cu numele meu pe el".
- Patronii de service/atelier au mâinile ocupate — nu răspund la numere necunoscute,
  dar se uită pe WhatsApp seara.
- Mesajul filtrează: cine deschide linkul și nu răspunde e călduț; cine nici nu-l
  deschide în 48h primește telefonul.

**Excepții — sună direct:**
- nișe „urgent" (tractări, parbrize, deblocări) — ăștia trăiesc cu telefonul în mână
  și răspund la orice număr;
- meșteri în vârstă (cizmărie, ceasornicărie) — unii nu folosesc WhatsApp;
- dacă mesajul are dublu-bif dar zero reacție după 2 zile — suni oricum, conform cadenței.

---

## 1. Funnel-ul, în cifre

Realist la început:

```
20 scrapate → ~15 valide → 10 contactate → 3-4 conversații → 1 deal
```

Vrei 4 clienți pe lună? Îți trebuie ~40-50 de contacte reale pe lună = **2-3 pe zi
lucrătoare**. Volumul e regele. Nu te oprești din contactat ca să „perfecționezi" —
mockup-ul e deja mai bun decât 90% din site-urile locale.

## 2. Cadența pe lead

| zi | acțiune |
|----|---------|
| 0, dimineața (9–11) | WhatsApp cu linkul live (mesajul de mai jos) |
| 0, după-amiaza | **a citit / a intrat pe link → suni AZI**, la 2-3 ore după citire |
| 1 | n-a citit ieri → telefon: „V-am scris ieri cu site-ul de probă — aruncați un ochi și vorbim" |
| 4 | follow-up scurt: „Mă interesează sincer părerea, chiar dacă e nu." |
| 10 | ultimul mesaj, apoi `pipeline_leads.py move N --status "FĂRĂ RĂSPUNS"` |

**Bifele decid, nu ceasul.** Semnalele, în ordinea forței:
1. **vizită pe mockup în GoatCounter** (setează `LEADS_ANALYTICS`, vezi README) —
   dashboard-ul arată vizitele per pagină = per lead; cine a intrat azi = lista de sunat azi;
2. **bifele albastre** pe WhatsApp = a citit mesajul;
3. nimic în 24h = telefonul de a doua zi devine „clopoțelul" care-l face să deschidă mesajul.

Citit + vizită pe link la aceeași oră = **sună acum**. Ritmul zilnic sănătos:
**dimineața trimiți, după-amiaza suni** pe tot ce s-a citit în ziua aia.

**80% din dealuri se închid la follow-up, nu la primul contact.** Concurența renunță
după primul mesaj — tu nu.

**Mesajul de deschidere:**

> Bună ziua! Am văzut că [Firma X] nu are site și v-am făcut unul de probă cu datele
> voastre reale — [link]. Dacă vă place, vorbim. Dacă nu, îl șterg, nicio problemă.

„Îl șterg, nicio problemă" dezarmează — nu ceri nimic, oferi ceva.
**Mesaje adaptate per nișă: [MESAJE.md](MESAJE.md)** — câte unul pentru fiecare
nișă din toolkit, scrise pe durerea specifică a fiecăreia.

**Când suni:** marți–joi, 10:00–12:00 sau 14:00–16:00. Lunea sunt ocupați, vinerea
nu decide nimeni nimic.

## 3. Oferta

- **Vinzi rezultatul, nu site-ul:** „clienții vă găsesc pe Google și vă scriu direct
  pe WhatsApp" — nu „design responsive cu HTML5".
- **Structura de preț:** setup 300–500€ + **mentenanță 25–50€/lună** (hosting, domeniu,
  modificări, poze noi). Abonamentul e afacerea reală: 20 clienți × 40€ = venit lunar
  predictibil. Domeniul + emailul pe numele lor sunt motivul natural al abonamentului.
- **Urgență onestă:** „mockup-ul rămâne live 2 săptămâni, apoi îl scot." E adevărat
  (nu ții zeci de mockupuri publicate) și motivează decizia.
- La „e scump": *„Pare că bugetul e problema — ce s-ar întâmpla dacă site-ul v-ar
  aduce doi clienți în plus pe lună?"* (risc inversat, nu discount).
- **Nu spune niciodată cât ți-a luat.** Prețul e pe valoare, nu pe oră.

## 4. Nișe și orașe

**Nișe de volum** (tichet mic, decizie rapidă): detailing, tapițerie auto, vulcanizare,
cizmărie, ceasornicărie, kineto, service GSM, reparații electrocasnice.

**Nișe de marjă** (tichet mare, ciclu mai lung): avocatură, consultanță/contabilitate —
arhetipul `birou`. Un avocat plătește 1000€+ dacă site-ul transmite încredere, dar
așteaptă mai mult și decide mai greu. **Volumul pe nișele ieftine, marja pe birou.**

**Orașe:** Cluj, Timișoara, Brașov (notate deja în README ca neexploatate) +
Constanța, Iași, Oradea, Sibiu — economie locală solidă, concurență de freelanceri
mult mai mică decât în București. Bonus: „am văzut că sunteți din Oradea" sună a
atenție, nu a spam.

**Pe cine suni primul:** scor = rating × log(recenzii). Firma cu 4,9★ și 80 de recenzii
trăiește din reputație și n-are site — ăla e lead-ul perfect.

## 5. Greșelile care omoară începutul

1. **Perfecționism pe mockup în loc de volum pe contact.** Trimite-l.
2. **Iei „nu"-ul personal.** E joc de numere. Un nu e un nu — next.
3. **Preț pe oră.** Niciodată. (Ți-a luat 5 minute cu generatorul.)
4. **Fără tracking.** `tested_leads.txt` cu status, religios. După 50 de contacte
   știi exact ce nișă/oraș/mesaj convertește — informația aia bate orice curs.

## 6. Resurse — alese pe situația asta exactă

**Cărți, în ordinea asta:**
1. *The Mom Test* — Rob Fitzpatrick: cum vorbești cu clienții fără să te mintă din
   politețe. Scurtă, direct aplicabilă la conversațiile de validare.
2. *$100M Offers* — Alex Hormozi: cum construiești o ofertă la care e greu să spui nu
   (garanții, bonusuri, risc inversat).
3. *Never Split the Difference* — Chris Voss: negociere și obiecții („e scump").

**YouTube:**
- **Fox Web School (Rob O'Rourke)** — literalmente nișa asta: site-uri vândute către
  afaceri locale, prețuri, scripturi de outreach. Cel mai relevant.
- **The Futur (Chris Do)** — cum vorbești despre preț și valoare; caută clipurile
  de „role play" cu negocieri reale.
- **Alex Hormozi** — volum + oferte; clipurile scurte despre closing ajung.
- **Charlie Morgan** — outreach la volum mare, mentalitate de prospectare.
