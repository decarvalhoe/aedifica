# Aedifica

Aedifica is the codename for **ArchiOS Suisse**: an agentic architecture operating system for the Swiss architectural context.

The long-term objective is to support the full architectural process, from initial constraints and project knowledge to design decisions, BIM, technical drawings, deliverables, building permits, tendering, execution, handover, and construction management.

> **Start here:** [`docs/overview.md`](docs/overview.md) — the up-to-date global plan (vision, approach, roadmap, and what already works).

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

- **[`docs/overview.md`](docs/overview.md): up-to-date global plan — start here.**
- `docs/vision.md`: full product framing.
- `docs/product/holistic-assistance.md`: end-to-end architect assistance model.
- `docs/strategy/`: strategy deep-dive — challenge & brainstorm, architect reality, Swiss regulatory stack, knowledge architecture, decisions, Lausanne PoC.
- `docs/research/`: Swiss architecture lifecycle, phase-agentic matrix, sources.
- `docs/architecture/`: target system architecture + first universal API/MCP surface.
- `docs/architecture/adr-0001-neutral-engine-and-jurisdiction-packs.md`: accepted ADR for the neutral engine + jurisdiction-pack split.
- `docs/architecture/trust-contract-and-ledger.md`: claim provenance, decision ledger, and professional-responsibility contract.
- `docs/architecture/jurisdiction-pack-contract.md`: versioned regulatory-pack contract + CI validation rules.
- `docs/permit/vd-camac-permit-completeness.md`: Vaud ACTIS-CAMAC permit dossier completeness contract.
- `docs/compliance/phase33-compliance-gates.md`: phase-33 compliance gates with binding-vs-contractual typing.
- `docs/nomos/nomos-archi.md`: NOMOS adaptation for architecture.
- `docs/nomos/nomos-archi-schema-v0.md`: initial canonical-unit schema for sources, rules, constraints, decisions, evidence, checks, and actions.
- `docs/nomos/phase-aware-constraint-matrix.md`: phase-aware matrix contract connecting constraints to SIA-phase actions.
- `docs/specs/mvp1-parcel-constraints-intake.md`: implementation-ready MVP1 spec.
- `docs/mvp-roadmap.md`: staged MVP plan.
- `docs/review/foundations-audit.md`: living corrections tracker.
- `docs/pitch/aedifica-one-pager.html`: visual one-pager (FR).
- `docs/backlog/initial-issues.md`: initial issue list mirrored into GitHub Issues.
- **[`pilot/`](pilot/): runnable MVP1/MVP2 pilot — parcel→constraints+envelope, opposition radar, regulatory-route selector (Lausanne + Pully).**

## Current Status

Concept + strategy + a **working pilot**. A strategy deep-dive ([`docs/strategy/`](docs/strategy/)) reframed the
product around **registry-anchored regulatory/project intelligence** (neutral engine + Swiss jurisdiction packs),
and a runnable pilot ([`pilot/`](pilot/)) demonstrates **MVP1** (parcel → sourced constraints + buildable envelope)
and an **MVP2 opposition-risk radar** on real Vaud parcels (Lausanne + Pully) via free public Swiss APIs.
See **[`docs/overview.md`](docs/overview.md)** for the up-to-date global plan. The pilot now has an offline
CI path and a versioned jurisdiction-pack contract, but it is still not production-ready (prototypes; re-verify sources).
