# Pilot — MVP1 end-to-end demo (Lausanne / VD)

First runnable code of the project: a thin, honest end-to-end demonstrator of **MVP1 Parcel & Constraints
Intake** (spec: [`../docs/specs/mvp1-parcel-constraints-intake.md`](../docs/specs/mvp1-parcel-constraints-intake.md);
proof: [`../docs/strategy/poc-lausanne-parcel.md`](../docs/strategy/poc-lausanne-parcel.md)).

## What it does

From a Lausanne **address or parcel**, it produces a **sourced constraints + buildable-envelope sheet**, with
**no BIM model**, using only free public Swiss APIs + the ingested communal règlement:

```
address ──[swisstopo SearchServer]──▶ LV95 coords
        ──[swisstopo identify, cadastre]──▶ EGRID + polygon ──▶ parcel area (shoelace)
EGRID   ──[VD OEREB extract]──▶ zone · noise DS · alignments · laws · theme presence
zone    ──[Lausanne RPGA ruleset]──▶ IUS/IBUS · IOS · heights · levels
compute ──▶ max SBP = area × index ; footprint = area × IOS
```

Every output line is **provenance-tagged** — the trust contract in action:

| Tag | Meaning |
|---|---|
| `[api]` | sourced from a public API (swisstopo / VD OEREB) |
| `[RPGA]` | sourced from the communal règlement (document) |
| `[calc]` | computed from sourced inputs |
| `[assumption]` / `[unknown]` | flagged, never silently asserted |

> The output is a **preparation & evidence** sheet, never an authority — the architect decides.

## Run

```bash
python pilot/mvp1_demo.py                      # default demo parcel (Place de la Palud, 10072)
python pilot/mvp1_demo.py "Avenue de Cour 1 Lausanne"
python pilot/mvp1_demo.py CH915772367853       # by EGRID
```

Python 3.9+ (stdlib only — `urllib`, `json`, `math`). No keys, no install. Needs outbound HTTPS to
`api3.geo.admin.ch` and `www.rdppf.vd.ch`. The verified demo parcel uses PoC-checked constraint values while
still performing the live OEREB fetch (shown as byte count).

## Files

- `mvp1_demo.py` — the end-to-end demonstrator (commune-aware: Lausanne, Pully).
- `oereb.py` — robust VD OEREB/RDPPF parser; works for **any VD parcel** (`python pilot/oereb.py <EGRID>`).
- `opposition_radar.py` — MVP2 opposition/recours-risk radar (`python pilot/opposition_radar.py [addr] [height_m]`).
- `fiche.py` — printable **A4 HTML fiche** per parcel combining constraints + envelope + radar (`python pilot/fiche.py [addr] [height_m]` → `pilot/out/`).
- `selector.py` — the **regulatory route**: composes Federal + canton + commune layers (`python pilot/selector.py`).
- `registry/federal.json`, `registry/canton_vd.json` — shared CH core + VD cantonal layer (refs verified from a live OEREB extract).
- `lausanne/`, `pully/` — per-commune ingested rulesets (`rpga_zones.json`) + `INGESTION.md` (sources, in-force status, gaps).
  Lausanne is **geometric/IUS**; Pully is **IOS 20 %** — the same engine absorbs both styles (run `selector.py` to see it).

## The regulatory route (selector)

```
python pilot/selector.py     # shows: CH/federal + VD/cantonal + {Lausanne|Pully}/communal, only active layers consulted
```
Adding a commune = drop a `<slug>/rpga_zones.json`. Adding a country = add a federal/canton/commune layer set;
the selector logic is unchanged (see docs/strategy/knowledge-architecture.md).

## The gap this closes

Switzerland exposes *which* zone applies (free API) but **not the numeric envelope** (indices/heights) — those
live only in the communal règlement PDFs. The Lausanne ruleset is a **one-time, capitalizable ingestion**,
refreshed only when the RPGA changes (see [`../docs/strategy/knowledge-architecture.md`](../docs/strategy/knowledge-architecture.md)).

> Status: pilot/demo, not production. Re-verify endpoints (some VD/federal routes are mid-migration) and the
> RPGA values (against the in-force règlement) before any real use.
