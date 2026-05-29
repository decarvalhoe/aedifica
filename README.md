# Aedifica

Aedifica is the codename for **ArchiOS Suisse**: an agentic architecture operating system for the Swiss architectural context.

The long-term objective is to support the full architectural process, from initial constraints and project knowledge to design decisions, BIM, technical drawings, deliverables, building permits, tendering, execution, handover, and construction management.

## Working Vision

Aedifica treats architecture as a constraint-led, evidence-based workflow:

- Bottom-up: collect authoritative sources, project documents, regulations, constraints, decisions, and evidence.
- Canonical-first: transform those sources into traceable rules, requirements, exceptions, and design obligations.
- Top-down: let agents coordinate architectural workflows and, when useful, act on software through a common API/MCP layer.
- Human-controlled: agents propose, verify, log, and request approval before critical actions.

The product should behave like a project-aware architectural operating system, not like a generic chatbot or a drawing automation layer. It should know the project, the Swiss regulatory context, the current model state, the relevant SIA phase, the decisions already made, and the deliverable expected next.

## Core Thesis

Most small and mid-sized architecture offices already draw digitally, but much of the BIM value is lost because metadata, classifications, properties, exports, checks, and documentation are too manual.

Aedifica explores whether agentic assistance can make the whole architectural process more coherent: constraints, conception, BIM, compliance, documentation, coordination, execution, and construction management.

Software automation is one capability of the system, not the product itself. The product is the end-to-end assistant for the architect.

One strong validation track is **Swiss Auto-BIM for small and mid-sized offices**:

- Read project and regulatory context.
- Inspect the BIM/model state.
- Complete missing metadata and classifications.
- Prepare IFC/PDF/DWG deliverables.
- Validate through IFC/IDS/openBIM checks where possible.
- Produce a traceable report with sources and human approvals.

## Initial Scope

- Swiss architectural project lifecycle based on SIA phases.
- Swiss federal, cantonal, communal, parcel, program, and office-specific constraints.
- Tool-agnostic core, with adapters for Archicad, Revit, Rhino/Grasshopper, SketchUp, AutoCAD/BricsCAD, IFC, Speckle, and future office systems.
- NOMOS-style project memory and canonical constraint matrix.
- Universal architecture API/MCP for agentic workflows.
- End-to-end assistance: intake, constraints, design reasoning, BIM enrichment, model checks, exports, permit dossiers, tendering, execution, handover, and construction management.

## Repository Map

- `docs/vision.md`: full product framing.
- `docs/product/holistic-assistance.md`: end-to-end architect assistance model.
- `docs/research/swiss-architecture-process.md`: Swiss architecture lifecycle and phase matrix.
- `docs/research/phase-agentic-matrix.md`: detailed phase-by-phase intervention matrix.
- `docs/architecture/agentic-archios.md`: target system architecture.
- `docs/architecture/universal-mcp-api.md`: first common API/MCP surface.
- `docs/nomos/nomos-archi.md`: NOMOS adaptation for architecture.
- `docs/mvp-roadmap.md`: staged MVP plan.
- `docs/backlog/initial-issues.md`: initial issue list mirrored into GitHub Issues.
- `docs/research/sources.md`: initial source references.

## Current Status

Concept and research foundation. No production implementation yet.
