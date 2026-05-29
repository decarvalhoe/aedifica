# MVP Roadmap

## MVP 0: Research Foundation

Goal: turn the conversation into a structured project foundation.

Deliverables:

- Vision document.
- Swiss process matrix.
- NOMOS Archi model.
- Universal MCP/API sketch.
- Initial issue backlog.

## Recommended MVP Track

The revised sequence is:

1. MVP0 Foundation: neutral engine, NOMOS, trust contract, packs, source registry.
2. MVP1 NOMOS Archi Intake: parcel -> sourced constraints + buildable envelope.
3. MVP2 Permit & Opposition: opposition radar, permit completeness, phase `33` compliance gates.
4. MVP3 Fees, Cost & Tender: SIA 102 fees, eCCC/NPK/CFC bridge, offer comparison.
5. MVP4 Project Memory & Coordination: site, decisions, handover, operation memory.

Auto-BIM/Archicad remains a live hybrid demo track for the partner office, but it is not the product identity
and should not block the regulatory/project-intelligence wedge.

## MVP 1: NOMOS Archi Intake

Goal: ingest a Swiss architecture project and produce a traceable constraints brief.

Inputs:

- Parcel and commune.
- Client program.
- Regulation PDFs or URLs.
- Existing drawings or notes.
- Office standards.

Outputs:

- Source registry.
- Constraint matrix.
- Phase-specific risks.
- Unknowns and required human decisions.
- Project brief for agents.

Success criteria:

- The system can distinguish sourced facts from assumptions.
- The output is useful to an architect before drawing starts.
- Constraints are structured enough to drive later model checks.

## MVP 2: Permit & Opposition

Goal: prepare and audit permit dossier completeness for a selected Swiss commune/canton, and surface
opposition/recours risks early enough to change the project.

Initial capabilities:

- Opposition-risk radar from parcel, heritage/noise/neighbourhood/shadow signals.
- Commune/canton checklist.
- Required document matrix.
- Missing document detection.
- Phase `33` compliance gates with legal/contractual typing.
- Regulation citation support.
- Draft notes and justification text.

Success criteria:

- Detects missing required permit evidence before filing.
- Distinguishes legal/authority-triggered obligations from contractual BIM conventions.
- Produces a human-reviewable report with source IDs, dates, and unknowns.
- Does not claim to replace ACTIS-CAMAC, commune, canton, architect, or specialists.

Spec: [`specs/mvp2-permit-dossier-assistant.md`](specs/mvp2-permit-dossier-assistant.md).

## MVP 3: Fees, Cost & Tender

Goal: connect architect fees, cost structures, quantities, and tendering.

Capabilities:

- SIA 102 fee and profitability cockpit.
- eCCC/NPK/CFC bridge, including `.crbx` / IfA18 where useful.
- Quantity extraction or import from plans/model snapshots.
- Draft tender descriptions.
- Offer comparison.
- Assumption and exclusion tracking.

## MVP 4: Direction Travaux Agentique

Goal: support execution and construction management workflows in a Swiss office context.

Capabilities:

- Site report generation.
- Meeting minutes to tasks.
- Defect tracking.
- Model-linked issues.
- Decision log.
- Cost and schedule alerts.
- Handover dossier.

## Later Track: Auto-BIM / Model Intelligence

Goal: inspect a BIM/model state, detect missing or inconsistent project information, propose corrections, apply approved updates through the available adapter, and export deliverables.

Capabilities:

- Connect first through the most practical project adapter: IFC, Speckle, Archicad JSON/Tapir/Add-On, or another available model source.
- Extract spaces, elements, attributes, properties, and classifications.
- Run missing metadata checks.
- Apply property updates after approval.
- Export IFC/PDF/DWG where supported.
- Generate a traceable report.

Note: Archicad is an excellent first real-world adapter because of the initial user context, but this track
should validate a general model-intelligence capability.

## Later Track: Voice-to-Design Workflow

Goal: let an architect describe controlled design actions orally and route them through safe structured commands.

Capabilities:

- Speech to text.
- Intent extraction.
- Structured drawing specification.
- Dry-run preview.
- Tool execution through MCP/API.
- Correction loop.
