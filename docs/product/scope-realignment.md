# Aedifica Product Scope Realignment

Status: product guardrail, 2026-05-31.

## Decision

Aedifica is not scoped by the visual surfaces generated for pitch, dashboard, intake, report or sales material. Those surfaces are communication and UX artifacts. They must not redefine the product.

Aedifica remains **ArchiOS Suisse**: an agentic operating layer that assists the architect across the full architectural process, from project intake and regulatory constraints to design reasoning, drawing/model assistance, BIM/CAD data, deliverables, permitting, tendering, site work, handover and project memory.

## Product Shape

The product has two inseparable movements:

1. **Bottom-up canonical intelligence**: collect sources, project material, registers, drawings, model states, office standards and decisions; transform them into canonical, source-backed project memory.
2. **Top-down architectural assistance**: let agents reason over that memory, propose next actions, generate briefs/reports/specifications, and execute approved actions through a universal architecture API.

The first wedge can be regulatory/project intelligence because it proves concrete value without requiring BIM maturity. That wedge does **not** mean Aedifica is only a permit assistant or a report generator.

## Multi-Software Drawing And Model Assistance

The multi-software API is a native product axis. It is the execution and inspection layer for architectural work:

- inspect drawings, sheets, spaces, elements, quantities and properties;
- generate structured design or drawing intents;
- compare model/drawing versions;
- run project-aware checks against requirements and sources;
- update BIM/CAD properties only after dry-run, approval and ledger entry;
- export IFC, PDF, DWG, BCF, reports or office deliverables through adapters.

Adapter targets include Archicad, Revit, Rhino/Grasshopper, SketchUp, AutoCAD/BricsCAD, Vectorworks, IFC, Speckle, office documents and later construction-management systems. Archicad is a first partner bridge, not the product identity.

## Scope Guardrails

- Do not reduce Aedifica to the currently generated UI/design surfaces.
- Do not reduce Aedifica to regulatory reports, even if the first wedge is regulatory.
- Do not reduce Aedifica to drawing automation, even though drawing/model assistance is first-class.
- Keep the neutral engine, project memory and universal API as the stable product center.
- Treat every adapter action as professional work: dry-run, evidence snapshot, human approval, execution, verification and ledger.
- Treat generated product and pitch surfaces as viewport-fit states. If content does not fit, create another state, chapter or export artifact instead of relying on body scroll.

## Roadmap Consequence

R1/R2 can remain focused on parcel, permit and opposition because they are the fastest evidence-backed path. In parallel, the architecture and backlog must keep the multi-software drawing/model API alive as a planned native capability, not as an optional afterthought.
