# Local Model Bridge Prototype

Issue: #11

The first Aedifica model bridge is a **contract prototype**, not a full Archicad add-on. It proves the safe
execution lifecycle for model work:

```text
select adapter -> check capabilities -> capture before snapshot -> dry-run plan -> approval -> execute -> verify -> memory
```

## Current Prototype

File: `pilot/model_bridge_demo.py`

Supported demo actions:

- `inspect_selected_elements`: non-mutating inspection plan.
- `set_room_usage_property`: mutating property-update plan, requiring dry-run and approval.

The prototype reads `pilot/research/adapter_capability_matrix.json` and currently selects `archicad_json` as
the first bridge.

Current offline functions:

- `health_check()` reports adapter availability plus declared read/write capabilities.
- `inspect_selected_elements()` returns element IDs, classifications, properties and source model version from
  `pilot/model/archicad_selection_fixture.json`.
- `missing_metadata_audit()` lists selected spaces missing required properties and proposes fixes.
- `dry_run_property_update()` prepares a property update but blocks it until a ledger approval exists.

## Why This Counts

It avoids two common traps:

- writing an Archicad-specific plugin before the neutral workflow contract is stable;
- letting an agent jump from natural-language instruction to model mutation.

The next implementation step is to replace the dry-run command placeholders with real Archicad JSON calls
against a local running Archicad instance.
