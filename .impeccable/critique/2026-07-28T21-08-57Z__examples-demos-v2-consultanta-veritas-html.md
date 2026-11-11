---
target: template consulting (_v2_consultanta_veritas.html)
total_score: 23
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 2
timestamp: 2026-07-28T21-08-57Z
slug: examples-demos-v2-consultanta-veritas-html
---
# Critique: _v2_consultanta_veritas.html (consulting template)

Method: dual-agent (A: design review · B: detector + headless browser evidence)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Live open/closed + aria-live preview strong; no post-WhatsApp-handoff feedback |
| 2 | Match System / Real World | 3 | Natural Romanian; nav "Echipa" promises a team the section doesn't deliver |
| 3 | User Control and Freedom | 3 | Chips deselectable, message editable; dock WA discards composed selections |
| 4 | Consistency and Standards | 2 | Nav labels ≠ section headings; floral mark (florist ancestry) on an accounting firm |
| 5 | Error Prevention | 3 | Sensible fallback; skipped steps produce verbless fragments ("Un SRL activ.") |
| 6 | Recognition Rather Than Recall | 4 | Everything visible; message previewed verbatim |
| 7 | Flexibility and Efficiency | n/a | One-shot persuade page; dock + tel: cover it |
| 8 | Aesthetic and Minimalist Design | 3 | Disciplined type/color; 6 contact affordances above the fold; ~40% dead CSS |
| 9 | Error Recovery | 2 | JS off/blocked → #waBtn href="#", empty "Mesajul tău" box — primary CTA dead |
| 10 | Help and Documentation | n/a | The one needed hint exists exactly where needed |
| Total | | 23/32 (72%) | Good — solid foundation, dragged by consistency & resilience |

## Design Specificity Verdict
Copy is authored for an accountant (ANAF, Revisal, PFA/SRL/ONG); structure is category-interchangeable; hero imagery actively miscast (tech coworking scene vs. fiscal trust); floral mark + leaked #atelier ID betray florist template ancestry.
Detector: marquee (real, mitigated by hover-pause + reduced-motion), em-dash-overuse (advisory, 12). Mechanical green: 0 console errors, 0 failed images, fonts loaded, no horizontal overflow 1440/390, all measured contrasts pass AA, 0 imgs without alt, 0 unnamed buttons. Overlay injection not attempted (headless fallback).

## Priority Issues
1. [P1] Imagery miscast + duplicated — hero is tech-coworking; same photo reused as "Salarizare & HR" thumb; "team" is one anonymous stock woman. Fix: sober per-service unique imagery; pull lead's real Google Business photos in pitch flow.
2. [P1] Primary CTA dies without JS — #bilet empty, #waBtn href="#" until scrie() runs. Fix: ship default message + working wa.me href in static HTML; JS enhances only.
3. [P2] Dock WhatsApp discards composed message — generic BASE text next to ticket on mobile. Fix: sync dock WA href with composer state or hide dock while #comanda in view.
4. [P2] Fabricated reviews disclaimed at trust peak — "Citatele de mai sus sunt ilustrative" beside the real 4.9. Fix: 2–3 real Google review excerpts with first names, link the count to the profile, drop disclaimer.
5. [P2] IA label drift + archetype bleed — "Echipa"→#atelier "Cum lucrăm"; floral favicon/notecard/ticket mark. Fix: align nav labels, replace floral mark, rename leaked IDs.

## Persona Red Flags
- Jordan (pitched owner): sees an office visibly not his + a "team member" he doesn't employ; "ilustrative" disclaimer poisons trust in the real rating; nothing marks this as a proposal for him.
- Casey (mobile): topline wraps cramped at 390px; dock buttons cover ticket hint at composer; may send generic message instead of composed one.
- Riley (stress): step-b-only → verbless message; JS off → dead CTA; reduced-motion → ticker items unreachable; duplicated ticker content read twice by screen readers (no aria-hidden on clone).

## Minor Observations
- hoursbox "închis acum" ~3.9:1 at 0.72rem (below AA small text)
- ~250 lines dead CSS (unused archetype heroes) per page
- Footer missing CUI/Reg. Com., ANPC/SOL, privacy — conspicuous for a fiscal-compliance firm
- alt="Veritas Consulting" non-descriptive; "Sector 1" ×3 in first viewport
- Chips 42.5px tall (above WCAG 24px floor, 1.5px under iOS 44px)

## Questions
1. Per-category visual signatures (ledger motif, document texture) instead of shared floral iconography?
2. Should a cold pitch ever invent reviews and disclaim them when the real 4.9/21 can carry the section?
3. Why does the hero CTA bypass the composer (the page's crown jewel) with a generic message instead of scrolling to #comanda?
