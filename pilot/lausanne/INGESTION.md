# Lausanne RPGA — Ingestion notes

How [`rpga_zones.json`](rpga_zones.json) was produced, what is in force, and what to trust.
This is the **capitalizable commune layer** for the pilot (see [`../../docs/strategy/knowledge-architecture.md`](../../docs/strategy/knowledge-architecture.md)):
ingested once, versioned, shared across all Lausanne projects, refreshed only when the règlement changes.

## Document in force

- **Règlement du Plan général d'affectation (PGA / RPGA), Ville de Lausanne — mis en vigueur le 26 juin 2006.**
  Source PDF: <https://www.lausanne.ch/dam/jcr:1d0dddd5-ad74-4bbc-ac15-e0050bd315d3/PGA_reglement.pdf> (59 pp.).
  Cross-checked against the parcel's OEREB extract, which lists "Plan général d'affectation Règlement",
  N°67379, dated 26.06.2006, authority DGTL.
- **Still in force for the urban territory (May 2026).** A general *Modification du PGA* (MPGA) + a *PACom*
  for the *territoires forains* went to public enquiry 17 Apr–16 May 2024 and were adopted (Préavis 2025/31),
  entry into force planned 2025 subject to oppositions — **but the MPGA does not change the plan des zones nor
  the per-zone envelope parameters of the urban territory**, and the PACom concerns only the territoires forains.
  So the values below remain those of the 2006 règlement.

## Key finding — Lausanne is envelope-based, not index-based

The 2006 PGA fixes density **geometrically** (ordre contigu/non contigu, building length, depth, façade height,
roof gabarit arcs) rather than by a floor-area ratio. Consequences for the data model:

- A numeric **IUS is fixed in only two zones**: *Zone mixte de faible densité* (IUS ≤ 0.50, Art. 119) and
  *Zone d'utilité publique* (IUS ≤ 2.0, Art. 129). Elsewhere `ius = null` means **not fixed**, not "unknown".
- **`ibus` = null everywhere** (the 2006 text predates AIHC/IBUS terminology; it uses IUS/CUS).
- **`ios` = null everywhere** (a COS is defined in the glossary but never imposed numerically).
- **Heights are "hauteur des façades"** (to cornice/acrotère); `height_faite_m = null` everywhere (the ridge is
  bounded indirectly by the roof gabarit arc, e.g. R = 8 m). For *Centre historique*, façade height is relative
  to the neighbour (Art. 89) → `height_corniche_m = null` is correct.

## Per-zone summary (full detail + verbatim in the JSON)

| Zone | IUS | Façade height | Levels | Setback min | Order |
|---|---|---|---|---|---|
| Centre historique | — | rel. au voisin (Art. 89) | — | 0 (contigu) | contigu |
| Zone urbaine | — | 15.5 / 17 m (selon D) | — | 6 m | contigu |
| Zone mixte forte densité | — | 14.5 m | — | 6 / 8 m | non contigu |
| Zone mixte moyenne densité | — | 13 m | — | 6 m | non contigu |
| **Zone mixte faible densité** | **0.50** | (par niveaux) | 2 + combles | 5 m | non contigu |
| **Zone d'utilité publique** | **2.0** | 17 m | — | 6 m | non contigu |
| Zone ferroviaire | — | — | — | — | droit féd./cant. |
| Parcs et espaces de détente | — | — | — | 5 m | inconstructible* |
| Équipements sportifs plein air | — | — | — | 5 m | restreint |
| Rives du lac | — | — | 1 | — | très restreint |
| Aire et zone forestières | — | — | — | — | régime forestier |

\* essentially inconstructible save small structures. Distances between buildings derive from Art. 28
(= 2 × setback) where applicable.

## Demo parcel mapping (parcel 10072, Place de la Palud)

OEREB designates 100% of the parcel as **"Zone centrale 15 LAT (Zone de centre historique)"** — the cantonal
harmonized type **NORMAT VD 1401**, which fixes *no* building parameter (it harmonizes only name/type/colour).
The parenthetical communal label maps to Lausanne's **"Centre historique"** zone (PGA Art. 83–94): ordre contigu,
façade height capped at the tallest contiguous neighbour, roof gabarit R = 8 m, ≥ 1/3 SBP housing — **no numeric
IUS or metric height**. The demo therefore correctly reports a *geometric* envelope, not a fabricated SBP figure.

## Gaps & cautions

- **Plans spéciaux override the PGA locally** (Art. 155–156): many areas are covered by plans partiels /
  plans de quartier / plans d'affectation cantonaux with their own parameters. For any parcel, check whether a
  plan spécial applies before relying on the zone defaults. (For parcel 10072, the in-force affectation is the
  general PGA's Centre historique zone.)
- Medium/low confidence zones: parcs, équipements sportifs, rives du lac (values from the synoptic Annexe 5);
  *aire et zone forestières* has no parameter articles (forestry law) — confidence low.
- Figures/tables in the PDF are partly raster; numeric values were taken from article text and cross-checked
  against the official **Annexe 5 "Tableau des zones"** (agreed in every case).

## Sources (re-verify before production)

- PGA règlement 2006 (binding): <https://www.lausanne.ch/dam/jcr:1d0dddd5-ad74-4bbc-ac15-e0050bd315d3/PGA_reglement.pdf>
- NORMAT directive v1.1 (cantonal zone typology, code VD 1401): <https://www.vd.ch/fileadmin/user_upload/themes/territoire/amenagement/Normat/20.06.01_Directive_NORMAT_v1.1.pdf>
- MPGA / PACom status: <https://www.lausanne.ch/officiel/grands-projets/lausanne-2030/plan-affectation-communal-pacom/modification-pga.html>
- Parcel OEREB extract: `https://www.rdppf.vd.ch/ws/RdppfSVC.svc/extract/json/?EGRID=CH915772367853&LANG=fr`

> Raw downloaded PDFs/text live under `sources/` (git-ignored — large binaries, re-downloadable from the URLs above).
> Refresh trigger: a new in-force PGA/MPGA affecting the plan des zones. Until then, this layer is canonical.
