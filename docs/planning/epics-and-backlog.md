# Aedifica Epics And Development Backlog

Status: issue-ready backlog baseline after the first 38 GitHub issues were closed.

## Backlog Model

Use these fields when opening GitHub issues:

- `Epic`: `AED-E##`
- `Priority`: `P0` critical path, `P1` next release, `P2` important but not blocking, `P3` later polish
- `Milestone`: `R1` to `R6`
- `Labels`: `product`, `backend`, `frontend`, `data`, `adapter`, `validation`, `docs`, `research`, `security`
- `Done`: testable acceptance criteria, not just text written

## Epic Summary

| Epic | Milestone | Priority | Outcome |
|---|---|---:|---|
| AED-E01 Project Workspace | R1 | P0 | Projects become explicit folders/manifests with reports and memory records. |
| AED-E02 Engine Packaging | R1 | P0 | Pilot logic becomes reusable modules with stable contracts. |
| AED-E03 Regulatory Route And Packs | R1 | P0 | `CH + canton + commune` route is selected and validated per project. |
| AED-E04 Sourced Parcel Brief | R1 | P0 | Architect gets a sourced brief and envelope from parcel input. |
| AED-E05 Trust Rendering And Reports | R1 | P0 | Claims render as sourced/computed/assumption/unknown/conflict. |
| AED-E06 Permit Readiness | R2 | P1 | Dossier evidence and phase-33 blockers become actionable. |
| AED-E07 Opposition Risk | R2 | P1 | Indicative opposition signals are explicit, sourced and reviewable. |
| AED-E08 Project Memory And Ledger | R3 | P0 | Decisions, approvals, evidence and handoffs persist across phases. |
| AED-E09 Model Intelligence Bridge | R4 | P1 | Archicad/IFC model inspection and dry-run updates work safely. |
| AED-E10 Cost And Tender | R5 | P1 | Fee, cost taxonomy and tender assumptions are tracked. |
| AED-E11 Site And Handover | R6 | P2 | PV, tasks, defects and handover evidence enter memory. |
| AED-E12 Product UI And Demo Readiness | R1-R6 | P1 | The user-facing experience stays coherent and demoable. |
| AED-E13 Quality, CI And Security | R1-R6 | P0 | Contract tests, source safety and privacy gates protect releases. |

## AED-E01 — Project Workspace

Goal: introduce the first durable project object.

Issue-ready tasks:

- **AED-001 Create project folder contract**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `data`, `validation`  
  Done: a fixture project contains `project.json`, `sources/`, `evidence/`, `reports/`, `memory/` and passes a
  validator.

- **AED-002 Add project manifest validator**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `validation`  
  Done: invalid project ID, missing jurisdiction, missing phase or missing trust settings fail CI.

- **AED-003 Persist generated report metadata**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `data`  
  Done: every generated brief stores report ID, source refs, generated timestamp and trust footer.

- **AED-004 Add sample Vaud/Lausanne project fixture**  
  Priority: P0 · Milestone: R1 · Labels: `data`, `validation`  
  Done: fixture can run through parcel brief generation without network.

## AED-E02 — Engine Packaging

Goal: move from scripts to reusable modules without overengineering.

Issue-ready tasks:

- **AED-005 Extract OEREB parsing into domain module**  
  Priority: P0 · Milestone: R1 · Labels: `backend`  
  Done: existing CLI still works; parser unit tests cover the current inline fixture.

- **AED-006 Extract envelope calculation service**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `validation`  
  Done: Lausanne and Pully calculations remain unchanged in selfcheck.

- **AED-007 Define domain error types**  
  Priority: P1 · Milestone: R1 · Labels: `backend`  
  Done: network failures, unsupported commune, missing pack and ambiguous zone produce structured errors.

- **AED-008 Keep CLIs as thin wrappers**  
  Priority: P1 · Milestone: R1 · Labels: `backend`  
  Done: `mvp1_demo.py`, `fiche.py`, `opposition_radar.py` call modules instead of duplicating logic.

## AED-E03 — Regulatory Route And Packs

Goal: make the selector a production contract.

Issue-ready tasks:

- **AED-009 Add regulatory route object**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `data`  
  Done: a project has active layers and inactive layers with timestamps and source versions.

- **AED-010 Add pack freshness warnings**  
  Priority: P1 · Milestone: R1 · Labels: `backend`, `validation`  
  Done: expired `review_due` does not crash, but report renders a visible warning.

- **AED-011 Add commune support policy**  
  Priority: P1 · Milestone: R1 · Labels: `docs`, `product`  
  Done: docs define supported, seed, on-demand and unsupported commune states.

- **AED-012 Add next commune ingestion checklist**  
  Priority: P2 · Milestone: R2 · Labels: `data`, `docs`  
  Done: a new commune can be added by following a repeatable checklist.

## AED-E04 — Sourced Parcel Brief

Goal: make MVP1 usable from a project context.

Issue-ready tasks:

- **AED-013 Add parcel intake API/function**  
  Priority: P0 · Milestone: R1 · Labels: `backend`  
  Done: accepts address, EGRID or parcel fixture and returns normalized parcel context.

- **AED-014 Generate constraint brief object**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `data`  
  Done: output contains source registry, constraints, envelope, risks, unknowns and project summary.

- **AED-015 Add brief renderer**  
  Priority: P0 · Milestone: R1 · Labels: `frontend`, `backend`  
  Done: HTML report uses trust states and can be saved in `reports/`.

- **AED-016 Add unsupported-data handling**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `validation`  
  Done: missing indices/heights render as `unknown` with next action, never as zero.

## AED-E05 — Trust Rendering And Reports

Goal: enforce the trust contract where users see outputs.

Issue-ready tasks:

- **AED-017 Add claim envelope schema**  
  Priority: P0 · Milestone: R1 · Labels: `data`, `validation`  
  Done: every claim has state, confidence, source refs or required human check.

- **AED-018 Add report renderer refusal tests**  
  Priority: P0 · Milestone: R1 · Labels: `backend`, `validation`  
  Done: a regulatory claim without `source_refs` cannot render as `sourced`.

- **AED-019 Add residual unknowns section**  
  Priority: P1 · Milestone: R1 · Labels: `frontend`, `product`  
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

- **AED-029 Write memory records from R1 reports**  
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
  Priority: P0 · Milestone: R1 · Labels: `product`, `frontend`, `architecture`  
  Done: decision doc records local web app vs desktop-local app and storage choice.

- **AED-045 Create project intake screen**  
  Priority: P1 · Milestone: R1 · Labels: `frontend`  
  Done: user can enter project name, commune/canton and parcel reference.

- **AED-046 Create claim review screen**  
  Priority: P1 · Milestone: R1 · Labels: `frontend`, `product`  
  Done: claims are grouped by state with source links and unknowns.

- **AED-047 Create demo script and fixture pack**  
  Priority: P1 · Milestone: R1 · Labels: `docs`, `product`  
  Done: partner-office demo can be run without live endpoint failure.

## AED-E13 — Quality, CI And Security

Goal: make correctness enforceable.

Issue-ready tasks:

- **AED-048 Add contract-test directory**  
  Priority: P0 · Milestone: R1 · Labels: `validation`, `backend`  
  Done: schema/fixture tests live outside ad hoc CLIs and run in CI.

- **AED-049 Add network/offline test split**  
  Priority: P1 · Milestone: R1 · Labels: `validation`, `backend`  
  Done: CI stays offline; live endpoint checks are explicit and non-blocking.

- **AED-050 Add project-data privacy checklist**  
  Priority: P1 · Milestone: R1 · Labels: `security`, `docs`  
  Done: project documents, model files and client data handling are documented before app work.

- **AED-051 Add release checklist to CI/docs**  
  Priority: P1 · Milestone: R1 · Labels: `validation`, `docs`  
  Done: release cannot be called ready without validation, demo fixture, report export and known-limit notes.

## Suggested Milestones

Create these milestones when opening the next issue wave:

| Milestone | Description |
|---|---|
| `R1 Project Workspace` | First usable app slice for parcel brief and report. |
| `R2 Permit And Opposition` | Dossier review and opposition-risk workflow. |
| `R3 Memory And Ledger` | Persistent decisions, approvals, evidence and handoffs. |
| `R4 Model Bridge` | Partner-office Archicad/IFC model intelligence slice. |
| `R5 Cost And Tender` | Fee, cost taxonomy and tender assumption workflow. |
| `R6 Site And Handover` | Construction-management and handover memory workflow. |

## Critical Path

```text
AED-E01 + AED-E02 + AED-E03
  -> AED-E04
  -> AED-E05
  -> AED-E08
  -> AED-E06 / AED-E07 / AED-E09
```

Do not start real model mutation, permit "ready" status, or tender export before the trust renderer and ledger
primitives exist.
