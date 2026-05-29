# MVP Roadmap

## MVP 0: Research Foundation

Goal: turn the conversation into a structured project foundation.

Deliverables:

- Vision document.
- Swiss process matrix.
- NOMOS Archi model.
- Universal MCP/API sketch.
- Initial issue backlog.

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

## MVP 2: Archicad Auto-BIM

Goal: inspect an Archicad model, detect missing BIM metadata, propose corrections, apply approved updates, and export deliverables.

Initial capabilities:

- Connect to Archicad through JSON API, Tapir, or a custom Add-On.
- Extract spaces, elements, attributes, properties, and classifications.
- Run missing metadata checks.
- Apply property updates after approval.
- Export IFC/PDF/DWG where supported.
- Generate a traceable report.

Success criteria:

- Saves measurable time on real Archicad cleanup.
- Produces better IFC/property completeness than manual baseline.
- Does not break the model.

## MVP 3: Permit Dossier Assistant

Goal: prepare and audit permit dossier completeness for a selected Swiss commune/canton.

Capabilities:

- Commune/canton checklist.
- Required document matrix.
- Missing document detection.
- Regulation citation support.
- Draft notices and justification text.

## MVP 4: Tender and Quantity Workflows

Goal: support calls for tender from BIM/model context.

Capabilities:

- Extract quantities.
- Map quantities to CFC/eCCC or office structure.
- Draft tender descriptions.
- Compare offers.
- Track assumptions and exclusions.

## MVP 5: Construction Management Agent

Goal: support site and execution work.

Capabilities:

- Site report generation.
- Meeting minutes to tasks.
- Defect tracking.
- Model-linked issues.
- Decision log.
- Cost and schedule alerts.
- Handover dossier.

## MVP 6: Voice-to-Design Workflow

Goal: let an architect describe controlled design actions orally and route them through safe structured commands.

Capabilities:

- Speech to text.
- Intent extraction.
- Structured drawing specification.
- Dry-run preview.
- Tool execution through MCP/API.
- Correction loop.

