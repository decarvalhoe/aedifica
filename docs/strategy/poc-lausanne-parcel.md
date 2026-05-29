# PoC — Binding constraints from free Swiss APIs (Lausanne parcel)

> **Real, executed proof of concept (2026-05-29).** From a real Ville de Lausanne parcel, how far can we
> get retrieving *binding* construction constraints using only free public Swiss APIs — no credentials?
> Every call below was actually run; statuses and snippets are verbatim. This validates the MVP1 pipeline
> (see [`../specs/mvp1-parcel-constraints-intake.md`](../specs/mvp1-parcel-constraints-intake.md)) and gives
> the partner office something concrete to see.

**Test parcel:** Place de la Palud 1–5, 1003 Lausanne → parcels **10072 / 10073**, commune BFS **5586**,
**EGRID CH915772367853**.

## Bottom line

> From **a parcel number alone**, with **zero credentials**, we can already retrieve — fully machine-readable —
> the parcel **geometry + EGRID**, the **zone d'affectation**, the **noise sensitivity degree (DS)**, the
> **alignments**, the **presence/absence of all 21 federal RDPPF themes** (polluted sites, groundwater, forest…),
> and **links to the governing laws/règlements**. The one thing **not** exposed by any free API is the **numeric
> building envelope** (indices IUS/IBUS, heights, setbacks) — those live only inside the commune's règlement
> PDFs and plans. That gap is a **one-off, per-commune ingestion** (Lausanne first), refreshed only when the
> RPGA changes — exactly the "capitalizable commune layer" in [`knowledge-architecture.md`](knowledge-architecture.md).

## Evidence log (real calls)

| Endpoint | HTTP | Real snippet |
|---|---|---|
| `api3.geo.admin.ch/rest/services/api/SearchServer?searchText=Place de la Palud Lausanne&type=locations&sr=2056` | 200 | `"label":"Place de la Palud 1 1003 Lausanne","x":1152577.6,"y":2538191.0` (LV95) |
| `.../all/MapServer/identify?...&layers=all:ch.kantone.cadastralwebmap-farbe` | 200 | `"number":"10072","egris_egrid":"CH915772367853"` (+ parcel polygon rings, LV95) |
| `.../identify?...&layers=all:ch.are.bauzonen` | 200 | `"ch_bez_f":"Zones centrales","bfs_no":"5586"` (harmonized federal zone class) |
| `.../identify?...&layers=all:ch.swisstopo-vd.stand-oerebkataster` | 200 | `"oereb_status_fr":"Cadastre RDPPF introduit","oereb_webservice":"https://www.rdppf.vd.ch/ws/RdppfSVC.svc"` |
| `.../identify?...&layers=all:ch.bak.bundesinventar-schuetzenswerte-ortsbilder` (ISOS) | 200 | `{"results": []}` → point not inside an inventoried site |
| `rdppf.vd.ch/ws/RdppfSVC.svc/getegrid/xml/?GNSS=46.521636,6.633138` | 200 | `<egrid>CH915772367853</egrid>` (cantonal EGRID lookup by lat/lon) |
| `rdppf.vd.ch/ws/RdppfSVC.svc/extract/json/?EGRID=CH915772367853&LANG=fr` | 200 | 106 KB `{"Item":…}` — the full OEREB extract, machine-readable |
| `rdppf.vd.ch/ws/RdppfSVC.svc/extract/pdf/?EGRID=CH915772367853` | 200 | `%PDF` 3.0 MB — the official binding RDPPF extract |

**Parsed from the OEREB extract:**
- **Concerned themes (3):** `ch.Nutzungsplanung` → *"Zone centrale 15 LAT"* + *"Périmètres des plans d'affectation légalisés"*; `ch.Laermempfindlichkeitsstufen` → **Degré de sensibilité III**; `ch.VD.BaulinienCantonalstrassen` → *"Limite des constructions définie par un plan approuvé"*.
- **Not-concerned themes (18):** sites pollués, zones de protection des eaux, distances forêt, planungszonen, etc. — explicitly returned as not-concerned.
- **Legal provisions (links):** LATC (`prestations.vd.ch/.../700.11`), LAT (`fedlex.admin.ch/eli/cc/1979/1573`), + cantonal acts.

**Honest failures noted:** the old federal OEREB route on `api3.geo.admin.ch/.../ch.swisstopo-vd.oereb/extract/…` → 404 (service moved; use the cantonal `rdppf.vd.ch` service); BAFU noise raster layers aren't point-identifiable on the `all` MapServer (the DS comes from the OEREB extract instead); the cantonal ArcGIS `ags.map.vd.ch/.../CRDPPF/MapServer` is **token-gated** (not freely queryable — rely on the OEREB classification + published plans).

## What we can retrieve vs not

| Data item | Status | Source |
|---|---|---|
| Parcel geometry (LV95) | ✅ Free API | swisstopo identify (cadastralwebmap) |
| Parcel № + EGRID | ✅ Free API | swisstopo identify; VD getegrid |
| Zone d'affectation (label) | ✅ Free API | OEREB extract; federal `ch.are.bauzonen` |
| RDPPF/ÖREB themes (which apply) | ✅ Free API | VD OEREB JSON/XML extract |
| Noise — degré de sensibilité (DS) | ✅ Free API | OEREB extract → DS III |
| Alignements / limites des constructions | ✅ Free API (existence + type) | OEREB extract |
| Polluted sites, water, forest… | ✅ Free API (presence/absence) | OEREB not-concerned themes |
| ISOS protected sites | ✅ Free API | swisstopo ISOS layer |
| Governing law / règlement text | 🔗 Link via API → PDF | OEREB legal-provisions URLs |
| **Indices IUS/IBUS** | ❌ Only in PDF/plan | RPGA/PGA — not exposed as data |
| **Distances, hauteurs, gabarits, niveaux** | ❌ Only in PDF/plan | RPGA/PGA + zone plans |

## Recommended MVP1 pipeline (validated)

1. **Address/parcel → coordinates:** `SearchServer?type=locations&sr=2056`.
2. **Coordinates → EGRID + geometry:** identify on `ch.kantone.cadastralwebmap-farbe` (or VD `getegrid` by lat/lon).
3. **EGRID → binding constraints:** **VD OEREB extract** `rdppf.vd.ch/ws/RdppfSVC.svc/extract/json/?EGRID={EGRID}&LANG=fr` (+ `/pdf/` for the human-facing legal extract). One call yields zone, DS, alignments, every theme's presence/absence, and law links.
4. **Context overlays (optional, free):** `ch.are.bauzonen`, ISOS.
5. **Commune (Lausanne) layer — the bounded gap:** fetch the RPGA/PGA PDFs (URLs handed by the OEREB legal-provisions) and parse the **per-zone parameter tables** (IUS/IBUS, heights, setbacks, levels) into a structured ruleset keyed by zone code (e.g. "Zone centrale"). One-time per commune, refreshed on RPGA change.

## Why this matters for the pitch

- **"Du solide" today:** type a Lausanne address → seconds later, a sourced constraints sheet with the zone, the noise DS, the alignments, and the exact laws — *before any drawing, no model needed.*
- **The moat is the commune layer:** Switzerland never exposes the numeric envelope as data; whoever ingests and maintains it per commune owns something competitors must rebuild.
- **Confirms the wedge:** MVP1 needs only public registries + one Lausanne ingestion — not BIM, not Archicad. Fits the partner office and any office.

## Demo script (to run live)

```
1. Enter "Place de la Palud, Lausanne"        → parcel 10072, EGRID CH915772367853
2. Show parcel outline on map                  (swisstopo geometry)
3. One click → constraints sheet:
     Zone:  Zone centrale (15 LAT)
     Bruit: Degré de sensibilité III
     Alignements: limite des constructions (plan approuvé)
     Pas concerné: sites pollués, eaux, forêt …
     Lois: LATC 700.11, LAT (fedlex) — clickable
4. Then: "indices & hauteurs" → pulled from the Lausanne RPGA layer (ingested)
5. Risk & unknowns list auto-generated
```

_All endpoints public, no API key. Re-verify against live services before shipping (some routes are mid-migration)._
