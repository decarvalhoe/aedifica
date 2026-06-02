# MVP Roadmap

This is the product/MVP sequence. The software-development execution plan, release gates and issue-ready epics
are maintained in [`planning/software-roadmap.md`](planning/software-roadmap.md) and
[`planning/epics-and-backlog.md`](planning/epics-and-backlog.md).

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
2. R1A Agent-To-Software Demo: agent CLI -> API/adapter -> model/drawing intent -> dry-run diff -> approval/ledger.
3. R1B NOMOS Archi Intake: parcel -> sourced constraints + buildable envelope inside a project workspace.
4. MVP2 Permit & Opposition: opposition radar, permit completeness, phase `33` compliance gates.
5. MVP3 Fees, Cost & Tender: SIA 102 fees, eCCC/NPK/CFC bridge, offer comparison.
6. MVP4 Project Memory & Coordination: site, decisions, handover, operation memory.

The regulatory/project-intelligence wedge comes first because it is evidence-backed and useful before BIM
maturity. It must not collapse the product into a permit/report tool. Auto-BIM, model intelligence and
controlled drawing assistance remain a native product track behind the same universal API/MCP.

The owner-confirmed adjustment is that the first spectacular proof now ships as `R1A`, before workspace
productization. This does not make Aedifica Archicad-only; it proves the top-down action layer while the
bottom-up regulatory spine remains intact.

## R1A: Agent-To-Architecture-Software Demo

Goal: prove that an agent CLI can assist an architect through a multi-software action lifecycle.

Inputs:

- Project context and ledger.
- Archicad-shaped selected-element fixture, then live Archicad JSON when available.
- Structured drawing/model intent.
- Adapter capability matrix.

Outputs:

- Adapter health and capability report.
- Missing metadata audit.
- Generated property/annotation action items.
- Before/after dry-run diff.
- Approval boundary and ledger evidence.

Success criteria:

- The demo is understandable to a skeptical architect without reading code.
- The fixture path is clearly marked as fixture mode.
- The same lifecycle can be reused by live Archicad, IFC, Speckle, Revit, Rhino, SketchUp, AutoCAD/BricsCAD and Vectorworks adapters.
- No mutation is possible without dry-run and approval.

Spec: [`specs/mvp1a-agent-to-architecture-software-demo.md`](specs/mvp1a-agent-to-architecture-software-demo.md).

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

Spec: [`specs/mvp4-direction-travaux-agentique.md`](specs/mvp4-direction-travaux-agentique.md).

## Native Track: Multi-Software Drawing / Model Intelligence

Goal: inspect a BIM/CAD/drawing/model state, detect missing or inconsistent project information, generate structured drawing/model intents, propose corrections, apply approved updates through the available adapter, and export deliverables.

Capabilities:

- Connect first through the most practical project adapter: IFC, Speckle, Archicad JSON/Tapir/Add-On, or another available model source.
- Extract spaces, elements, attributes, properties, and classifications.
- Translate approved design intent into safe drawing/model commands.
- Compare drawings/model snapshots and flag inconsistencies against project memory.
- Run missing metadata checks.
- Apply property updates after approval.
- Export IFC/PDF/DWG where supported.
- Generate a traceable report.

Note: Archicad is an excellent first real-world adapter because of the initial user context, but this track
should validate a general model-intelligence capability.

Spec: [`specs/later-model-intelligence.md`](specs/later-model-intelligence.md) and [`specs/later-voice-to-design.md`](specs/later-voice-to-design.md).

## Native Track: Voice-To-Design Workflow

Goal: let an architect describe controlled design actions orally and route them through safe structured commands.

Capabilities:

- Speech to text.
- Intent extraction.
- Structured drawing specification.
- Dry-run preview.
- Tool execution through MCP/API.
- Correction loop.

Spec: [`specs/later-voice-to-design.md`](specs/later-voice-to-design.md).

## Later Track: Tender and Quantity Workflows

The tender/quantity track is specified in
[`specs/later-tender-quantity-workflows.md`](specs/later-tender-quantity-workflows.md). Its current strategic
placement overlaps MVP3 because the cost/honoraires contracts are the next monetizable block; this later-track
spec preserves the workflow boundaries while the MVP3 software slice is built.
