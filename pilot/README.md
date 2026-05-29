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

- `mvp1_demo.py` — the end-to-end demonstrator.
- `lausanne/rpga_zones.json` — ingested per-zone building rules (indices/heights), with provenance + confidence.
- `lausanne/INGESTION.md` — how the règlement was ingested, sources, in-force status, gaps.

## The gap this closes

Switzerland exposes *which* zone applies (free API) but **not the numeric envelope** (indices/heights) — those
live only in the communal règlement PDFs. The Lausanne ruleset is a **one-time, capitalizable ingestion**,
refreshed only when the RPGA changes (see [`../docs/strategy/knowledge-architecture.md`](../docs/strategy/knowledge-architecture.md)).

> Status: pilot/demo, not production. Re-verify endpoints (some VD/federal routes are mid-migration) and the
> RPGA values (against the in-force règlement) before any real use.
