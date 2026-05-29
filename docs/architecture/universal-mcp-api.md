# Universal Architecture MCP/API

This document sketches the first common action surface for agentic architecture tools.

The goal is not to expose every software command one-to-one. The goal is to expose stable architectural commands that can be implemented by different adapters.

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

## Initial Command Groups

### Project and Context

```text
inspect_project
get_project_metadata
get_current_view
get_selection
list_layers_or_attributes
list_favorites_or_types
```

### Model Extraction

```text
extract_spaces
extract_elements
extract_properties
extract_quantities
export_model_snapshot
compare_model_snapshots
```

### Model Mutation

```text
create_wall
create_slab
create_opening
place_object
update_parameters
update_bim_properties
rename_elements
classify_elements
```

### BIM and IFC

```text
run_bim_audit
apply_property_mapping
validate_ifc_requirements
export_ifc
export_bcf
sync_speckle
```

### Documentation

```text
publish_layouts
export_pdf_set
export_dwg_set
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

## First Adapter Priority

1. Archicad inspection and export.
2. Archicad BIM property updates.
3. IFC extraction and validation through IfcOpenShell.
4. Speckle synchronization.
5. Revit and Rhino adapters after the first Archicad MVP.

