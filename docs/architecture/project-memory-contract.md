# Project Memory Contract

This is the first concrete contract for issue #31: one queryable memory that survives phase handoffs and keeps
provenance visible.

Files:

- fixture: `pilot/memory/demo_project_memory.json`;
- validator and query demo: `pilot/validate_memory.py`;
- knowledge-regime dependency: [`project-knowledge-regime.md`](project-knowledge-regime.md).

## Purpose

Aedifica project memory is not a generic chat transcript. It is a phase-aware evidence ledger that answers:

- What changed since a known version?
- Which source or evidence justifies a claim?
- What is still undecided before the next phase gate?
- Which permit, tender, or site obligation must carry forward?

## Record Contract

Every memory record has:

| Field | Meaning |
|---|---|
| `memory_id` | Stable project-local record ID. |
| `record_type` | Source evidence, decision, model version, change, correspondence, handoff, site issue, etc. |
| `phase_code` | SIA/Aedifica phase where the record was created or matters first. |
| `claim_state` | Trust state: sourced, decision, evidence, unknown, conflict, etc. |
| `status` | Active, approved, open, pending human review, closed. |
| `source_refs` | Source IDs, locators, valid-as-of dates, confidence. |
| `evidence_refs` | Project file/API/model/report references. |
| `links` | Other memory records that this record depends on or carries forward. |

## Demo Queries

The fixture proves three cross-phase queries:

| Query | Why it matters |
|---|---|
| `Q-CHANGES-SINCE-V3` | Finds phase `33` changes linked to model snapshot `v3`. |
| `Q-SOURCE-FIRE` | Returns phase `33` and phase `52` records justified by the same ECA/fire source. |
| `Q-UNDECIDED-BEFORE-PERMIT` | Lists open items before filing: energy review and fire evidence. |

These are not natural-language search tricks. Each answer must return record IDs with source/evidence refs.

## Relationship To Other Contracts

- The trust contract defines claim states and ledger discipline.
- The project knowledge regime decides whether the memory lives as context-first files, hybrid index, or RAG/DB.
- The phase lifecycle matrix defines where records belong.
- Permit and compliance contracts generate phase `33` records that must carry into tender and site phases.

## Validation

```bash
python pilot/validate_memory.py
python pilot/selfcheck.py
```

The validator fails if records lack source/evidence refs, if required record types are absent, or if the demo
queries do not return their expected provenance-backed records.
