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

The recommended sequence is:

1. NOMOS Archi Intake.
2. Auto-BIM / Model Intelligence.
3. Permit Dossier Assistant.
4. Direction Travaux Agentique.

Tendering and voice-to-design remain important, but they should follow the first validated project memory and model-intelligence loop.

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

## MVP 2: Auto-BIM / Model Intelligence

Goal: inspect a BIM/model state, detect missing or inconsistent project information, propose corrections, apply approved updates through the available adapter, and export deliverables.

Initial capabilities:

- Connect first through the most practical project adapter: IFC, Speckle, Archicad JSON/Tapir/Add-On, or another available model source.
- Extract spaces, elements, attributes, properties, and classifications.
- Run missing metadata checks.
- Apply property updates after approval.
- Export IFC/PDF/DWG where supported.
- Generate a traceable report.

Success criteria:

- Saves measurable time on real model cleanup.
- Produces better IFC/property completeness than manual baseline.
- Does not break the model.
- Keeps a clear before/after audit trail.

Note: Archicad is an excellent first real-world adapter because of the initial user context, but this MVP should validate a general model-intelligence capability.

## MVP 3: Permit Dossier Assistant

Goal: prepare and audit permit dossier completeness for a selected Swiss commune/canton.

Capabilities:

- Commune/canton checklist.
- Required document matrix.
- Missing document detection.
- Regulation citation support.
- Draft notices and justification text.

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

## Later Track: Tender and Quantity Workflows

Goal: support calls for tender from BIM/model context.

Capabilities:

- Extract quantities.
- Map quantities to CFC/eCCC or office structure.
- Draft tender descriptions.
- Compare offers.
- Track assumptions and exclusions.

## Later Track: Voice-to-Design Workflow

Goal: let an architect describe controlled design actions orally and route them through safe structured commands.

Capabilities:

- Speech to text.
- Intent extraction.
- Structured drawing specification.
- Dry-run preview.
- Tool execution through MCP/API.
- Correction loop.
