# Aedifica Software Development Plan

Status: planning baseline after reading the full project documentation and `README.md` on 2026-05-31.

## Executive Read

Aedifica already has a strong product thesis and a runnable Python pilot, but it is not yet a software product.
The current repository proves that public Swiss registries, Vaud RDPPF/OEREB data, commune packs, permit
checklists, phase-aware constraints, project memory fixtures and cost fixtures can be validated offline. The
next step is to productize that proof into a small, reliable application that an architect can use on a real
pilot project.

The development plan should not start with a broad "AI platform", and it should not shrink Aedifica to the
current regulatory/report surfaces. It should turn the working pilot into a project workspace with four hard guarantees:

- sourced claims stay sourced;
- assumptions stay visible;
- mutating actions require dry-run and approval;
- every workflow writes a project memory or ledger record.

## Current State

Already functional:

- Python pilot for parcel intake, RDPPF/OEREB parsing, envelope calculation, opposition radar and printable A4
  fiches.
- Versioned jurisdiction-pack contract for CH/VD/commune overlays.
- Phase-aware constraint matrix and Swiss lifecycle matrix.
- Permit completeness, phase-33 compliance gates, project memory fixture, cost/taxonomy fixtures and model
  bridge dry-run prototype.
- CI smoke suite on Python 3.11 and 3.12.
- Strategic decisions: neutral engine + jurisdiction packs; Vaud/Lausanne first; context-first project memory;
  Archicad as partner-office thread, not product identity.

Missing before this can be used as software:

- no application shell or project workspace;
- no stable package/API boundary around the pilot logic;
- no persistent project object, source manifest, evidence store or ledger implementation;
- no UI for an architect to enter a parcel, review claims, mark assumptions or approve actions;
- no production data-store decision;
- no real adapter implementation for Archicad/IFC/Speckle;
- no post-closure GitHub backlog for the next development wave.

## Product Target

The first product target is **Aedifica Workspace for Vaud/Lausanne pilot projects**:

```text
create project
  -> resolve parcel / EGRID
  -> select regulatory route
  -> generate sourced constraint brief
  -> compute envelope where commune pack allows it
  -> flag unknowns, opposition risks and permit blockers
  -> persist evidence and decisions
  -> export a reviewed report
```

This target keeps the no-BIM wedge first while preserving the native drawing/model API boundary for the partner-office Archicad bridge and later adapters.

## Product Principles

- **Registry anchored:** official sources and project documents feed the system; prompts do not become truth.
- **Pack selected:** every project activates one regulatory route, such as `CH + VD + Lausanne`.
- **Phase aware:** a claim is useful only when the system knows when it matters and what action it triggers.
- **Context-first by default:** small projects use files, manifest and ledger before a heavy RAG/database.
- **Tool neutral:** Archicad is the first partner bridge, not the core ontology.
- **Drawing/model assistance is first-class:** the product must keep a universal API for inspected, generated, checked and approved model/drawing actions across tools.
- **Human accountable:** the architect validates regulatory interpretations, assumptions, dossier readiness and
  model mutations.
- **Integrate, do not replace:** Messerli, SORBA, BBase, CRB, CAMAC, Archicad, Revit and construction clouds are
  rails or adapters, not first targets to displace.

## Proposed Technical Shape

Use the existing Python pilot as the domain core, then wrap it progressively.

| Layer | First implementation | Later evolution |
|---|---|---|
| Domain core | Python package extracted from `pilot/` | Stable engine modules with typed contracts. |
| Project workspace | Files + manifest + ledger JSON | SQLite/Postgres when repeated project queries justify it. |
| API | Thin local HTTP API around project and reports | FastAPI service with auth, jobs and storage. |
| UI | Minimal web workspace for project intake/review/export | Role-aware multi-project app. |
| Evidence store | Stored extracts, source refs, hashes, generated reports | Versioned object storage and indexed memory. |
| Adapters | Dry-run local bridge contracts | Archicad JSON, IFC/IfcOpenShell, Speckle, Revit/Rhino/SketchUp/AutoCAD bridges and document systems. |
| CI | Current validators and selfcheck | Contract tests, fixture regression tests, UI smoke tests. |

The first production code should remain boring: explicit files, clear schemas, small pure functions, and
validator-first changes. Do not introduce a vector database, queue, plugin marketplace or complex auth before a
real project requires it.

## Development Tracks

### Track A — Product Shell And Project Workspace

Goal: let an architect create/open one pilot project and see the state of sources, claims, unknowns and outputs.

Core capabilities:

- project manifest;
- project folder layout;
- source/evidence registry;
- generated report history;
- trust footer and claim-state rendering;
- export of a reviewed A4/brief.

### Track B — Regulatory Engine And Packs

Goal: turn the existing selector, pack and matrix logic into reusable engine modules.

Core capabilities:

- regulatory route selection;
- pack validation and review metadata;
- source freshness checks;
- phase-aware constraint rows;
- multilingual term renderings where available.

### Track C — Parcel Intake, Envelope And Risk

Goal: make the current MVP1/MVP2 parcel workflow usable from the workspace.

Core capabilities:

- address / EGRID / parcel intake;
- OEREB/RDPPF extraction;
- commune pack match;
- sourced envelope fields;
- opposition risk signals;
- unknowns list with required next action.

### Track D — Permit Readiness

Goal: turn the phase-33 checklists into a real dossier review workflow.

Core capabilities:

- evidence upload or reference;
- accepted evidence-key mapping;
- completeness report;
- compliance gate report;
- human status: draft, missing evidence, ready for review, architect approved.

### Track E — Project Memory And Ledger

Goal: persist decisions, evidence, approvals, generated reports and carryover obligations across phases.

Core capabilities:

- ledger entry schema;
- project memory records;
- queries such as changes since version, open blockers before permit, conditions carried to site;
- report hashes and source refs.

### Track F — Multi-Software Drawing And Model Intelligence Bridge

Goal: prove the partner-office Archicad thread while keeping the core adapter-neutral and ready for drawing/model assistance across software.

Core capabilities:

- adapter capability manifest;
- Archicad JSON connection check;
- structured design/drawing intent contract;
- selected-element and room/space property inspection;
- dry-run property update plan;
- approval and verification records.

### Track G — Fees, Cost And Tender

Goal: move from research fixtures to a first useful cost/tender assistant.

Core capabilities:

- SIA 102 hours/fee assumptions;
- absorbed special-prestations register;
- eCCC/NPK/CFC mapping rows;
- quantity source versioning;
- `.crbx`-style export/import contract proof.

### Track H — Site And Handover

Goal: convert site notes into memory-backed PVs, tasks, defects and handover evidence.

Core capabilities:

- note/photo/voice-note intake;
- PV generation;
- task and defect registers;
- permit/tender condition carryover;
- handover checklist and warranty register.

## First Release Definition

Release `R1` should be small enough to demo in one meeting:

- create a project for a Vaud/Lausanne parcel;
- fetch or load OEREB/RDPPF evidence;
- select `CH + VD + Lausanne`;
- render a sourced constraint brief and envelope;
- show assumptions/unknowns;
- persist a project memory record and ledger entry;
- export an A4 report;
- pass the existing CI plus new project-workspace tests.

`R1` does not need multi-user auth, payments, generic Swiss coverage, production Archicad mutation, full RAG, or
submission to CAMAC. It must, however, avoid decisions that would block the later universal architecture API.

## Engineering Rules

- Every new schema gets a fixture and a validator before UI work depends on it.
- Every generated regulatory claim must have `source_refs`, `claim_state`, `valid_as_of` and confidence.
- Every mutating adapter action starts as dry-run only.
- Keep public-source integrations replaceable: endpoints can move.
- Prefer small modules over large orchestration files.
- Keep docs and issue titles bilingual where useful, but canonical contracts can stay English.

## Immediate Product Questions To Resolve

1. Should the first app be desktop-local only, or a local web app that can later be hosted?
2. Should `R1` persist projects as files only, or introduce SQLite for local project state?
3. Which partner-office demo should be first after `R1`: permit readiness, Archicad metadata audit, or site PV?
4. Which commune should be ingested after Lausanne and Pully to prove repeatability?
