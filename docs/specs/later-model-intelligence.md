# Native Track Spec — Multi-Software Drawing / Model Intelligence

Issue: #16  
Status: native product track, scheduled after the first regulatory proof points but not removed from scope.

## Goal

Inspect a BIM/CAD/IFC/Speckle/Archicad/Revit/Rhino/SketchUp source, detect missing or inconsistent information,
turn approved architectural intent into safe drawing/model commands, apply only approved changes through the
available adapter, export deliverables, and write a traceable report.

## Inputs

- Project context: phase, constraints, permit conditions, office standards, decisions.
- Model/drawing source: IFC, Speckle version, Archicad/Tapir/JSON export, Revit, Rhino/Grasshopper, SketchUp, AutoCAD/BricsCAD or PDF/DWG set where available.
- Structured drawing/model intent: desired geometry, property, classification, sheet, export or check action.
- BIM requirements: room/space properties, classification, property sets, IFC/export expectations.
- Adapter capability manifest: what can be read, written, previewed, exported, or undone.

## Pipeline

1. Inspect project and adapter capabilities.
2. Extract spaces, elements, properties, classifications, quantities and model version.
3. Compare extracted data with project requirements and office rules.
4. Produce a missing/inconsistent information audit.
5. Propose a drawing/model correction or generation plan with before/after diff.
6. Run dry-run and require human approval.
7. Execute through adapter when approved.
8. Verify output and write memory/ledger records.

## Outputs

- Model audit.
- Drawing/model intent plan.
- Correction plan.
- Dry-run diff.
- Approval record.
- Export report: IFC/PDF/DWG where adapter supports it.
- Memory records linking changes to model version, actor, evidence and phase.

## Safety

- No model mutation without dry-run.
- No model mutation without human approval.
- Every write must capture before/after state.
- Adapter capability check must precede every action.
- Failed verification blocks the report from claiming success.

## Success Criteria

- Detects missing room/space metadata and classification gaps.
- Produces structured drawing/model actions from approved project intent.
- Produces traceable proposed fixes.
- Does not mutate a model without approval.
- Produces an export/check report linked to project memory.
