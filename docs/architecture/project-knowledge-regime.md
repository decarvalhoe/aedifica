# Project Knowledge Regime

This closes issue #25: Aedifica needs a default regime for project knowledge and a threshold where the project
graduates from context-first work to indexed/RAG memory.

Structured decision file: `pilot/research/project_knowledge_regime.json`  
Validator: `pilot/validate_research.py`

## Decision

Small projects default to **context-first**.

The agent works in the project folder like a coding agent works in a repository: files remain the source of
truth, with an explicit context manifest, decision ledger, and targeted extraction. A project RAG/DB is not built
unless its cost is justified.

## Regimes

| Regime | Use | Storage | Retrieval |
|---|---|---|---|
| `context_first` | Small mandates, early intake, low volume. | Files + manifest + decision ledger. | Direct reads, file search, targeted extraction. |
| `hybrid_index` | Medium projects with repeated cross-document questions. | Files + selected metadata/index + ledger. | Selector first, then indexed snippets with file/hash refs. |
| `project_rag_db` | Large/multi-year/formal BIM/public projects. | Versioned evidence store + index/vector + graph + ledger. | Scoped RAG/DB with source hashes, versions, phases, actors. |

## Thresholds

Use context-first by default below these guideline values:

| Metric | Context-first guideline | Hybrid trigger | RAG/DB trigger |
|---|---:|---:|---:|
| Documents | <= 80 | > 80 | > 300 |
| Active participants | <= 8 | > 8 | > 20 |
| Duration | <= 6 months | > 6 months | > 12 months |
| Model snapshots | <= 3 | > 3 | > 10 |
| Total project data | <= 250 MB | > 250 MB | > 1 GB |

Escalate to `hybrid_index` when one hybrid threshold is crossed **and** the same information is queried
repeatedly. Escalate to `project_rag_db` when two RAG thresholds are crossed, or when public procurement,
formal BIM governance, or long-lived evidence obligations justify persistent memory.

## Critical Boundary

Do not let retrieval architecture blur source authority:

- regulatory facts come from the selected jurisdiction packs and source registry;
- project facts come from project documents and decisions;
- general/SIA/office knowledge guides structure and checks;
- every answer must preserve source IDs, claim state, and version.

This is the same trust boundary as
[`trust-contract-and-ledger.md`](trust-contract-and-ledger.md): project assumptions cannot become reusable
regulatory claims just because they were indexed.

## Review Gates

Re-evaluate the regime at:

- phase `0` intake;
- phase `31` before concept freeze;
- phase `33` before permit filing;
- phase `41` before tender;
- phase `52` before site start.

## Metrics To Collect

The thresholds are pilot defaults. Tune them with real office data:

- document count by phase;
- repeated cross-document questions;
- time spent finding latest document;
- active participant count;
- model snapshot count;
- stale or failed retrieval events.
