# Wave 4 backlog — action layer & agentic orchestration in the runtime

> Status: proposed 2026-06-02 (owner: **option B**, see
> `../review/direction-alignment.md`). Re-balances the product away from "more
> regulatory CRUD/surfaces" toward the **north-star center**: the universal
> multi-software **action loop**, **project memory**, and a **per-phase next-step**
> orchestrator — exposed in the product runtime, not left as engine contracts.
> Milestone: **W4 Action Layer & Agent**.

## Why

W1/W3 productized the bottom-up regulatory wedge + substrate. The top-down half —
the action loop (`inspect → intent → dry-run diff → scoped approval → ledger`, the
**D-006 lead proof**) and the agentic per-phase orchestration + memory — exists as
engine contracts (E27/E28) but is **absent from the product**. W4 closes that gap.
**No new pure-CRUD/regulatory surfaces in this wave.**

## Epics

| Epic | Outcome |
|---|---|
| **AED-E35** Action loop in the runtime | The agent→software loop runs through the product API/UI: capability discovery → dry-run diff → scoped approval → ledger, persisted; the cockpit's agent→Archicad surface becomes a product surface. |
| **AED-E36** Memory & per-phase orchestration | Project memory/ledger is queryable in the product; a first "next step per SIA phase" orchestrator answers the north-star questions, sourced. |

## W4 issues

### AED-E35 — Action loop in the runtime
| # | P | Title | Definition of Done |
|---|---|---|---|
| W4-1 | P0 | Persist ledger + scoped approvals via API | `ledger_writer`/`approval`/`adapter_evidence` write to the `LedgerEntry`/`Approval` tables; `GET /projects/{id}/ledger`, `POST …/approvals` (scoped); a report/dry-run leaves a ledger row. |
| W4-2 | P0 | Adapter capability + dry-run endpoint | Expose `adapter_capability` manifests + `adapter_transaction` dry-run + `export_intent`; `POST …/adapter/dry-run` returns the plan, before/after diff and capability gaps; **no mutation**. |
| W4-3 | P0 | Scoped approval + execution gate | Execution stays blocked without an `adapter_execution` approval; dry-run/approve/execute each append a ledger row; report approval never authorizes adapter mutation (enforced in the runtime). |
| W4-4 | P1 | Web "Actions / Modèle" surface | Pull the cockpit agent→Archicad loop into the product: capabilities → dry-run diff → approval-gated → ledger, rendered with Datum. |

### AED-E36 — Memory & per-phase orchestration
| # | P | Title | Definition of Done |
|---|---|---|---|
| W4-5 | P0 | Memory & ledger query endpoints | `GET …/memory/open-decisions | unknowns | changes | source/{id}` over the persisted records (productize `validate_memory.answer_query`); each answer carries source/evidence refs. |
| W4-6 | P0 | Per-phase "next step" orchestrator | `GET …/next-step?phase=` composes brief unknowns + permit blockers + open decisions + freshness warnings into sourced recommended actions (the north-star Q&A); never invents, marks unknowns. |
| W4-7 | P1 | Web "Mémoire" + "Prochaine étape" surfaces | Tabs rendering the memory queries and the next-step orchestration with Datum trust states. |

## Guardrails (carried)

Sourced-or-unknown; **every mutation = dry-run → execution-scope approval →
ledger**; redactable client/model data; offline engine + product suites green in
CI. Archicad is the first adapter, not the identity — the action API stays
adapter-neutral.
