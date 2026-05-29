# Agentic ArchiOS Architecture

## Target Architecture

```text
Sources and documents
  -> NOMOS project memory
  -> Canonical constraint matrix
  -> Project/BIM context graph
  -> Agentic workflow layer
  -> Verification and approval layer
  -> Tool action layer
  -> Archicad / IFC / Speckle / Revit / Rhino / DWG
```

## Core Layers

### 1. Project Source Layer

Stores the authoritative material for the project:

- Regulations.
- Standards.
- Client program.
- Parcels and site data.
- Existing drawings.
- Emails and meeting notes.
- Decisions and exceptions.
- Model exports and reports.

This layer must keep provenance, version, owner, and allowed use.

### 2. Canonical Constraint Layer

Transforms source material into atomic units:

- Rule.
- Term.
- Requirement.
- Constraint.
- Formula.
- Exception.
- Decision.
- Evidence.

Each unit should reference its source and carry verification metadata.

### 3. Project Context Graph

Represents the project in a tool-neutral way:

- Project.
- Site.
- Building.
- Level.
- Space.
- Element.
- Material.
- System.
- Document.
- Deliverable.
- Actor.
- Task.
- Decision.

This is not a replacement for Archicad or Revit. It is the shared context that lets agents reason across tools and documents.

### 4. Tool Adapter Layer

Each software gets an adapter:

- Archicad Add-On / JSON API / Tapir.
- Revit Add-In / Design Automation API.
- Rhino / Grasshopper / Rhino.Compute.
- SketchUp Ruby extension.
- AutoCAD / BricsCAD CLI and scripts.
- IFC via IfcOpenShell.
- Speckle connectors.

The adapter must expose safe actions through one common API shape.

### 5. Agentic Workflow Layer

Specialized agents work on bounded domains:

- Intake agent.
- Regulation agent.
- Design variant agent.
- BIM manager agent.
- Permit agent.
- Tender agent.
- Construction management agent.
- Handover agent.

Agents should not make critical decisions alone. They propose, cite, simulate, validate, and ask for human approval when needed.

### 6. Verification Layer

The system needs checks before and after actions:

- Source citation check.
- Rule applicability check.
- Geometry/model sanity check.
- IFC validation.
- IDS checks.
- Visual diff.
- Action log.
- Human approval gates.

## Design Principles

- Canonical first: no unsupported project truth.
- Tool neutral: avoid locking the business logic to one CAD/BIM vendor.
- Archicad first: optimize the first MVP around the user's real workflow.
- Local first where possible: keep desktop tools usable through localhost bridges.
- Human accountable: agents assist, but the architect remains responsible.
- Evidence over eloquence: every claim should point to a source or marked assumption.

