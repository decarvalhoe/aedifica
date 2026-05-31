# Holistic Architect Assistance

Aedifica should assist the architect's full responsibility, not only drawing or software automation.

## Product Scope

The product covers nine assistance layers:

1. **Project orientation**: clarify phase, stakeholders, next decisions, risks, and missing inputs.
2. **Constraint intelligence**: collect and structure federal, cantonal, communal, parcel, SIA, office, and client constraints.
3. **Design reasoning**: compare variants, surfaces, programs, feasibility, costs, and regulatory fit.
4. **Model intelligence**: inspect BIM/CAD/IFC/Speckle data and connect it to project requirements.
5. **Documentation**: prepare briefs, reports, drawing sets, permit dossiers, schedules, and handover packs.
6. **Coordination**: track decisions, consultant inputs, open questions, model versions, and conflicts.
7. **Procurement**: support quantities, tender packages, offer comparison, assumptions, and exclusions.
8. **Construction management**: site reports, tasks, defects, photos, costs, schedule, approvals, and handover.
9. **Drawing and model assistance**: structured design/drawing intent, model inspection, drawing-set checks, version comparison, BIM/CAD updates and exports.
10. **Tool execution**: act through adapters only when the workflow needs software-side execution.

## What This Is Not

Aedifica is not:

- An Archicad-only plugin.
- A drawing-only assistant.
- A generic RAG chatbot.
- A prompt-to-CAD demo detached from professional process.
- A replacement for the architect's legal and professional responsibility.
- A product whose scope is defined by the current pitch/dashboard/report surfaces.

## What This Is

Aedifica is a project-aware operating layer:

```text
Project sources
  -> canonical constraints
  -> phase-aware workflow state
  -> agentic recommendations
  -> checked actions
  -> project evidence and memory
```

Tool automation is downstream of that operating layer. The system should first understand what the architect is trying to achieve and what the project allows, then choose whether the next action is a question, a report, a checklist, a model check, a BIM update, an export, a site task, or a human decision.

The multi-software drawing/model API is part of that operating layer's normal action surface, not a side idea. It exists to turn project knowledge into safe architectural work inside Archicad, Revit, Rhino/Grasshopper, SketchUp, AutoCAD/BricsCAD, IFC, Speckle and office documents, with dry-run and approval before any mutation.

## Generalization Principle

Every feature should be evaluated against this question:

> Does this help an architect move a real project forward across the Swiss process, or does it only automate a narrow software command?

Narrow automation is acceptable only when it compounds into the broader project memory and workflow.
