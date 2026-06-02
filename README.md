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

**Scope guardrail:** generated design surfaces and the current no-BIM regulatory wedge do not define the product boundary. Aedifica remains a full architectural assistant with a native multi-software API/MCP layer for model, drawing, BIM/CAD, document and construction workflows. See [`docs/product/scope-realignment.md`](docs/product/scope-realignment.md).

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
- Tool-agnostic core, with adapters for Archicad, Revit, Rhino/Grasshopper, SketchUp, AutoCAD/BricsCAD, Vectorworks, IFC, Speckle, and future office systems.
- NOMOS-style project memory and canonical constraint matrix.
- Universal architecture API/MCP for agentic workflows.
- End-to-end assistance: intake, constraints, design reasoning, BIM enrichment, model checks, exports, permit dossiers, tendering, execution, handover, and construction management.

## Repository Map

- **[`docs/overview.md`](docs/overview.md): up-to-date global plan — start here.**
- `docs/vision.md`: full product framing.
- `docs/product/holistic-assistance.md`: end-to-end architect assistance model.
- `docs/product/scope-realignment.md`: guardrail reaffirming the full product scope and multi-software drawing/model API.
- `docs/design-system/`: AEDIFICA Datum visual system tokens, assets and manifest from the validated Claude Design pack.
- `docs/strategy/`: strategy deep-dive — challenge & brainstorm, architect reality, Swiss regulatory stack, knowledge architecture, decisions, Lausanne PoC.
- `docs/research/`: Swiss architecture lifecycle, phase-agentic matrix, sources.
- `docs/research/bim-adapter-capability-map.md`: adapter capability map for Archicad, IFC, Speckle, Revit, Rhino, SketchUp, AutoCAD/BricsCAD, Vectorworks.
- `docs/research/swiss-competitions-and-study-mandates.md`: SIA 142/143 workflow research.
- `docs/research/swiss-construction-management-tools.md`: Swiss bauadministration/construction-management tool landscape.
- `docs/research/competitive-positioning.md`: integrate-vs-compete positioning map.
- `docs/product/business-model-and-pricing.md`: pricing hypothesis tied to MVP sequence.
- `docs/architecture/multilingual-regulatory-graph.md`: FR/DE/IT canonical regulatory graph contract.
- `docs/research/swiss-phase-lifecycle-matrix.md`: validated Swiss/SIA phase lifecycle matrix with
  small/medium/large project variants.
- `docs/research/pilot-source-registry.md`: prioritized CH/VD/Lausanne source registry compatible with NOMOS.
- `docs/architecture/`: target system architecture + first universal API/MCP surface.
- `docs/architecture/adr-0001-neutral-engine-and-jurisdiction-packs.md`: accepted ADR for the neutral engine + jurisdiction-pack split.
- `docs/architecture/trust-contract-and-ledger.md`: claim provenance, decision ledger, and professional-responsibility contract.
- `docs/architecture/adapter-evidence-record.md`: evidence shape for adapter dry-runs, approvals and future execution verification.
- `docs/architecture/jurisdiction-pack-contract.md`: versioned regulatory-pack contract + CI validation rules.
- `docs/architecture/project-knowledge-regime.md`: context-first vs hybrid index vs project RAG thresholds.
- `docs/architecture/project-memory-contract.md`: cross-phase project memory and provenance-backed query contract.
- `docs/architecture/local-model-bridge-prototype.md`: first local model bridge dry-run contract.
- `docs/architecture/archicad-json-live-setup.md`: live Archicad JSON setup and failure modes for R4.
- `docs/cost/`: SIA 102 fee/profitability and eCCC/NPK/CFC bridge contracts.
- `docs/permit/vd-camac-permit-completeness.md`: Vaud ACTIS-CAMAC permit dossier completeness contract.
- `docs/compliance/phase33-compliance-gates.md`: phase-33 compliance gates with binding-vs-contractual typing.
- `docs/nomos/nomos-archi.md`: NOMOS adaptation for architecture.
- `docs/nomos/nomos-archi-schema-v0.md`: initial canonical-unit schema for sources, rules, constraints, decisions, evidence, checks, and actions.
- `docs/nomos/phase-aware-constraint-matrix.md`: phase-aware matrix contract connecting constraints to SIA-phase actions.
- `docs/specs/mvp1-parcel-constraints-intake.md`: implementation-ready MVP1 spec.
- `docs/specs/mvp1a-agent-to-architecture-software-demo.md`: early agent CLI -> API -> architecture-software demo spec.
- `docs/specs/mvp2-permit-dossier-assistant.md`: implementation-ready permit dossier assistant spec.
- `docs/specs/later-model-intelligence.md`: Auto-BIM/model-intelligence track spec.
- `docs/specs/later-tender-quantity-workflows.md`: tender and quantity track spec.
- `docs/specs/mvp4-direction-travaux-agentique.md`: construction-management track spec.
- `docs/specs/later-voice-to-design.md`: voice-to-design track spec.
- `docs/mvp-roadmap.md`: staged MVP plan.
- **`docs/planning/`: software-development plan, release roadmap, epics/backlog, and delivery checklists.**
- `docs/validation/partner-agent-demo-protocol.md`: protocol for testing the R1A demo with the partner architect.
- `docs/review/foundations-audit.md`: living corrections tracker.
- `docs/pitch/aedifica-one-pager.html`: visual one-pager (FR).
- `docs/backlog/initial-issues.md`: first issue wave, now closed and superseded by the planning backlog.
- **[`pilot/`](pilot/): runnable MVP1/MVP2 pilot — parcel→constraints+envelope, opposition radar, regulatory-route selector (Lausanne + Pully).**

## Current Status

Concept + strategy + a **working pilot**. A strategy deep-dive ([`docs/strategy/`](docs/strategy/)) reframed the
product around **registry-anchored regulatory/project intelligence** (neutral engine + Swiss jurisdiction packs),
and a runnable pilot ([`pilot/`](pilot/)) demonstrates **MVP1** (parcel -> sourced constraints + buildable envelope)
and an **MVP2 opposition-risk radar** on real Vaud parcels (Lausanne + Pully) via free public Swiss APIs.

The roadmap is now rebaselined around **R1A Agent-To-Software Demo**: before productizing the workspace, Aedifica
must show the spectacular loop `agent CLI -> API/adapter -> model/drawing intent -> dry-run diff -> approval
boundary -> ledger`. The offline pilot already includes an Archicad-shaped bridge fixture, selected-element
inspection, missing metadata audit, generated design-intent items and before/after diff output.

See **[`docs/overview.md`](docs/overview.md)** for the up-to-date global plan. The pilot now has an offline
CI path, a versioned jurisdiction-pack contract, a validated Swiss phase matrix, a prioritized source registry,
workspace/memory/ledger contracts, and the first agent-to-software demo contract. The first GitHub issue waves
are closed or being re-opened against the R1A/R1B sequence. The project is still not production-ready: it needs
a live Archicad JSON bridge, stable package/API boundaries, persistence, UI, and partner-office validation
against real material.
