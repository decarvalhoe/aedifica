# Pully RCATC — Ingestion notes

Second commune (after Lausanne) — ingested to prove the multi-level **selector** handles communes with a
*different rule style*. See [`../selector.py`](../selector.py) and [`../../docs/strategy/knowledge-architecture.md`](../../docs/strategy/knowledge-architecture.md).

## Document in force

- **Règlement communal sur l'aménagement du territoire et les constructions (RCATC), Pully** — approved
  7 Sep 2017, **in force 3 Nov 2017** (modification of the 2012 RCATC; abrogates the 1983 regulation).
  PDF: <https://www.pully.ch/media/kx2bz5gf/rcatc-2017-final-2017-11-03.pdf>
- Zoning map (PGA/PACom): last adaptation **2001** (layout v2017-11-22).
- A **zone réservée communale** (since 2023) overlays an *indice de pleine terre* 50 % + heritage (note 3)
  but does **not** change the indices/heights/levels below. **Pully 2040** (new PACom) is in revision, **not adopted**.

## Key contrast with Lausanne (why Pully was chosen)

| | Lausanne (PGA 2006) | Pully (RCATC 2017) |
|---|---|---|
| Density control | **geometric** (contiguïté, longueur, profondeur, hauteur façade, gabarit); IUS only in 2 zones | **IOS = emprise au sol max 20 %** in *all* building zones (Art. 10) — no IUS/IBUS |
| Height | "hauteur des façades" (corniche) | **hauteur au faîte** (ridge) |
| Net | geometric + sparse IUS | hybrid: one coverage index (IOS) + geometric gabarit |

This proves the engine + canonical-unit schema absorbs **different regulatory paradigms** behind one
selector — the point of the jurisdiction-pack design.

## Zones ingested (full detail + verbatim in `rpga_zones.json`)

| Zone | IOS | Hauteur au faîte | Niveaux | Distance min |
|---|---|---|---|---|
| Zone de villas | 0.20 | 10 m | 3 | 5 m |
| Habitation faible densité | 0.20 | 12 m | 3 | 5 m |
| Habitation moyenne densité | 0.20 | 15 m | 4 | 5 m |
| Habitation forte densité | 0.20 | 18 m | 5 | 5 m |
| Constructions d'utilité publique | 0.20 | 12 m* | — | 5 m |

\* applies to sport/loisirs surfaces, technical premises and public édicules ≤ 200 m² (Art. 41).

## Gaps & cautions

- **No IUS/IBUS** — confirmed absent (do not synthesise a floor-area ratio for Pully). Density = IOS 20 % + gabarit.
- `setback_min_m` = 5 m is a **floor**; the real setback grows with façade length (+0.30 m/m beyond 16 m) and
  corniche height >10 m (Art. 16).
- Heights are **au faîte**; `height_corniche_m` is null for every Pully zone.
- **Plans spéciaux override** (Art. 6): PPA/PQ/PEP perimeters and the city centre (Masterplan) carry their own
  parameters. Per-parcel local height caps via PGA sectors (Art. 19 al. 4) are not in the zone table.
- The 2023 *zone réservée* overlay (pleine terre 50 %, heritage note 3) must be layered for a real assessment.
- OCR caveat: the PDF's accents extract corrupted, but numeric values/articles/zone names are unambiguous;
  verbatims above have accents restored.

## Sources

- RCATC 2017 (binding): <https://www.pully.ch/media/kx2bz5gf/rcatc-2017-final-2017-11-03.pdf>
- PGA plan: <https://www.pully.ch/media/beddoecl/pully_pga_10_000_v2017-11-22.pdf>
- Règlements index: <https://www.pully.ch/fr/pully-officiel/reglements-et-directives/>
- Pully 2040 (revision context): <https://www.pully.ch/fr/vivre-a-pully/constructions/pully-2040/>

> Raw PDFs git-ignored under `sources/`. Refresh trigger: adoption of the Pully 2040 PACom.
