# Aedifica Epics And Development Backlog

Status: issue-ready backlog baseline after the first 38 GitHub issues were closed.

## Backlog Model

Use these fields when opening GitHub issues:

- `Epic`: `AED-E##`
- `Priority`: `P0` critical path, `P1` next release, `P2` important but not blocking, `P3` later polish
- `Milestone`: `R1A` to `R6`
- `Labels`: `product`, `backend`, `frontend`, `data`, `adapter`, `validation`, `docs`, `research`, `security`
- `Done`: testable acceptance criteria, not just text written

## Epic Summary

| Epic | Milestone | Priority | Outcome |
|---|---|---:|---|
| AED-E14 Product Scope Operating Doctrine | R1A | P0 | Scope cannot drift back to regulatory-only or surface-only product framing. |
| AED-E15 Spectacular Partner Demo | R1A | P0 | Skeptical architect sees the agent-to-software value in one meeting. |
| AED-E16 Agent CLI Orchestrator | R1A | P0 | One command runs project context, bridge inspection, dry-run diff and safety output. |
| AED-E17 Adapter-Neutral Action Contract | R1A | P0 | Drawing/model actions share one lifecycle across software. |
| AED-E18 Archicad JSON Live Bridge | R4 | P1 | Fixture bridge is replaced by live Archicad JSON calls when available. |
| AED-E19 Drawing / Item Generation Intent | R1A | P0 | Architect intent becomes structured property, annotation or drawing/model items. |
| AED-E20 Before/After Diff And Approval UX | R1A | P0 | User sees exactly what would change before approval. |
| AED-E21 Demo Ledger Evidence | R1A | P0 | Dry-runs and future executions leave auditable evidence. |
| AED-E22 Partner Model Validation | R4 | P1 | The first partner-office model validates the bridge against real work. |
| AED-E23 Later Adapter Expansion | R4+ | P2 | IFC, Speckle, Revit, Rhino, SketchUp, AutoCAD/BricsCAD and Vectorworks stay planned. |
| AED-E01 Project Workspace | R1B | P0 | Projects become explicit folders/manifests with reports and memory records. |
| AED-E02 Engine Packaging | R1B | P0 | Pilot logic becomes reusable modules with stable contracts. |
| AED-E03 Regulatory Route And Packs | R1B | P0 | `CH + canton + commune` route is selected and validated per project. |
| AED-E04 Sourced Parcel Brief | R1B | P0 | Architect gets a sourced brief and envelope from parcel input. |
| AED-E05 Trust Rendering And Reports | R1B | P0 | Claims render as sourced/computed/assumption/unknown/conflict. |
| AED-E06 Permit Readiness | R2 | P1 | Dossier evidence and phase-33 blockers become actionable. |
| AED-E07 Opposition Risk | R2 | P1 | Indicative opposition signals are explicit, sourced and reviewable. |
| AED-E08 Project Memory And Ledger | R3 | P0 | Decisions, approvals, evidence and handoffs persist across phases. |
| AED-E09 Model Intelligence Bridge | R4 | P1 | Archicad/IFC model inspection and dry-run updates work safely. |
| AED-E10 Cost And Tender | R5 | P1 | Fee, cost taxonomy and tender assumptions are tracked. |
| AED-E11 Site And Handover | R6 | P2 | PV, tasks, defects and handover evidence enter memory. |
| AED-E12 Product UI And Demo Readiness | R1A-R6 | P1 | The user-facing experience stays coherent and demoable. |
| AED-E13 Quality, CI And Security | R1A-R6 | P0 | Contract tests, source safety and privacy gates protect releases. |

## AED-E14 — Product Scope Operating Doctrine

Goal: make the owner-confirmed scope correction operational, not only rhetorical.

Issue-ready tasks:

- **AED-052 Record R1A scope decision**  
  Priority: P0 · Milestone: R1A · Labels: `product`, `docs`, `architecture`  
  Done: decision log states that agent-to-software proof moves before workspace productization while preserving full ArchiOS scope.

- **AED-053 Add R1A implementation spec**  
  Priority: P0 · Milestone: R1A · Labels: `product`, `docs`, `adapter`  
  Done: spec defines demo flow, inputs, outputs, live/fallback behavior, safety gates and acceptance criteria.

- **AED-054 Rebaseline roadmap documents**  
  Priority: P0 · Milestone: R1A · Labels: `product`, `docs`  
  Done: README, overview, MVP roadmap, software roadmap and development plan all show `R1A` before `R1B`.

## AED-E15 — Spectacular Partner Demo

Goal: make the first meeting demo convincing for a skeptical architect.

Issue-ready tasks:

- **AED-055 Write partner demo narrative**  
  Priority: P0 · Milestone: R1A · Labels: `product`, `docs`, `demo`  
  Done: demo script explains why the CLI agent is valuable without implying Archicad is the product.

- **AED-056 Add fixture-mode disclosure**  
  Priority: P0 · Milestone: R1A · Labels: `product`, `docs`, `security`  
  Done: CLI output and docs explicitly mark offline fixture mode when no live Archicad bridge is used.

- **AED-057 Add skeptical-architect success criteria**  
  Priority: P1 · Milestone: R1A · Labels: `product`, `validation`, `demo`  
  Done: partner validation protocol captures time saved, trust, clarity, and willingness to test on a real model.

## AED-E16 — Agent CLI Orchestrator

Goal: make one local command tell the whole R1A story.

Issue-ready tasks:

- **AED-058 Extend demo_run with model bridge summary**  
  Priority: P0 · Milestone: R1A · Labels: `backend`, `adapter`, `demo`  
  Done: `python pilot/demo_run.py` prints brief, permit, opposition and model bridge action summary.

- **AED-059 Add selfcheck coverage for R1A agent demo**  
  Priority: P0 · Milestone: R1A · Labels: `backend`, `validation`, `adapter`  
  Done: offline selfcheck validates design intent loading, generated dry-run actions and before/after diff output.

- **AED-060 Add dedicated CLI entry for R1A**  
  Priority: P1 · Milestone: R1A · Labels: `backend`, `adapter`, `demo`  
  Done: a dedicated command can run only the agent-to-software demo and emit JSON plus human-readable output.

## AED-E17 — Adapter-Neutral Action Contract

Goal: keep the demo generalizable to every future architecture-software adapter.

Issue-ready tasks:

- **AED-061 Add structured design intent fixture**  
  Priority: P0 · Milestone: R1A · Labels: `data`, `adapter`, `validation`  
  Done: fixture expresses architect intent as property updates and drawing annotations against an adapter-neutral item shape.

- **AED-062 Add dry-run design intent planner**  
  Priority: P0 · Milestone: R1A · Labels: `backend`, `adapter`, `security`  
  Done: model bridge converts design intent into supported action items without mutating the model.

- **AED-063 Block unsupported adapter actions**  
  Priority: P1 · Milestone: R1A · Labels: `backend`, `adapter`, `validation`  
  Done: unsupported intent item kinds are reported as unsupported and cannot be presented as executable.

## AED-E18 — Archicad JSON Live Bridge

Goal: replace the fixture transport with a real partner-office Archicad JSON transport.

Issue-ready tasks:

- **AED-064 Document live Archicad JSON setup**  
  Priority: P1 · Milestone: R4 · Labels: `docs`, `adapter`, `archicad`  
  Done: setup doc names expected Archicad version, JSON endpoint, local port, test command and failure modes.

- **AED-065 Implement live product-info probe**  
  Priority: P1 · Milestone: R4 · Labels: `backend`, `adapter`, `archicad`  
  Done: bridge can query a running Archicad JSON endpoint and report version/capabilities without fixture data.

- **AED-066 Replace selected-element fixture with live call**  
  Priority: P1 · Milestone: R4 · Labels: `backend`, `adapter`, `archicad`  
  Done: selected elements can be read from live Archicad and normalized to the same shape as the fixture.

- **AED-067 Verify live dry-run against partner model**  
  Priority: P1 · Milestone: R4 · Labels: `adapter`, `validation`, `archicad`  
  Done: a partner model produces before/after diff evidence without mutation.

## AED-E19 — Drawing / Item Generation Intent

Goal: turn architect intent into concrete, reviewable work items.

Issue-ready tasks:

- **AED-068 Generate room metadata items**  
  Priority: P0 · Milestone: R1A · Labels: `backend`, `adapter`, `data`  
  Done: selected spaces missing `RoomUsage` or `SIA416SurfaceType` receive proposed update items.

- **AED-069 Generate drawing annotation items**  
  Priority: P1 · Milestone: R1A · Labels: `backend`, `adapter`, `product`  
  Done: demo can prepare at least one drawing annotation intent without claiming it has been placed live.

- **AED-070 Link generated items to project basis**  
  Priority: P1 · Milestone: R1A · Labels: `backend`, `liability`, `data`  
  Done: every generated item carries source/basis/confidence/human-check metadata.

## AED-E20 — Before/After Diff And Approval UX

Goal: make the safety boundary visible and credible.

Issue-ready tasks:

- **AED-071 Render before/after diff text**  
  Priority: P0 · Milestone: R1A · Labels: `backend`, `adapter`, `demo`  
  Done: dry-run output includes human-readable `Before/After` lines for property and annotation items.

- **AED-072 Add adapter approval state rendering**  
  Priority: P1 · Milestone: R1A · Labels: `frontend`, `security`, `adapter`  
  Done: reference UI shows blocked, dry-run approved and execution-approved states using Datum trust language.

- **AED-073 Add failure-mode copy**  
  Priority: P1 · Milestone: R1A · Labels: `product`, `docs`, `security`  
  Done: docs explain unavailable adapter, unsupported capability, missing approval and failed verification.

## AED-E21 — Demo Ledger Evidence

Goal: make every proposed model/drawing action auditable.

Issue-ready tasks:

- **AED-074 Connect dry-run plan to ledger approval fixture**  
  Priority: P0 · Milestone: R1A · Labels: `backend`, `liability`, `validation`  
  Done: demo ledger approval allows dry-run planning while still blocking unapproved execution.

- **AED-075 Add adapter evidence record shape**  
  Priority: P1 · Milestone: R3 · Labels: `data`, `liability`, `validation`  
  Done: before snapshot, dry-run plan, approval and verification can be stored as evidence refs.

## AED-E22 — Partner Model Validation

Goal: move from fixture confidence to partner-office proof.

Issue-ready tasks:

- **AED-076 Prepare partner validation protocol**  
  Priority: P1 · Milestone: R4 · Labels: `product`, `validation`, `demo`  
  Done: protocol captures model type, phase, selected elements, time saved, trust concerns and next desired workflow.

- **AED-077 Run first partner model audit**  
  Priority: P1 · Milestone: R4 · Labels: `adapter`, `validation`, `archicad`  
  Done: partner model produces a missing-metadata audit and diff evidence, with sensitive data handling noted.

## AED-E23 — Later Adapter Expansion

Goal: keep the multi-software API alive beyond the first Archicad proof.

Issue-ready tasks:

- **AED-078 Add IFC/IfcOpenShell inspection baseline**  
  Priority: P2 · Milestone: R4 · Labels: `adapter`, `backend`, `validation`  
  Done: exported IFC can be inspected for spaces, elements and property sets through a neutral adapter.

- **AED-079 Add Speckle snapshot baseline**  
  Priority: P2 · Milestone: R4 · Labels: `adapter`, `backend`, `validation`  
  Done: a Speckle model/version snapshot can normalize object metadata to the same action lifecycle.

- **AED-080 Keep Revit/Rhino/SketchUp/AutoCAD/Vectorworks adapter map current**  
  Priority: P3 · Milestone: R4 · Labels: `adapter`, `research`, `docs`  
  Done: capability matrix names read/write/export limits and recommended use for each adapter family.

## AED-E01 — Project Workspace

Goal: introduce the first durable project object.

Issue-ready tasks:

- **AED-001 Create project folder contract**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `data`, `validation`  
  Done: a fixture project contains `project.json`, `sources/`, `evidence/`, `reports/`, `memory/` and passes a
  validator.

- **AED-002 Add project manifest validator**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `validation`  
  Done: invalid project ID, missing jurisdiction, missing phase or missing trust settings fail CI.

- **AED-003 Persist generated report metadata**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `data`  
  Done: every generated brief stores report ID, source refs, generated timestamp and trust footer.

- **AED-004 Add sample Vaud/Lausanne project fixture**  
  Priority: P0 · Milestone: R1B · Labels: `data`, `validation`  
  Done: fixture can run through parcel brief generation without network.

## AED-E02 — Engine Packaging

Goal: move from scripts to reusable modules without overengineering.

Issue-ready tasks:

- **AED-005 Extract OEREB parsing into domain module**  
  Priority: P0 · Milestone: R1B · Labels: `backend`  
  Done: existing CLI still works; parser unit tests cover the current inline fixture.

- **AED-006 Extract envelope calculation service**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `validation`  
  Done: Lausanne and Pully calculations remain unchanged in selfcheck.

- **AED-007 Define domain error types**  
  Priority: P1 · Milestone: R1B · Labels: `backend`  
  Done: network failures, unsupported commune, missing pack and ambiguous zone produce structured errors.

- **AED-008 Keep CLIs as thin wrappers**  
  Priority: P1 · Milestone: R1B · Labels: `backend`  
  Done: `mvp1_demo.py`, `fiche.py`, `opposition_radar.py` call modules instead of duplicating logic.

## AED-E03 — Regulatory Route And Packs

Goal: make the selector a production contract.

Issue-ready tasks:

- **AED-009 Add regulatory route object**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `data`  
  Done: a project has active layers and inactive layers with timestamps and source versions.

- **AED-010 Add pack freshness warnings**  
  Priority: P1 · Milestone: R1B · Labels: `backend`, `validation`  
  Done: expired `review_due` does not crash, but report renders a visible warning.

- **AED-011 Add commune support policy**  
  Priority: P1 · Milestone: R1B · Labels: `docs`, `product`  
  Done: docs define supported, seed, on-demand and unsupported commune states.

- **AED-012 Add next commune ingestion checklist**  
  Priority: P2 · Milestone: R2 · Labels: `data`, `docs`  
  Done: a new commune can be added by following a repeatable checklist.

## AED-E04 — Sourced Parcel Brief

Goal: make MVP1 usable from a project context.

Issue-ready tasks:

- **AED-013 Add parcel intake API/function**  
  Priority: P0 · Milestone: R1B · Labels: `backend`  
  Done: accepts address, EGRID or parcel fixture and returns normalized parcel context.

- **AED-014 Generate constraint brief object**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `data`  
  Done: output contains source registry, constraints, envelope, risks, unknowns and project summary.

- **AED-015 Add brief renderer**  
  Priority: P0 · Milestone: R1B · Labels: `frontend`, `backend`  
  Done: HTML report uses trust states and can be saved in `reports/`.

- **AED-016 Add unsupported-data handling**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `validation`  
  Done: missing indices/heights render as `unknown` with next action, never as zero.

## AED-E05 — Trust Rendering And Reports

Goal: enforce the trust contract where users see outputs.

Issue-ready tasks:

- **AED-017 Add claim envelope schema**  
  Priority: P0 · Milestone: R1B · Labels: `data`, `validation`  
  Done: every claim has state, confidence, source refs or required human check.

- **AED-018 Add report renderer refusal tests**  
  Priority: P0 · Milestone: R1B · Labels: `backend`, `validation`  
  Done: a regulatory claim without `source_refs` cannot render as `sourced`.

- **AED-019 Add residual unknowns section**  
  Priority: P1 · Milestone: R1B · Labels: `frontend`, `product`  
  Done: every report lists unresolved assumptions and next human checks.

- **AED-020 Hash generated evidence and reports**  
  Priority: P1 · Milestone: R3 · Labels: `backend`, `security`  
  Done: generated reports carry stable hashes in memory records.

## AED-E06 — Permit Readiness

Goal: turn current validators into a dossier review workflow.

Issue-ready tasks:

- **AED-021 Define dossier evidence object**  
  Priority: P1 · Milestone: R2 · Labels: `data`, `validation`  
  Done: booleans are replaced by file-backed or external-reference evidence records.

- **AED-022 Implement evidence-key mapper**  
  Priority: P1 · Milestone: R2 · Labels: `backend`  
  Done: uploaded/referenced evidence maps to accepted checklist keys.

- **AED-023 Render permit completeness report**  
  Priority: P1 · Milestone: R2 · Labels: `frontend`, `backend`  
  Done: required, missing, conditional and out-of-scope items are grouped by actor/category.

- **AED-024 Add complete dossier fixture**  
  Priority: P1 · Milestone: R2 · Labels: `validation`  
  Done: one complete fixture has zero required blockers while conditional gates remain visible.

## AED-E07 — Opposition Risk

Goal: make risk signals useful without pretending to predict authority decisions.

Issue-ready tasks:

- **AED-025 Normalize opposition signal model**  
  Priority: P1 · Milestone: R2 · Labels: `backend`, `data`  
  Done: each signal has source, confidence, affected parcel/context and mitigation text.

- **AED-026 Add shadow/neighbor evidence placeholders**  
  Priority: P1 · Milestone: R2 · Labels: `backend`, `research`  
  Done: unavailable precise geometry renders as `unknown` or `assumption`, not fact.

- **AED-027 Render opposition-risk report**  
  Priority: P1 · Milestone: R2 · Labels: `frontend`, `product`  
  Done: report explains likely grounds, confidence and required checks.

## AED-E08 — Project Memory And Ledger

Goal: implement the core liability-protection layer.

Issue-ready tasks:

- **AED-028 Add ledger schema and validator**  
  Priority: P0 · Milestone: R3 · Labels: `data`, `validation`  
  Done: decisions, approvals, adapter dry-runs and report generations validate.

- **AED-029 Write memory records from R1B reports**  
  Priority: P0 · Milestone: R3 · Labels: `backend`  
  Done: sourced claims and unknowns survive after report generation.

- **AED-030 Add approval workflow primitive**  
  Priority: P0 · Milestone: R3 · Labels: `backend`, `security`  
  Done: approved_by, timestamp, basis and scope are required before mutating actions.

- **AED-031 Implement carryover queries**  
  Priority: P1 · Milestone: R3 · Labels: `backend`  
  Done: queries return open blockers before permit, conditions for tender/site and changes since report.

## AED-E09 — Model Intelligence Bridge

Goal: ship a safe partner-office bridge.

Issue-ready tasks:

- **AED-032 Implement Archicad JSON health check**  
  Priority: P1 · Milestone: R4 · Labels: `adapter`, `backend`  
  Done: app can detect running Archicad JSON bridge and report capabilities.

- **AED-033 Inspect selected spaces/elements**  
  Priority: P1 · Milestone: R4 · Labels: `adapter`, `backend`  
  Done: selected elements return IDs, classifications, properties and source model version.

- **AED-034 Generate missing metadata audit**  
  Priority: P1 · Milestone: R4 · Labels: `adapter`, `product`  
  Done: spaces missing required properties are listed with proposed fixes.

- **AED-035 Add dry-run property update**  
  Priority: P1 · Milestone: R4 · Labels: `adapter`, `security`  
  Done: update plan is created but blocked until approval exists in ledger.

## AED-E10 — Cost And Tender

Goal: make the economics track tangible.

Issue-ready tasks:

- **AED-036 Build fee assumptions object**  
  Priority: P1 · Milestone: R5 · Labels: `backend`, `data`  
  Done: hours, hourly rate, margin target and special prestations validate.

- **AED-037 Render profitability cockpit**  
  Priority: P1 · Milestone: R5 · Labels: `frontend`, `product`  
  Done: output shows estimated fee, absorbed tasks, risk and assumptions.

- **AED-038 Expand taxonomy mapping rows**  
  Priority: P1 · Milestone: R5 · Labels: `data`, `validation`  
  Done: multiple eCCC/NPK/CFC sample rows survive round-trip.

- **AED-039 Add tender assumptions log**  
  Priority: P2 · Milestone: R5 · Labels: `backend`, `product`  
  Done: assumptions/exclusions can be carried to offer comparison.

## AED-E11 — Site And Handover

Goal: prove downstream project-memory value.

Issue-ready tasks:

- **AED-040 Define site note input contract**  
  Priority: P2 · Milestone: R6 · Labels: `data`, `validation`  
  Done: note/photo/source metadata validates.

- **AED-041 Generate PV and task register**  
  Priority: P2 · Milestone: R6 · Labels: `backend`, `product`  
  Done: sample notes produce a structured PV and owner/deadline tasks.

- **AED-042 Add defect register fixture**  
  Priority: P2 · Milestone: R6 · Labels: `data`, `validation`  
  Done: defects have location, responsible actor, evidence and close-out state.

- **AED-043 Render handover checklist**  
  Priority: P2 · Milestone: R6 · Labels: `frontend`, `product`  
  Done: final report includes warranties, reserves, manuals, as-built and open defects.

## AED-E12 — Product UI And Demo Readiness

Goal: avoid a pile of backend contracts with no usable product surface.

Issue-ready tasks:

- **AED-044 Choose first app shell**  
  Priority: P0 · Milestone: R1B · Labels: `product`, `frontend`, `architecture`  
  Done: decision doc records local web app vs desktop-local app and storage choice.

- **AED-045 Create project intake screen**  
  Priority: P1 · Milestone: R1B · Labels: `frontend`  
  Done: user can enter project name, commune/canton and parcel reference.

- **AED-046 Create claim review screen**  
  Priority: P1 · Milestone: R1B · Labels: `frontend`, `product`  
  Done: claims are grouped by state with source links and unknowns.

- **AED-047 Create demo script and fixture pack**  
  Priority: P1 · Milestone: R1B · Labels: `docs`, `product`  
  Done: partner-office demo can be run without live endpoint failure.

## AED-E13 — Quality, CI And Security

Goal: make correctness enforceable.

Issue-ready tasks:

- **AED-048 Add contract-test directory**  
  Priority: P0 · Milestone: R1B · Labels: `validation`, `backend`  
  Done: schema/fixture tests live outside ad hoc CLIs and run in CI.

- **AED-049 Add network/offline test split**  
  Priority: P1 · Milestone: R1B · Labels: `validation`, `backend`  
  Done: CI stays offline; live endpoint checks are explicit and non-blocking.

- **AED-050 Add project-data privacy checklist**  
  Priority: P1 · Milestone: R1B · Labels: `security`, `docs`  
  Done: project documents, model files and client data handling are documented before app work.

- **AED-051 Add release checklist to CI/docs**  
  Priority: P1 · Milestone: R1B · Labels: `validation`, `docs`  
  Done: release cannot be called ready without validation, demo fixture, report export and known-limit notes.

## Suggested Milestones

Create these milestones when opening the next issue wave:

| Milestone | Description |
|---|---|
| `R1A Agent-To-Software Demo` | First spectacular agent CLI to architecture-software proof. |
| `R1B Project Workspace` | First usable app slice for parcel brief and report. |
| `R2 Permit And Opposition` | Dossier review and opposition-risk workflow. |
| `R3 Memory And Ledger` | Persistent decisions, approvals, evidence and handoffs. |
| `R4 Live Adapters` | Partner-office Archicad live bridge plus IFC/Speckle follow-ups. |
| `R5 Cost And Tender` | Fee, cost taxonomy and tender assumption workflow. |
| `R6 Site And Handover` | Construction-management and handover memory workflow. |

## Critical Path

```text
AED-E14 + AED-E15 + AED-E16 + AED-E17
  -> AED-E19 + AED-E20 + AED-E21
  -> AED-E18 / AED-E22

AED-E01 + AED-E02 + AED-E03
  -> AED-E04
  -> AED-E05
  -> AED-E08
  -> AED-E06 / AED-E07 / AED-E09
```

Do not start real model mutation, permit "ready" status, or tender export before the trust renderer and ledger
primitives exist.
