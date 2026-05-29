# Aedifica Vision

## One-Line Definition

Aedifica is **ArchiOS Suisse**: an agentic system that accompanies the full Swiss architectural process, from initial constraints to BIM, deliverables, permitting, tendering, execution, handover, and construction management.

It combines project knowledge, regulations, design reasoning, BIM metadata, architectural software automation, documentation, collaboration, and construction workflows into one coherent system.

## Product North Star

An architect should be able to open a project and ask:

```text
What are the constraints?
What are the risks?
What is missing in the BIM model?
What should be decided, checked, coordinated, generated, exported, or prepared next?
What has changed since the previous version?
Which source justifies this claim?
```

Aedifica should answer with sourced project context, then orchestrate the next workflow step. Sometimes that means drafting a brief, asking a question, identifying a risk, preparing a permit checklist, comparing options, updating BIM data, or acting through safe software adapters after approval.

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

Small and mid-sized offices often operate with fragmented knowledge: project constraints in PDFs, decisions in emails, model information in BIM/CAD software, tasks in meetings, costs in spreadsheets, and site reality in photos or notes. BIM metadata is one visible symptom: it has high downstream value, but creating and maintaining it is tedious, so it is often incomplete or postponed.

## Product Hypothesis

If an agent can access a canonical project memory, understand Swiss constraints, inspect the BIM/CAD model when needed, and coordinate the next project step, then it can reduce high-friction architectural work:

- Collect and summarize project constraints.
- Generate project briefs and feasibility checks.
- Enrich BIM metadata automatically.
- Detect missing model information.
- Prepare IFC, PDF, DWG, and permit exports.
- Maintain a traceable record of design decisions.
- Support calls for tender, comparisons, site reports, defects, and handover.
- Keep the architect oriented across the full SIA lifecycle.

## Product Shape

Aedifica should not start as a generic chatbot. It should be a structured project system with agentic interfaces.

The system needs:

- A project memory with authoritative sources and decisions.
- A canonical constraint matrix.
- A neutral building/project model.
- Tool adapters for Archicad, Revit, Rhino, SketchUp, AutoCAD/BricsCAD, IFC, Speckle, office documents, and future construction-management systems.
- A universal architecture API/MCP.
- Agents specialized by project phase and domain.
- Verification gates before risky actions.
- Logs and evidence for every generated claim or model mutation.

## Two-Movement Architecture

### Bottom-Up Canonical-First

The project starts from sources:

- Regulations.
- Standards.
- Parcel constraints.
- Client program.
- Model states.
- Meeting decisions.
- Office standards.
- Exceptions and approvals.

NOMOS Archi turns those sources into canonical units: rules, constraints, requirements, exceptions, decisions, checks, actions, and evidence. Every rule should know where it comes from, which project phase it applies to, and whether it can be verified manually, through a document check, or through a BIM/model query.

### Top-Down Workflow Orchestration

The system then lets agents orchestrate architectural workflows. Software automation is the execution layer when a task needs to touch a model, export, document, issue, or report:

```text
inspect_project
extract_spaces
create_wall
update_bim_properties
run_model_check
generate_variant
export_ifc
publish_pdf_set
compare_versions
create_site_report
```

Tool automation is not the product and not the source of truth. It is the action layer that executes validated intentions against Archicad, Revit, Rhino, IFC, Speckle, DWG, office documents, or construction-management workflows.

## Strategic Positioning

The first product promise is not "automate Archicad" or "draw by voice". The promise is:

> Assist an architect from beginning to end with project-aware, Swiss-aware, evidence-backed agents.

Auto-BIM remains a strong validation track because it is painful, measurable, and connected to downstream value:

- Read a model.
- Detect missing or inconsistent BIM information.
- Map requirements from the project/regulatory context.
- Propose corrections.
- Inject metadata through the appropriate adapter.
- Export IFC/PDF/DWG.
- Produce a traceable report.

But the architecture must stay generalizable: Archicad is one adapter, not the identity of the product.

## Swiss Differentiation

The product should be built for the Swiss context from the start:

- SIA 102/SIA 112 phase structure.
- Federal, cantonal, and communal source layers.
- Commune-specific zoning and building rules.
- Parcel constraints, servitudes, neighboring rights, and existing conditions.
- SIA 2051/openBIM expectations.
- Competition and study mandate workflows.
- Direction de travaux practices used by Swiss offices.

This is not just localization. The Swiss constraint stack is a core product advantage.

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
