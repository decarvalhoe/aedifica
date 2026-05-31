# Permit dossier state machine

> Status: R2. Implemented in `pilot/permit_state.py`. **Aedifica is not an
> authority** — these states describe the architect's preparation, never an
> authority decision.

## States

| State | Meaning |
|---|---|
| `draft` | Dossier opened, evidence being assembled. |
| `missing_evidence` | One or more required evidence items still missing. |
| `ready_for_review` | No required blockers; awaiting architect review. |
| `architect_approved` | Architect reviewed and approved for submission. |
| `submitted_external` | Submitted to the authority (external, out of our hands). |

## Valid transitions

```
draft              -> missing_evidence | ready_for_review
missing_evidence   -> ready_for_review | draft
ready_for_review   -> architect_approved | missing_evidence
architect_approved -> submitted_external | ready_for_review
submitted_external -> ready_for_review
```

Any other transition raises `PermitStateError`. Each transition carries the human
action + evidence change that justifies it (`TRANSITION_ACTIONS`).

## Derivation

`derive_state(completeness, architect_approved=…, submitted=…)` computes the
state from a `validate_permit.completeness_report`: required blockers ⇒
`missing_evidence`; otherwise present evidence ⇒ `ready_for_review`. Human flags
move it to `architect_approved` / `submitted_external`.

## Non-authority scope

`ready_for_review` and `architect_approved` mean the architect's dossier looks
complete and approved **for submission** — they never mean the permit is granted.
The decision belongs to the competent authority (VD: ACTIS/CAMAC).
