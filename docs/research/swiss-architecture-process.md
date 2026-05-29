# Swiss Architecture Process

This document frames the lifecycle Aedifica should model first. It uses the SIA phase structure as the backbone, then extends it with agentic opportunities.

The validated implementation asset for this lifecycle is now
[`swiss-phase-lifecycle-matrix.md`](swiss-phase-lifecycle-matrix.md), backed by
`pilot/research/swiss_phase_lifecycle_matrix.json`. That matrix adds actors, decisions, deliverables, risks,
and small/medium/large project variants for each phase.

## Reference Backbone

The natural reference model is the Swiss SIA process:

- Phase 1: strategic planning.
- Phase 2: preliminary studies.
- Phase 3: project.
- Phase 4: tendering.
- Phase 5: realization.
- Phase 6: operation.

The operational breakdown used by Aedifica should include:

- 31 preliminary project.
- 32 project.
- 33 authorization.
- 41 tendering.
- 51 execution project.
- 52 execution.
- 53 commissioning and closure.

The product should also model pre-SIA intake, because many decisive constraints are collected before the architect starts producing formal phase deliverables.

## Phase Matrix

| Phase | Swiss/SIA framing | Typical architect activities | Documents and data | Agentic opportunities |
|---|---|---|---|---|
| 0 / Intake | Pre-project context | Collect client need, parcel, budget, constraints, risks | Client brief, parcel ID, cadastral extracts, zoning, photos, existing drawings | Project intake, document ingestion, source registry, first constraint map |
| 1 | Strategic planning | Clarify objectives, feasibility, project organization | Needs analysis, budget order, risks, project setup | Feasibility assistant, constraint summarizer, decision log |
| 2 | Preliminary studies | Variants, site analysis, competition strategy, consultant setup | Existing conditions, regulation extracts, scenarios, initial surfaces | Variant generation, rule scoring, competition dossier assistant |
| 3.1 | Preliminary project | Architectural concept, surfaces, massing, costs | Plans, sections, model, surface schedules, cost estimate | Program compliance, surface checks, model summaries |
| 3.2 | Project | Technical coordination, material choices, BIM development | BIM model, specialist inputs, IFC, reports, details of principle | Auto-BIM, metadata completion, clash/check workflows |
| 3.3 | Authorization | Build permit dossier | Official forms, signed drawings, notices, calculations, justifications | Permit checklist, dossier completeness, local regulation verification |
| 4 | Tendering | Quantities, specifications, offers, comparisons | CFC/eCCC structure, bills of quantities, tender docs, bids | Quantity extraction, spec drafting, offer comparison |
| 5.1 | Execution project | Execution drawings, details, coordination | Execution plans, details, updated BIM, technical approvals | Drawing set control, change tracking, detail consistency |
| 5.2 | Execution / site | Construction management, site meetings, defects, costs, schedule | PVs, photos, site tasks, invoices, defects, decisions | Site report agent, task extraction, budget/schedule alerts |
| 5.3 | Commissioning | Handover, defects, final documentation | As-built, warranties, manuals, defects, final accounts | Handover checklist, as-built control, documentation assembly |
| 6 | Operation | Facility use, maintenance, transformations | As-built BIM, intervention records, energy data | Project memory for future renovation and maintenance |

## Swiss-Specific Complexity

The Swiss context is not one homogeneous rulebook. Aedifica must model several source layers:

- Federal framework.
- Cantonal law and procedure.
- Communal zoning and building regulations.
- Parcel-level constraints.
- Servitudes and neighboring rights.
- SIA standards and professional norms.
- Fire, energy, accessibility, heritage, environmental, and civil protection constraints.
- Client program and budget.
- Competition or mandate rules when applicable.

The agent must be able to say which source supports a claim, which phase the rule applies to, and whether it can verify the rule automatically.

## Bottom-Up Project Birth

The product should treat a project as something born from constraints, not from drawing commands.

The first useful project object is therefore not a wall or room. It is a sourced project context:

```text
site + parcel + commune + canton + program + budget + regulation + decisions + unknowns
```

From this context, Aedifica should produce:

- A source registry.
- A constraint matrix.
- A risk list.
- A first feasibility brief.
- A phase-specific deliverable plan.
- A set of model/BIM checks that can later be applied to Archicad, IFC, or Speckle.

## Project Sizes

### Small Projects

Examples: villa, apartment transformation, small extension, interior renovation.

Characteristics:

- Fewer actors.
- Strong need for permit and drawing efficiency.
- BIM often underused.
- High value in document assembly and model cleanup.

### Medium Projects

Examples: small housing block, mixed-use renovation, public facility, office building.

Characteristics:

- More consultants.
- IFC coordination becomes valuable.
- Tendering and construction management become heavier.
- Good target for Auto-BIM plus permit/tender workflows.

### Large Projects

Examples: large housing, hospitals, schools, infrastructure-adjacent buildings.

Characteristics:

- Formal BIM requirements.
- Specialist coordination.
- More legal, procurement, and reporting overhead.
- Higher need for auditability and integration with existing enterprise tools.

## Initial Research Tasks

1. Build a detailed SIA phase-to-deliverable matrix.
2. Identify differences between small, medium, and large projects.
3. Map Swiss federal/cantonal/communal source types.
4. Build a sample canton/commune research pack.
5. List BIM information requirements by phase.
6. Identify high-frequency repetitive office workflows.
7. Identify where agentic automation can produce immediate time savings.
8. Separate automatable checks from judgment calls requiring an architect.
