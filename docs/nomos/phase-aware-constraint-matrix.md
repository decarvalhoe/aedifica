# Phase-Aware Constraint Matrix

The phase-aware constraint matrix is the handoff format between Aedifica's regulatory intake, NOMOS canonical
units, permit-readiness work, and later execution tracking.

It answers four questions for each constraint:

1. What claim or unknown matters?
2. Which source, assumption, or conflict supports it?
3. In which SIA phase does it matter?
4. What action must the architect or system take at that phase?

## Files

- Pilot matrix: `pilot/constraints/mvp1_lausanne_matrix.json`
- Validator: `pilot/validate_matrix.py`
- Human-readable schema: `pilot/schemas/constraint-matrix.schema.json`

## Matrix Header

```json
{
  "matrix_version": "1.0",
  "matrix_id": "MATRIX-CH-VD-LAUSANNE-MVP1",
  "title": "MVP1 phase-aware constraint matrix for Lausanne/VD parcel intake",
  "phase_model": {
    "source": "SIA 112:2014 / SIA 102 practice, with pre-SIA intake phase 0",
    "jurisdiction_pack": "CH"
  }
}
```

`phase_model` is pack-owned, not engine-owned. The Swiss pack can use SIA codes; another country can provide a
different phase model without changing the matrix contract.

## Constraint Row

```json
{
  "constraint_id": "ALIGNMENT-LIMIT",
  "title": "Construction alignment is present and must be confirmed before design commitment",
  "domain": "roads_alignments",
  "claim_state": "sourced",
  "owner": "Architect / surveyor when mandated",
  "verification": "api_check",
  "outputs": ["alignment_flag", "survey_request"],
  "source_refs": [
    {
      "source_id": "VD-OEREB",
      "locator": "Limite des constructions definie par un plan approuve",
      "valid_as_of": "2026-05-29",
      "confidence": "high"
    }
  ],
  "phase_applicability": [
    {
      "phase_code": "21",
      "relevance": "blocker",
      "action": "Confirm precise line before relying on envelope."
    },
    {
      "phase_code": "52",
      "relevance": "check",
      "action": "Use confirmed setting-out data before site execution."
    }
  ]
}
```

## Claim State

The matrix reuses the trust contract states:

| State | Use |
| --- | --- |
| `sourced` | Source-backed fact or requirement. |
| `computed` | Calculated from sourced inputs. |
| `assumption` | Useful but not yet proven. |
| `unknown` | Missing data that must stay visible. |
| `conflict` | Active sources or interpretations disagree. |
| `decision` | Human-approved choice. |

`sourced` and `computed` rows require `source_refs`. `assumption` and `unknown` rows may omit them but must
make their required action explicit.

## Phase Relevance

| Relevance | Meaning |
| --- | --- |
| `inform` | Include in briefs and awareness lists. |
| `check` | Verify at this phase before proceeding. |
| `blocker` | Cannot make the next commitment without resolving it. |
| `deliverable` | Must appear in an output package. |
| `handoff` | Must be carried into the next phase or actor boundary. |

This is deliberately more precise than a boolean phase tag. A fire rule, servitude, or alignment may exist
from day one, but the action differs between feasibility, permit, tendering, and site execution.

## Validation

```bash
python pilot/validate_matrix.py
python pilot/selfcheck.py
```

CI runs both commands. The selfcheck asserts that the pilot matrix covers phase `33` and downstream phases
`41` and `52`, so the matrix cannot collapse back into a narrow intake-only checklist.

## Relationship To Other Contracts

- NOMOS schema v0 defines canonical units and source refs.
- The trust contract defines claim states and ledger rules.
- The jurisdiction-pack contract defines source versioning.
- The matrix ties those contracts to phase-specific actions.

The matrix is the practical bridge from "we know a constraint exists" to "what does the architect need to do
with it, when, and with what evidence?"
