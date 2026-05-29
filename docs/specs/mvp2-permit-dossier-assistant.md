# MVP2 Spec — Permit Dossier Assistant

> Implementation-ready specification for issue #17. The original issue title says "MVP 3"; the revised roadmap
> moves permit readiness directly after MVP1 because the parcel/source/constraint spine already feeds phase `33`.
> Pilot jurisdiction: **Vaud / Lausanne**. Status: build spec on top of validated contracts.

## 1. Goal

From an MVP1 project context plus a project dossier, produce a **permit-readiness package**:

- completeness report;
- missing evidence list;
- citation-backed notes;
- phase `33` compliance gate report;
- handoff actions for architect and specialists.

Aedifica does **not** submit to ACTIS-CAMAC and does **not** decide legality. It prepares evidence and makes
uncertainty visible so the architect can decide whether the dossier is ready to file.

## 2. Inputs

- Project context from MVP1: parcel, commune, canton, EGRID, zone, constraints matrix, regulatory route.
- Program and use: housing, public use, transformation, new build, protected/heritage context if known.
- Project dossier object: evidence keys, uploaded files, plan-set metadata, signatures, forms, calculations,
  notices, specialist reports.
- Jurisdiction checklist: `pilot/permit/vd_camac_checklist.json`.
- Compliance gates: `pilot/compliance/ch_phase33_gates.json`.
- Source registry: `pilot/research/pilot_source_registry.json`.
- Human decisions and assumptions from the project ledger.

## 3. Outputs

1. **Completeness report** — required/present/missing items, grouped by category and responsible actor.
2. **Missing evidence actions** — what to add, who should provide it, and which source requires it.
3. **Citation notes** — short draft notes tied to source IDs, locators, and `valid_as_of` dates.
4. **Compliance gate report** — energy, fire, accessibility, structure, and contractual BIM conventions typed
   as legal/authority-triggered/contractual.
5. **Unknowns & assumptions** — visible blockers that need architect or specialist confirmation.
6. **Authority handoff pack** — preparation checklist for ACTIS-CAMAC/commune workflow; not an automated filing.

## 4. Pipeline

| Step | Action | Contract |
|---|---|---|
| 1 | Load project context and regulatory route | `selector.py`, MVP1 output |
| 2 | Select checklist for canton/commune/project type | `vd_camac_checklist.json` |
| 3 | Map dossier evidence to accepted evidence keys | project dossier object |
| 4 | Run missing-item detector | `validate_permit.py` |
| 5 | Run phase `33` compliance gates | `validate_compliance.py` |
| 6 | Generate citation-backed notes and blockers | source registry + trust contract |
| 7 | Require human review before "ready to file" | decision ledger |

## 5. Data Contract

The current demo dossier is intentionally minimal:

```json
{
  "checklist_id": "VD-ACTIS-CAMAC-PHASE33",
  "evidence": {
    "application_form": true,
    "signed_plans": false,
    "energy_form": false,
    "fire_safety_note": false
  }
}
```

Production should replace booleans with file-backed evidence objects:

```json
{
  "evidence_id": "EVID-ENERGY-001",
  "kind": "energy_form",
  "file_ref": "project://documents/energy_form.pdf",
  "source_id": "VD-ENERGY-FORMS",
  "provided_by": "physicien du batiment",
  "status": "submitted_for_review",
  "checked_at": "2026-05-29"
}
```

## 6. Trust Rules

- Every missing item must cite the source or checklist item that triggered it.
- Every generated note must carry source IDs and dates.
- `contractual_not_legal` gates must never be rendered as legal permit obligations.
- The final status can be `draft`, `missing_required_evidence`, `ready_for_human_review`, or
  `architect_approved_for_filing`; the system cannot mark a dossier "authorized".

## 7. Success Criteria

- Given the demo incomplete dossier, the system reports the three known blockers:
  signed plans, energy evidence, fire evidence.
- A complete test dossier can be added later and must produce zero required blockers while still listing
  conditional gates for human confirmation.
- The report distinguishes authority/legal requirements from office/project conventions.
- The architect can see exactly why each required item is present, missing, conditional, or out of scope.

## 8. Current Implementation

- Permit contract: [`../permit/vd-camac-permit-completeness.md`](../permit/vd-camac-permit-completeness.md)
- Compliance gates: [`../compliance/phase33-compliance-gates.md`](../compliance/phase33-compliance-gates.md)
- Checklist data: `pilot/permit/vd_camac_checklist.json`
- Demo dossier: `pilot/permit/demo_missing_dossier.json`
- Validators: `pilot/validate_permit.py`, `pilot/validate_compliance.py`
- CI: validates permit/compliance contracts and `pilot/selfcheck.py`

## 9. Boundaries

- Canton/commune-specific additions remain project-scoped until ingested.
- Conditional forms depend on project type, use, size, energy scope, fire-safety concept, accessibility trigger,
  and authority practice.
- Aedifica prepares and audits; the architect, specialists, commune, and canton remain the decision authorities.
