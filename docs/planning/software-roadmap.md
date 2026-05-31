# Aedifica Software Roadmap

Status: execution roadmap baseline, 2026-05-31.

## Roadmap Logic

The roadmap follows the existing strategic decision: lead with the no-BIM regulatory/project-intelligence wedge
because it is the fastest real proof, while preserving the full ArchiOS scope. The Archicad/model thread is
the first visible adapter of a broader multi-software drawing/model API, and the same trust, memory and adapter
contracts must apply everywhere.

Each release must produce a demoable vertical slice, not only documentation.

## Release Map

| Release | Horizon | Theme | Demo outcome |
|---|---:|---|---|
| R0 | Done | Research + pilot foundation | Python pilot, validators, one-pager, roadmap foundation. |
| R1 | 2-4 weeks | Project workspace + parcel brief | Create project -> parcel -> sourced brief -> report. |
| R2 | 4-8 weeks | Permit/opposition workflow | Missing dossier evidence + phase-33 gates + opposition risk. |
| R3 | 6-10 weeks | Project memory and ledger | Decisions, evidence, approvals and carryover queries. |
| R4 | 8-12 weeks | Multi-software drawing/model bridge | Archicad JSON inspection + dry-run metadata update; API contract remains adapter-neutral. |
| R5 | 12-16 weeks | Cost/tender assistant | SIA 102 fee assumptions + eCCC/NPK/CFC mapping report. |
| R6 | 16-24 weeks | Site/handover assistant | Site notes/photos -> PV/tasks/defects/handover memory. |

Horizons are planning ranges, not commitments. Each release depends on partner-office access, source endpoint
stability and validation against real project material.

## R0 — Foundation Already In Place

Delivered:

- Aedifica vision, strategy and architecture docs.
- Neutral engine + jurisdiction-pack ADR.
- MVP1/MVP2 pilot for Lausanne/Pully.
- Permit, compliance, memory, research, cost and model-bridge fixtures.
- CI validators and `pilot/selfcheck.py`.
- Repo hygiene and planning baseline.

Exit gate: passed.

## R1 — Project Workspace And Sourced Parcel Brief

Goal: transform the pilot into the first usable software slice.

Scope:

- project manifest and folder layout;
- regulatory route selection from project location;
- OEREB/RDPPF evidence capture;
- sourced claims and envelope report;
- first project memory records;
- exportable HTML/PDF-ready report;
- minimal UI or local API facade.

Exit criteria:

- a user can create one Vaud/Lausanne project without touching Python scripts directly;
- the output clearly separates sourced, computed, assumption and unknown claims;
- generated reports are saved with source/evidence refs;
- CI covers project workspace fixtures and existing pilot checks.

Key dependencies:

- existing `pilot/oereb.py`, `selector.py`, `fiche.py`, `trust.py`;
- jurisdiction pack contract;
- project memory contract.

## R2 — Permit And Opposition Workflow

Goal: make phase `33` actionable after the parcel brief.

Scope:

- dossier evidence model;
- Vaud/ACTIS-CAMAC checklist UI/report;
- phase-33 compliance gates;
- opposition-risk report with visible confidence;
- human review status.

Exit criteria:

- incomplete dossier reports known blockers;
- contractual BIM gates do not render as legal obligations;
- risk report is explicitly indicative and source-backed where possible;
- report can be exported for architect review.

Dependencies:

- R1 project context;
- permit checklist and compliance gates;
- source registry.

## R3 — Project Memory And Ledger

Goal: make Aedifica useful across phase handoffs, not only as a report generator.

Scope:

- persistent ledger entries;
- evidence refs with hashes where possible;
- approval records;
- cross-phase memory queries;
- carryover of permit conditions into tender/site.

Exit criteria:

- every generated report leaves a memory record;
- every human approval is stored;
- the system can answer "what changed", "what is still undecided" and "which source justified this";
- no mutating adapter can execute without an approval record.

Dependencies:

- trust contract;
- project knowledge regime;
- R1/R2 generated evidence.

## R4 — Multi-Software Drawing / Model Bridge

Goal: prove that the same engine can inspect and assist a real model/drawing workflow without becoming Archicad-only.

Scope:

- Archicad JSON connection check;
- adapter capability discovery;
- selected element/space/property extraction;
- structured drawing/model intent contract;
- missing metadata audit;
- dry-run update plan;
- human-approved execution only if the bridge is verified.

Exit criteria:

- connection and inspection work against a real partner model or controlled fixture;
- dry-run diff is human-readable;
- before/after evidence is captured;
- all operations are blocked when adapter capabilities are insufficient.

Dependencies:

- R3 ledger/approval;
- adapter capability matrix;
- access to Archicad JSON or a representative export.

## R5 — Fees, Cost And Tender

Goal: address the economic pain identified in the docs.

Scope:

- mandate hours/fee assumptions;
- absorbed special-prestations flags;
- eCCC/NPK/CFC mapping register;
- quantity source versioning;
- tender assumption/exclusion log.

Exit criteria:

- one project can produce a fee/profitability cockpit from explicit assumptions;
- one quantity register can round-trip through the bridge contract;
- unsupported paid SIA/CRB content is not hardcoded;
- outputs are suitable for human review or export to established Swiss tools later.

Dependencies:

- R3 project memory;
- cost fixtures and source boundary docs;
- partner-office examples.

## R6 — Site, Handover And Operation Memory

Goal: prove value in the highest-fee, highest-liability phases.

Scope:

- site notes/photos to PV;
- minutes to tasks;
- defect tracking;
- cost/schedule signal placeholders;
- handover checklist and warranty register;
- operation memory reactivation.

Exit criteria:

- a site report can be generated from structured notes and photos;
- tasks and defects carry owners, deadlines, source evidence and status;
- permit/tender assumptions can be carried into site and handover reports;
- final records can be queried later by phase and source.

Dependencies:

- R3 project memory;
- R5 cost/tender assumptions where applicable;
- real or synthetic site material.

## Cross-Cutting Workstreams

| Workstream | Runs through | Why |
|---|---|---|
| Source freshness and pack review | R1-R6 | Regulatory correctness decays without review metadata. |
| Validation and CI | R1-R6 | Every contract must remain testable offline. |
| Partner-office validation | R1-R6 | Product value depends on real workflow fit. |
| Universal architecture API | R1-R6 | Regulatory intelligence, drawing assistance, model checks and document exports must share one approved action lifecycle. |
| Security and privacy | R1-R6 | Project documents, client data and model files are sensitive. |
| Documentation and issue hygiene | R1-R6 | The project needs traceable work packages and done criteria. |

## Stop Conditions

Pause or re-scope a release if:

- the output cannot show source provenance for regulatory claims;
- the release requires paid SIA/CRB text to be hardcoded;
- the app cannot distinguish assumptions from facts;
- an adapter would mutate a model without dry-run and approval;
- the demo depends on BIM maturity before the no-BIM wedge is validated;
- the roadmap starts treating the no-BIM wedge or generated UI surfaces as the whole product scope.
