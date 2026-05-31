# BIM/CAD Adapter Capability Map

Issues: #10, #13, #14  
Structured file: `pilot/research/adapter_capability_matrix.json`  
Prototype: `pilot/model_bridge_demo.py`

## Decision

Use **Archicad JSON** as the first local bridge for the partner-office demo, with **IFC/IfcOpenShell** and
**Speckle** as neutral fallbacks. Do not make Archicad the identity of the product.

## Sources Checked

- Graphisoft Archicad JSON Interface: <https://archicadapi.graphisoft.com/JSONInterfaceDocumentation/>
- Graphisoft Archicad C++ API DevKit: <https://graphisoft.github.io/archicad-api-devkit/>
- IfcOpenShell documentation: <https://docs.ifcopenshell.org/>
- Speckle Automate documentation: <https://docs.speckle.systems/developers/automate/introduction>
- Autodesk Revit API: <https://aps.autodesk.com/developer/overview/revit-api>
- Rhino Compute: <https://developer.rhino3d.com/en/guides/compute/features/>
- SketchUp Ruby API: <https://help.sketchup.com/en/sketchup/developing-tools-sketchup-ruby-api-and-console>

Checked on 2026-05-31.

## Adapter Tiers

| Tier | Adapter | Aedifica use |
|---|---|---|
| First local bridge | Archicad JSON | Inspect selection/elements/properties, propose property/classification updates, dry-run plans. |
| Deep Archicad later | Archicad C++ Add-On | Native events, deeper database access, custom UI, later distribution. |
| Neutral baseline | IFC + IfcOpenShell | Vendor-independent model reading, validation, quantities, memory snapshots. |
| Version layer | Speckle | Model versions, automation runs, collaboration when adopted by the office. |
| Later authoring adapters | Revit, Rhino, SketchUp, AutoCAD/BricsCAD, Vectorworks | Add once neutral workflow contracts prove value. |

## Bridge Rule

Every adapter must expose:

- read capabilities;
- write capabilities;
- export capabilities;
- known limits;
- safety gates before mutation.

The universal API remains stable; adapters satisfy parts of it.

## Prototype

```bash
python pilot/model_bridge_demo.py
```

The demo does not connect to Archicad. It proves that the first bridge can produce dry-run plans from a
capability manifest before any mutating model action is allowed.

## Fixture Baselines

The first neutral baselines live in the pilot as normalized snapshots:

- `pilot/model/ifc_snapshot_fixture.json` for the IFC/IfcOpenShell path.
- `pilot/model/speckle_snapshot_fixture.json` for the Speckle path.

They do not replace live adapters. They preserve the output contract that live IFC and Speckle connectors must
produce: source model ref, elements, spaces, property sets and quantity refs behind the same dry-run/approval
lifecycle.
