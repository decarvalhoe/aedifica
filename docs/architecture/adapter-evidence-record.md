# Adapter Evidence Record

Status: R1A/R3 contract note, 2026-05-31.

Adapter actions are professional work. Every mutating or potentially mutating model/drawing action must be
represented as evidence before it can become execution.

## Minimum Record

```json
{
  "evidence_id": "EVID-ADAPTER-DRYRUN-001",
  "kind": "adapter_dry_run",
  "adapter_id": "archicad_json",
  "project_id": "DEMO-LAUSANNE-PALUD",
  "phase_code": "32",
  "source_model_version": "ARCHICAD-DEMO-V3",
  "intent_id": "INTENT-DEMO-ROOM-PROGRAM-001",
  "before_ref": "project://models/model_v3.ifc",
  "dry_run_ref": "project://adapter_dry_runs/INTENT-DEMO-ROOM-PROGRAM-001.json",
  "approval_ledger_id": "LEDGER-APPROVAL-BRIDGE-DRYRUN",
  "verification_ref": null,
  "execution_allowed": false,
  "created_at": "2026-05-31T08:25:00+02:00"
}
```

## Rules

- `before_ref` is required before any dry-run.
- `dry_run_ref` is required before human approval.
- `approval_ledger_id` is required before execution.
- `verification_ref` is required before a report can claim execution success.
- `execution_allowed=false` remains the default for fixture mode.
- Live adapters reuse the same record shape; only transport and refs change.

## Later Adapter Snapshots

The R4 fixture baselines normalize IFC/IfcOpenShell and Speckle snapshots to the same minimum evidence shape:

- `pilot/model/ifc_snapshot_fixture.json`
- `pilot/model/speckle_snapshot_fixture.json`

Both expose adapter id, source model/version ref, elements, spaces, property sets and quantity refs. The live IFC
and Speckle integrations can replace fixture loading without changing the approval and evidence lifecycle.
