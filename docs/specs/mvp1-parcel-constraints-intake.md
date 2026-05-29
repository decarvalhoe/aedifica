# MVP1 Spec — Parcel & Constraints Intake

> Implementation-ready specification for the first MVP (sharpens issue #15 "NOMOS Archi Intake").
> Grounded in the validated pipeline of [`../strategy/poc-lausanne-parcel.md`](../strategy/poc-lausanne-parcel.md)
> and the architecture of [`../strategy/knowledge-architecture.md`](../strategy/knowledge-architecture.md).
> Pilot jurisdiction: **Vaud / Ville de Lausanne** (FR). Status: draft for build.

## 1. Goal

From **a parcel** (number/address) + a **client program**, produce a **sourced, phase-aware constraints brief
and a legal buildable envelope** — with no BIM model required. Every fact is either linked to an official
source or explicitly flagged as an assumption.

## 2. In / out of scope

**In:** parcel intake; federal + cantonal (VD) + communal (Lausanne) constraints; buildable envelope; risk &
unknowns list; project brief; the per-project selector (regulatory route); the trust/evidence contract.

**Out (later MVPs):** opposition-risk scoring (MVP2), permit dossier assembly (MVP2), fee/cost (MVP3), BIM/model
work (Later/Track B), multi-commune corpus beyond Lausanne (on-demand later).

## 3. User & primary use case

A small/mid Swiss architect (the partner office, and any office) at **phase 0–1 (intake/feasibility)** asks:
*"I have this parcel and this program — what constrains it, what can I build, what's risky, what's unknown?"*
and gets an answer in seconds, sourced, before any drawing.

## 4. Inputs

- Parcel identifier: address **or** parcel № **or** EGRID **or** map click (lat/lon).
- Commune + canton (derived from the parcel; pilot fixed to Lausanne/VD).
- Client program (free text / structured: usage, target area, units, budget order).
- Optional: existing documents (PDF/notes) for the project context.

## 5. Data pipeline (validated — see PoC)

| Step | Action | Endpoint / source | Output |
|---|---|---|---|
| 1 | Address/parcel → LV95 coords | `api3.geo.admin.ch/rest/services/api/SearchServer?type=locations&sr=2056` | coordinates, GWR id |
| 2 | Coords → EGRID + geometry | identify `all:ch.kantone.cadastralwebmap-farbe` (or VD `RdppfSVC.svc/getegrid/xml/?GNSS=lat,lon`) | EGRID, parcel polygon |
| 3 | EGRID → binding constraints | **VD OEREB** `rdppf.vd.ch/ws/RdppfSVC.svc/extract/json/?EGRID={EGRID}&LANG=fr` (+ `/pdf/`) | zone, DS noise, alignments, all RDPPF themes (presence/absence), legal links |
| 4 | Context overlays | identify `ch.are.bauzonen` (zone class), `ch.bak.bundesinventar-…-ortsbilder` (ISOS) | harmonized zone, protected-site flag |
| 5 | Commune envelope (the gap) | Lausanne **RPGA/PGA** PDFs (URLs from step-3 legal provisions), parsed into per-zone tables | IUS/IBUS, heights, setbacks, levels, by zone code |
| 6 | Compose | run the selector: Federal core + VD + Lausanne; assemble units | constraints matrix + envelope + brief |

**Provenance rule:** steps 1–4 are `sourced:api`; step 5 fields are `sourced:document` (cite RPGA article +
version + retrieval date); anything inferred is `assumption` and visibly flagged. Never silently mix.

## 6. Outputs (data model)

1. **Source registry** — every source with `{id, type(federal|cantonal|communal|parcel), uri, version, retrieved_at, allowed_use}`.
2. **Constraint matrix** — list of canonical units (see §7), each phase-tagged, source-linked, and tied to a phase-specific action (see [`../nomos/phase-aware-constraint-matrix.md`](../nomos/phase-aware-constraint-matrix.md)).
3. **Buildable envelope** — `{zone, IUS, IBUS, IOS, max_height, setbacks{N,E,S,W}, max_levels, DS_noise, alignments[], derived_max_SBP, est_units}` — each field carrying `provenance` (api | document | assumption | unknown).
4. **Risk list** — constraints likely to block/shrink (e.g. alignment, DS, servitude, protected fabric).
5. **Unknowns & required human decisions** — what's missing to proceed.
6. **Project brief** — a readable synthesis for the architect + a machine context object for downstream agents.

## 7. Canonical unit (NOMOS, MVP1 subset)

```yaml
unit_id: VD-LSN-ZONE-CENTRALE-IUS
unit_type: constraint           # rule|term|requirement|constraint|exception|decision|evidence
level: communal                 # federal|cantonal|communal|parcel
phase_applicability: ["1","31"]
domain: zoning
business_rule: "IUS max = <value> in Zone centrale."
value: { kind: index, code: IUS, n: <value> }
language: { canonical: fr, renderings: { fr: "...", de: "...", it: "..." } }
source_refs:
  - { source_id: LSN-RPGA, locator: "art. X / Zone centrale", version: "<date>", retrieved_at: "<date>" }
provenance: sourced:document     # sourced:api | sourced:document | assumption | unknown
valid_as_of: "<date>"
verification: { method: document_check }
status: draft
```

## 8. The selector ("regulatory route")

A project declares `{commune: Lausanne, canton: VD, country: CH}`. The engine activates **only**
`Federal core + VD overlay + Lausanne overlay` from the shared corpus and scopes all retrieval to them
(no per-project corpus rebuild). See [`../strategy/knowledge-architecture.md`](../strategy/knowledge-architecture.md).

## 9. Trust / evidence contract (enforced at output)

- Every claim renders with its source (article + version + date) **or** a visible `assumption`/`unknown` tag.
- The system states confidence and **never asserts** a regulatory value it cannot source.
- Output is *preparation & evidence*, never an authority; the architect remains accountable.
  (See [`../strategy/challenge-and-brainstorm.md`](../strategy/challenge-and-brainstorm.md) §B8.)

## 10. Architecture placement

MVP1 is the first vertical slice of **Track A** over the **neutral engine + CH jurisdiction pack** (#22).
It exercises: ontology, NOMOS units, the selector, the two-RAG separation, and the trust contract — the
foundations every later MVP reuses.

## 11. Success criteria

- For a **real Lausanne parcel**, produce the constraints sheet + envelope in **< 30 s**, every API-sourced
  field linked to its source.
- The system **distinguishes** sourced facts from assumptions (no unsourced regulatory value).
- The envelope's `document`-sourced fields (indices/heights) cite the exact RPGA locator.
- An architect judges the brief **useful before drawing starts** (qualitative, partner-office validation).
- Output is structured enough to feed MVP2 (opposition/permit).

## 12. Build tasks → issues

- Engine + pack skeleton — #22
- Composable corpus + selector — #23 (depends on NOMOS #6)
- Seed 3-level corpus (Federal+VD+Lausanne) — #24 (depends on #3)
- Parcel → envelope — #27
- Phase matrix / sources foundation — #1, #3, #8
- Project-knowledge regime (context vs RAG) — #25
- Trust ledger / contract — #32 (sharpens #9)

## 13. Risks & open questions

- **Commune envelope is PDF-only** (indices/heights/setbacks). Mitigation: bounded one-time Lausanne RPGA
  ingestion; structure per zone; refresh on change. *This is the main effort.*
- **Cantonal ArcGIS is token-gated** (precise alignment geometry). Mitigation: use OEREB classification + the
  published plan; defer precise geometry.
- **Some federal OEREB routes are mid-migration.** Mitigation: pin to the cantonal `rdppf.vd.ch` service;
  re-verify endpoints before shipping.
- **Project-knowledge regime** (#25): confirm small-project = context-first is economically right.

## Appendix — worked example (real, from the PoC)

`Place de la Palud, Lausanne` → parcel **10072**, **EGRID CH915772367853**, commune BFS 5586.
OEREB extract returns: **Zone centrale (15 LAT)**, **noise DS III**, **alignment "limite des constructions
(plan approuvé)"**, *not concerned* by polluted sites / water / forest; laws **LATC 700.11**, **LAT (fedlex)**.
Indices/heights for "Zone centrale" → from the Lausanne RPGA layer (ingested, step 5).
