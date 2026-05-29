# NOMOS Archi

NOMOS Archi adapts the canonical-first method to architecture projects.

## Purpose

Architecture agents need a trusted project context. They cannot safely infer regulatory, technical, or contractual truth from prompts alone.

NOMOS Archi provides:

- Source registry.
- Constraint atomization.
- Project rule matrix.
- Evidence tracking.
- Exception management.
- Decision records.
- Phase-aware applicability.
- Model-aware verification.
- Human approval gates.

## Source Types

| Source type | Examples |
|---|---|
| Federal | Federal spatial planning and construction-related frameworks |
| Cantonal | Cantonal planning, construction, energy, fire, procedure rules |
| Communal | Zoning plan, building code, local constraints |
| Parcel | Cadastral extract, easements, topography, existing state |
| Professional | SIA standards, BIM standards, office methodology |
| Project | Client brief, program, budget, meetings, decisions |
| Model | Archicad/Revit/IFC/Speckle snapshots |
| Execution | Site reports, defects, invoices, approvals, handover docs |

## Two RAG Contexts

Aedifica should separate two retrieval contexts:

### Project RAG

Project-specific memory:

- Client program.
- Parcel and commune.
- Project decisions.
- Model versions.
- Meeting minutes.
- Permit documents.
- Tender and construction records.

### General Swiss Architecture RAG

Reusable knowledge:

- SIA process references.
- Swiss BIM/openBIM practices.
- Canonical regulatory patterns.
- Office method templates.
- Construction-management workflows.

The agent must never mix these contexts silently. Project-specific facts have priority for the project, while general knowledge can guide structure, interpretation, and checklists.

## Canonical Unit Types

```text
rule
term
requirement
constraint
formula
exception
decision
evidence
deliverable
check
action
```

## Example Unit

```yaml
unit_id: ARCHI-REQ-BIM-SPACE-NAME
unit_type: requirement
phase_applicability:
  - "3.2 Project"
  - "3.3 Authorization"
  - "4 Tendering"
domain: bim
criticality: medium
source_refs:
  - source_id: OFFICE-BIM-GUIDE
    locator: "section: room properties"
business_rule: "Every modeled space must have a stable name, number, level, area, and usage classification before export."
verification:
  method: model_query
  command: extract_spaces
  pass_condition: "No space has missing name, number, level, area, or usage classification."
actions:
  - update_bim_properties
status: draft
```

## Agent Contract

Agents using NOMOS Archi must:

- Cite source-backed rules when explaining constraints.
- Mark assumptions explicitly.
- Separate recommendation from decision.
- Never silently mutate a model.
- Log every model action with before/after evidence.
- Escalate conflicts between sources.
- Identify whether a check can be automated, semi-automated, or only reviewed by a human.
