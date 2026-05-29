# Vaud ACTIS-CAMAC Permit Completeness

This contract is the first Aedifica permit-readiness surface for phase `33`. It is not a submission tool.
ACTIS-CAMAC and the competent authority remain the receiving and deciding rails. Aedifica pre-checks whether
the architect has assembled the expected evidence before filing.

Product spec: [`../specs/mvp2-permit-dossier-assistant.md`](../specs/mvp2-permit-dossier-assistant.md).

## Files

- Checklist: `pilot/permit/vd_camac_checklist.json`
- Demo incomplete dossier: `pilot/permit/demo_missing_dossier.json`
- Validator/report: `pilot/validate_permit.py`

## Sources Checked

- Etat de Vaud, permits and ACTIS-CAMAC platform:
  <https://www.vd.ch/territoire-et-construction/permis-de-construire>
- Etat de Vaud, preparing a permit dossier:
  <https://www.vd.ch/territoire-et-construction/permis-de-construire/realiser-son-dossier-en-vue-dune-demande-de-permis-de-construire>
- Etat de Vaud, CAMAC role:
  <https://www.vd.ch/dits/dgtl/dac/camac>

These sources were checked on 2026-05-29 and are recorded in the JSON checklist with `valid_as_of`.

## Checklist Item

```json
{
  "item_id": "VD-CAMAC-SIGNED-PLANS",
  "title": "Signed permit plans",
  "category": "plans",
  "required": true,
  "claim_state": "sourced",
  "accepted_evidence": ["signed_plans"],
  "source_ids": ["VD-REALISER-DOSSIER"],
  "missing_message": "Ajouter les plans de mise a l'enquete signes par les professionnels requis."
}
```

The `accepted_evidence` keys are the bridge to a future project dossier object. The current demo dossier uses
booleans to prove missing-item detection.

## Missing-Item Detection

```bash
python pilot/validate_permit.py
```

The demo incomplete dossier currently reports:

- missing signed plans;
- missing energy forms / SIA 380/1 evidence;
- missing fire-safety evidence.

This is intentional: the validator must prove it can fail a dossier before it can be trusted to pass one.

## Boundaries

- The checklist is a baseline for Vaud/ACTIS-CAMAC. Communal additions and project-specific special
  questionnaires remain scoped by the actual project.
- Aedifica does not submit to ACTIS-CAMAC.
- Required items can be conditional in reality; this pilot marks high-signal phase-33 blockers explicitly so
  they cannot disappear from the handoff.
