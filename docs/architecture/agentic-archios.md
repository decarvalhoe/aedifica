# Agentic ArchiOS Architecture

## Target Architecture

```text
NOMOS Project Memory
  -> Sources, regulations, decisions, program, versions

Canonical Constraint Matrix
  -> Federal, cantonal, communal, SIA, office, and project rules

BIM/Model Layer
  -> Archicad, Revit, IFC, Speckle, Rhino, DWG

Agentic Workflow Layer
  -> Strategy, design, BIM, permits, tendering, execution, construction management

Verification Layer
  -> IDS, IFC checks, visual diff, logs, human approval

Action Layer
  -> Local MCP/API, plugins, CLI, batch jobs
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

This layer is what prevents the agent from improvising Swiss regulatory or project truth. It should separate:

- Sourced fact.
- Interpretation.
- Assumption.
- Conflict.
- Exception.
- Human decision.

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

Software and workflow systems get adapters:

- Archicad Add-On / JSON API / Tapir.
- Revit Add-In / Design Automation API.
- Rhino / Grasshopper / Rhino.Compute.
- SketchUp Ruby extension.
- AutoCAD / BricsCAD CLI and scripts.
- IFC via IfcOpenShell.
- Speckle connectors.
- Document repositories and office templates.
- Construction-management tools.
- Email/calendar/task systems where relevant.

The adapter must expose safe actions through one common API shape.

The core must remain tool-neutral and workflow-first. A first Archicad adapter can validate the approach, but the ontology is the architectural process, not a software API.

### 5. Agentic Workflow Layer

Specialized agents work on bounded domains:

- Intake agent.
- Regulation agent.
- Design variant agent.
- BIM manager agent.
- Permit agent.
- Tender agent.
- Coordination agent.
- Construction management agent.
- Handover agent.
- Voice-to-design agent.

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

For BIM-specific validation, the architecture should consider IFC, IDS, BCF, and Speckle snapshots as neutral artifacts that can be checked outside the authoring tool.

## Design Principles

- Canonical first: no unsupported project truth.
- Tool neutral: avoid locking the business logic to one CAD/BIM vendor.
- Workflow first: assist the architect's job before optimizing for a specific tool.
- Adapter based: connect to Archicad or another tool only where it creates real leverage.
- Local first where possible: keep desktop tools usable through localhost bridges.
- Human accountable: agents assist, but the architect remains responsible.
- Evidence over eloquence: every claim should point to a source or marked assumption.
