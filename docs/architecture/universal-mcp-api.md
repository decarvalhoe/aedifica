# Universal Architecture MCP/API

This document sketches the first common action surface for agentic architecture workflows.

The goal is not to expose every software command one-to-one. The goal is to expose stable architectural workflow commands that can be implemented by different adapters, including BIM/CAD/drawing tools, document systems, IFC/Speckle, permit dossier workflows, and construction-management systems.

This API is a native part of Aedifica's product scope. The first regulatory workspace can ship before full adapter implementation, but the product architecture must keep model/drawing assistance as a first-class surface rather than treating it as a detached future experiment.

This API belongs behind the neutral-engine boundary defined in
[`adr-0001-neutral-engine-and-jurisdiction-packs.md`](adr-0001-neutral-engine-and-jurisdiction-packs.md). Mutating
commands must follow the ledger and approval contract in
[`trust-contract-and-ledger.md`](trust-contract-and-ledger.md).

## Transport

Initial candidates:

- Local HTTP server exposed by the plugin.
- WebSocket for streaming progress and model events.
- MCP server for direct agent integration.
- CLI wrapper for batch workflows.

## Safety Requirements

- Every mutating command must support dry-run.
- Every mutating command must return an action plan before execution.
- Commands should be grouped into transactions when the target software supports undo.
- Logs must include actor, source, command, target elements, before/after summaries, and result.
- Critical actions require approval.

Minimum command lifecycle:

```text
intent -> inspect -> dry-run plan -> evidence snapshot -> human approval -> execute -> verify -> ledger entry
```

## Initial Command Groups

### Project and Context

```text
inspect_project
get_project_metadata
get_current_view
get_selection
list_layers_or_attributes
list_favorites_or_types
load_project_context
resolve_phase_deliverables
```

### Model Extraction

```text
extract_spaces
extract_elements
extract_properties
extract_quantities
export_model_snapshot
compare_model_snapshots
extract_bim_requirements
```

### Model Mutation

```text
create_wall
create_slab
create_opening
place_object
move_element
adjust_opening
update_parameters
update_bim_properties
rename_elements
classify_elements
generate_variant
```

### Drawing And Layout Assistance

```text
create_drawing_view
update_drawing_annotations
check_drawing_set
compare_drawing_versions
publish_layouts
export_pdf_set
export_dwg_set
```

### BIM and IFC

```text
run_bim_audit
run_model_check
apply_property_mapping
validate_ifc_requirements
export_ifc
export_bcf
sync_speckle
```

### Documentation

```text
generate_schedule
generate_report
check_dossier_completeness
```

### Construction Management

```text
create_site_report
extract_tasks_from_minutes
link_issue_to_model_element
track_defect
update_decision_log
generate_handover_checklist
```

## Adapter Strategy

The common API should be designed before any single adapter dominates the product.

Early adapter candidates:

1. Project/document ingestion adapter.
2. IFC extraction and validation through IfcOpenShell.
3. Speckle synchronization and version snapshots.
4. Archicad inspection, export, drawing/model assistance and BIM property updates.
5. Revit, Rhino/Grasshopper, SketchUp, AutoCAD/BricsCAD, and construction-management adapters.

## Voice-to-Design Contract

Voice should enter the system as intent, not as raw tool commands.

```text
speech
  -> transcript
  -> structured design intent
  -> dry-run action plan
  -> visual/model preview
  -> human approval
  -> MCP/API execution
  -> report and diff
```

This keeps the long-term dream of prompted architectural work compatible with professional responsibility, project context, and model safety.
