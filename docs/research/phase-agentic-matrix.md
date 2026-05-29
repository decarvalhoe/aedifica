# Phase-by-Phase Agentic Matrix

This matrix is the next working backbone for Aedifica research. It expands the SIA-oriented lifecycle with documents, decisions, BIM data, source types, possible agents, required APIs, and feasibility.

The implementation-facing handoff format is now defined in
[`../nomos/phase-aware-constraint-matrix.md`](../nomos/phase-aware-constraint-matrix.md), with a validated
pilot file at `pilot/constraints/mvp1_lausanne_matrix.json`. The table below remains a research overview.

The detailed Swiss lifecycle matrix for issue #1 is now the validated asset
[`swiss-phase-lifecycle-matrix.md`](swiss-phase-lifecycle-matrix.md), backed by
`pilot/research/swiss_phase_lifecycle_matrix.json`. Use that file for phase coverage, actors, decisions,
deliverables, risks, and small/medium/large project variants.

## Matrix

| Phase | Documents and decisions | BIM/model data | Regulatory/source inputs | Agentic intervention | Required API/MCP surface | Feasibility |
|---|---|---|---|---|---|---|
| 0/1 Intake and strategy | Client brief, parcel, budget, objectives, initial risks, project setup | Existing drawings if available, site photos, survey files | Parcel, cadastre, commune, canton, federal context, SIA phase expectations | NOMOS ingestion, source registry, feasibility brief, unknowns list | `load_project_context`, `inspect_project`, document ingestion | High |
| 2 Preliminary studies | Variants, competition brief, massing, surfaces, decision matrix | Early massing, zoning envelope, rough areas | SIA 142/143 if competition, zoning, local rules, program | Variant generation, regulatory scoring, comparison matrix | `generate_variant`, `extract_quantities`, `compare_versions` | Medium |
| 31 Avant-projet | Plans, sections, surface schedule, estimate, concept decisions | Spaces, levels, surfaces, building envelope | Program, commune/canton constraints, SIA deliverables | Program/surface checks, concept risk report, cost assumptions | `extract_spaces`, `extract_quantities`, `run_model_check` | High |
| 32 Projet de l'ouvrage | Coordinated model, specialists, details of principle, reports | BIM/CAD model, IFC, Speckle snapshots, classifications, properties | Office BIM rules, project digital-information convention, project requirements | Auto-BIM, metadata enrichment, IFC preparation, model audits | `extract_elements`, `update_bim_properties`, `export_ifc`, `validate_ifc_requirements` | High |
| 33 Autorisation | Permit forms, signed plans, notices, calculations, justifications | Permit plan set, project metadata, areas | Federal/cantonal/communal procedure, local checklist | Dossier checklist, completeness check, citation-backed notes | `publish_pdf_set`, `check_dossier_completeness`, `generate_report` | High |
| 41 Appel d'offres | CFC/eCCC structure, quantities, tender descriptions, offers | Quantities, element types, materials, room/element schedules | Office standards, project decisions, procurement constraints | Quantity extraction, draft specs, offer comparison, assumptions log | `extract_quantities`, `generate_schedule`, `generate_report` | Medium |
| 51 Projet d'exécution | Execution drawings, details, coordination comments, revisions | Detailed BIM/model, sheets, details, issue links | Specialist requirements, approvals, execution decisions | Drawing set audit, detail consistency, change tracking | `publish_layouts`, `compare_model_snapshots`, `run_model_check` | Medium |
| 52 Exécution de l'ouvrage | Site minutes, photos, tasks, defects, costs, schedule, invoices | Model-linked issues, as-built deviations | Contracts, site decisions, safety/quality constraints | Site report agent, task extraction, defect tracking, budget/schedule alerts | `create_site_report`, `extract_tasks_from_minutes`, `track_defect`, `link_issue_to_model_element` | Medium |
| 53 Mise en service, achèvement | Reception, defects, warranties, final accounts, handover docs | As-built BIM, final IFC, final drawings | Contractual handover requirements, owner requirements | Handover checklist, completeness audit, as-built package | `generate_handover_checklist`, `export_ifc`, `publish_pdf_set` | Medium |
| 61/62/63 Operation | Maintenance records, interventions, renovation decisions | As-built model, asset data, future changes | Facility requirements, energy/maintenance records | Project memory for operation and future renovation | `inspect_project`, `update_decision_log`, `compare_versions` | Later |

## Research Use

Each row should become a deeper research pack:

- Actors.
- Required documents.
- Typical pain points.
- Automatable checks.
- Human decisions.
- Data structures.
- Software touchpoints where they matter.
- MVP priority.

## Immediate Next Step

The remaining phase work should now enrich individual phase packs with real office examples, not recreate the
phase backbone.
