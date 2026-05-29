# Aedifica Vision

## One-Line Definition

Aedifica is an agentic architecture operating system for Swiss architecture offices.

It combines project knowledge, regulations, BIM metadata, architectural software automation, and construction workflows into one coherent system.

## Problem

Architecture projects are constrained from the beginning by many sources:

- Parcel and cadastral data.
- Federal, cantonal, and communal regulations.
- Zoning rules and local building codes.
- SIA standards and phase expectations.
- Client program and budget.
- Technical constraints from engineers and specialists.
- Office standards, templates, layers, favorites, and drawing habits.
- Decisions made across meetings, emails, sketches, and model versions.

In practice, these constraints are scattered across PDFs, web pages, emails, models, drawings, spreadsheets, and human memory. CAD/BIM tools hold geometry, but they rarely hold the full reasoning context of the project.

Small and mid-sized offices often draw in Archicad/Revit as if the software were digital paper. BIM metadata has high downstream value, but creating and maintaining it is tedious. As a result, BIM is often incomplete, inconsistent, or only done when a client or authority demands it.

## Product Hypothesis

If an agent can access a canonical project memory, understand Swiss constraints, inspect the BIM/CAD model, and act through safe tool adapters, then it can reduce high-friction architectural work:

- Collect and summarize project constraints.
- Generate project briefs and feasibility checks.
- Enrich BIM metadata automatically.
- Detect missing model information.
- Prepare IFC, PDF, DWG, and permit exports.
- Maintain a traceable record of design decisions.
- Support calls for tender, comparisons, site reports, defects, and handover.

## Product Shape

Aedifica should not start as a generic chatbot. It should be a structured project system with agentic interfaces.

The system needs:

- A project memory with authoritative sources and decisions.
- A canonical constraint matrix.
- A neutral building/project model.
- Tool adapters for Archicad, IFC, Speckle, and later Revit/Rhino/SketchUp.
- A universal architecture API/MCP.
- Agents specialized by project phase and domain.
- Verification gates before risky actions.
- Logs and evidence for every generated claim or model mutation.

## Strategic Positioning

The first wedge is not full automatic design. The first wedge is Auto-BIM for Swiss Archicad workflows:

- Read a model.
- Detect missing or inconsistent BIM information.
- Map requirements from the project/regulatory context.
- Propose corrections.
- Inject metadata through Archicad automation.
- Export IFC/PDF/DWG.
- Produce a traceable report.

From there, the system can expand into permits, tendering, and construction management.

## Long-Term Vision

Aedifica becomes an "ArchiOS" for the full project lifecycle:

1. Project intake and constraints.
2. Feasibility and competition.
3. Preliminary design.
4. Project development.
5. Permit dossier.
6. Tendering and procurement.
7. Execution drawings.
8. Construction management.
9. Handover and operation.

The agent should always know the project context, the relevant sources, the current model state, the decisions already made, and the next deliverables expected by the Swiss architectural process.

