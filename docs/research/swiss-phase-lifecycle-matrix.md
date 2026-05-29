# Swiss Phase Lifecycle Matrix

This is the implementation-facing answer to issue #1. It turns the Swiss/SIA-oriented lifecycle into a
validated Aedifica research asset:

- structured file: `pilot/research/swiss_phase_lifecycle_matrix.json`;
- validator: `pilot/validate_research.py`;
- CI coverage through the pilot smoke suite.

The matrix uses the SIA phase backbone as Swiss practice context and adds Aedifica phase `0` for pre-SIA
project intake, because parcel, source, and feasibility decisions often happen before formal deliverables.

## Source Position

The file stores SIA references as metadata anchors only. SIA standards are paid/protected professional
documents; production mappings must be checked against the office's licensed copy.

Useful public anchors:

- SIA 102:2020 product page: <https://shop.sia.ch/normenwerk/architekt/102_2020_f/F/Product/>
- SIA 112:2014 public appendix anchor: <https://www.shop.sia.ch/bfe9decc-d1eb-4d73-8834-8e4c55cbc06d/F/DownloadAnhang>

## Phase Coverage

The validated phase set is:

| Phase | Meaning in Aedifica |
|---|---|
| `0` | Intake pre-SIA: parcel, programme, route reglementaire, unknowns. |
| `1` | Strategic planning. |
| `2` | Preliminary studies and variants. |
| `31` | Avant-projet. |
| `32` | Projet de l'ouvrage. |
| `33` | Autorisation / mise a l'enquete. |
| `41` | Appel d'offres. |
| `51` | Projet d'execution. |
| `52` | Execution de l'ouvrage. |
| `53` | Mise en service and closure. |
| `61-63` | Operation, conservation, transformation. |

Each phase row must include activities, actors, decisions, deliverables, risks, source inputs, Aedifica outputs,
and variants for small, medium, and large projects.

## Critical Reading

The important correction is that Aedifica should not treat the SIA sequence as a linear checklist. The product
value comes from phase-aware carryover:

- a phase `0` parcel unknown can become a phase `33` permit blocker;
- a phase `33` authority condition can become a phase `51` drawing constraint and a phase `52` site check;
- a phase `53` handover document becomes phase `61-63` memory for future work.

This is why the lifecycle matrix is paired with the constraint matrix contract in
[`../nomos/phase-aware-constraint-matrix.md`](../nomos/phase-aware-constraint-matrix.md). The phase matrix says
what the architect is doing; the constraint matrix says which claims must be carried forward, when, and with
what evidence.

## Validation

```bash
python pilot/validate_research.py
python pilot/selfcheck.py
```

The validator fails if:

- a required phase is missing;
- a phase has no activities, actors, decisions, deliverables, or risks;
- small/medium/large variants are incomplete;
- the pilot source registry does not cover all required source tiers.
