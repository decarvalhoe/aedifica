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
- `trust.py` — shared non-authority output contract footer and provenance tags.
- `constraints/mvp1_lausanne_matrix.json` — phase-aware constraint matrix for the Lausanne/VD pilot.
- `validate_matrix.py` — stdlib validator for the phase-aware matrix.
- `permit/vd_camac_checklist.json` — Vaud ACTIS-CAMAC baseline permit completeness checklist.
- `permit/demo_missing_dossier.json` — intentionally incomplete demo dossier proving missing-item detection.
- `compliance/ch_phase33_gates.json` — phase-33 compliance gates with legal/contractual typing.
- `validate_permit.py`, `validate_compliance.py` — stdlib validators for permit and compliance contracts.
- `research/swiss_phase_lifecycle_matrix.json` — Swiss/SIA-oriented phase lifecycle matrix with
  small/medium/large variants.
- `research/pilot_source_registry.json` — prioritized NOMOS-compatible source registry for CH/VD/Lausanne.
- `research/project_knowledge_regime.json` — context-first vs hybrid-index vs project-RAG decision model.
- `research/workflow_track_specs.json` — structured specs for model intelligence, tender, site and voice tracks.
- `research/adapter_capability_matrix.json` — BIM/CAD adapter capability map and first bridge decision.
- `research/practice_workflow_research.json` — Swiss competitions/study mandates and construction-management tool research.
- `research/business_positioning.json` — pricing hypothesis and integrate-vs-compete positioning map.
- `research/multilingual_regulatory_graph.json` — FR/DE/IT canonical regulatory graph contract.
- `validate_research.py` — stdlib validator for the research backbone.
- `projects/demo_lausanne_palud/` — first project workspace fixture with manifest, sources, evidence,
  reports and memory folders.
- `workspace.py`, `validate_workspace.py` — stdlib project-workspace contract and offline brief generation.
- `memory/demo_project_memory.json` — cross-phase project memory fixture with provenance-backed demo queries.
- `validate_memory.py` — stdlib validator and query demo for project memory.
- `cost/` — fee/profitability and eCCC/NPK/CFC bridge fixtures.
- `model_bridge_demo.py` — offline dry-run prototype for the local model bridge.
- `validate_cost.py` — fee/taxonomy validator and in-memory `.crbx` round-trip demo.
- `selfcheck.py` — offline smoke test of the pure logic, no network (`python pilot/selfcheck.py`, 48 checks).
- `registry/federal.json`, `registry/canton_vd.json` — shared CH core + VD cantonal layer (refs verified from a live OEREB extract).
- `lausanne/`, `pully/` — per-commune ingested rulesets (`rpga_zones.json`) + `INGESTION.md` (sources, in-force status, gaps).
  Lausanne is **geometric/IUS**; Pully is **IOS 20 %** — the same engine absorbs both styles (run `selector.py` to see it).

## The regulatory route (selector)

```
python pilot/selector.py     # shows: CH/federal + VD/cantonal + {Lausanne|Pully}/communal, only active layers consulted
python pilot/validate_packs.py
python pilot/validate_matrix.py
python pilot/validate_permit.py
python pilot/validate_compliance.py
python pilot/validate_research.py
python pilot/validate_workspace.py
python pilot/validate_memory.py
python pilot/validate_cost.py
```
Adding a commune = drop a `<slug>/rpga_zones.json`. Adding a country = add a federal/canton/commune layer set;
the selector logic is unchanged (see docs/strategy/knowledge-architecture.md).

## Pack contract and CI

Each regulatory pack declares a `schema_version` and `source_version` (`verified_at`, `review_due`, status).
`python pilot/validate_packs.py` checks the contract with stdlib only; `python pilot/selfcheck.py` includes
that validator and the output trust contract in the offline smoke suite. GitHub Actions runs both on pushes and PRs. See
[`../docs/architecture/jurisdiction-pack-contract.md`](../docs/architecture/jurisdiction-pack-contract.md).
Project workspaces also persist the selected regulatory route with active layers, inactive layers, timestamps,
source versions and freshness warnings. Commune support states are documented in
[`../docs/architecture/commune-support-policy.md`](../docs/architecture/commune-support-policy.md), with a repeatable
checklist in [`../docs/planning/next-commune-ingestion-checklist.md`](../docs/planning/next-commune-ingestion-checklist.md).

`python pilot/validate_matrix.py` validates the phase-aware constraint matrix described in
[`../docs/nomos/phase-aware-constraint-matrix.md`](../docs/nomos/phase-aware-constraint-matrix.md).
`python pilot/validate_permit.py` and `python pilot/validate_compliance.py` validate the phase-33 permit and
compliance contracts described in [`../docs/permit/vd-camac-permit-completeness.md`](../docs/permit/vd-camac-permit-completeness.md)
and [`../docs/compliance/phase33-compliance-gates.md`](../docs/compliance/phase33-compliance-gates.md).
`python pilot/validate_research.py` validates the Swiss phase lifecycle matrix, pilot source registry, and
project knowledge regime
described in [`../docs/research/swiss-phase-lifecycle-matrix.md`](../docs/research/swiss-phase-lifecycle-matrix.md)
[`../docs/research/pilot-source-registry.md`](../docs/research/pilot-source-registry.md), and
[`../docs/architecture/project-knowledge-regime.md`](../docs/architecture/project-knowledge-regime.md).
`python pilot/validate_workspace.py` validates the first project workspace fixture used by the R1 software
planning wave.
`python pilot/validate_memory.py` validates the cross-phase memory contract described in
[`../docs/architecture/project-memory-contract.md`](../docs/architecture/project-memory-contract.md).

## The gap this closes

Switzerland exposes *which* zone applies (free API) but **not the numeric envelope** (indices/heights) — those
live only in the communal règlement PDFs. The Lausanne ruleset is a **one-time, capitalizable ingestion**,
refreshed only when the RPGA changes (see [`../docs/strategy/knowledge-architecture.md`](../docs/strategy/knowledge-architecture.md)).

> Status: pilot/demo, not production. Re-verify endpoints (some VD/federal routes are mid-migration) and the
> RPGA values (against the in-force règlement) before any real use.
