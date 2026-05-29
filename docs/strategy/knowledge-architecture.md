# Knowledge Architecture — Composable Corpus, Selectors, and Project-as-Context

> Captures the owner's design intent (2026-05-29): **one composable knowledge base with per-project
> selectors**, a **capitalizable commune layer**, and **project knowledge as context-first (repo-like)** rather
> than always a pre-built RAG. This refines the NOMOS two-RAG idea and operationalizes the jurisdiction-pack
> architecture from [`challenge-and-brainstorm.md`](challenge-and-brainstorm.md) §E.

## The core idea: layered corpus + per-project regulatory route

Instead of building a separate RAG per project (expensive, redundant), maintain **one layered knowledge base**
where every layer coexists, and each project **activates only the layers it needs** via selectors:

```
                ┌───────────────────────────────────────────────┐
                │  GENERAL SWISS RAG  (reusable knowledge)        │
                │  SIA process, openBIM, CRB/NPK, office method   │
                └───────────────────────────────────────────────┘
   REGULATORY    ┌───────────────────────────────────────────────┐
   CORPUS        │  FEDERAL CORE  (always on)                      │
   (canonical,   │  LAT/RPG, OPB, LHand, AEAI frame, CO₂…          │
   versioned,    ├───────────────────────────────────────────────┤
   shared)       │  CANTON OVERLAY  (selectable)  ── e.g. VD       │
                 │  LATC/RLATC, cantonal energy, CAMAC procedure   │
                 ├───────────────────────────────────────────────┤
                 │  COMMUNE OVERLAY (selectable)  ── e.g. Lausanne │
                 │  PGA/RPGA, zones, indices, DS, plans de quartier│
                 └───────────────────────────────────────────────┘
                                  ▲
                                  │  per-project SELECTOR = "regulatory route"
                                  │  (Federal core) + (canton VD) + (commune Lausanne)
                 ┌────────────────┴──────────────────────────────┐
                 │  PROJECT KNOWLEDGE  (per project)               │
                 │  small project → CONTEXT (repo-like, see below) │
                 │  large project → dedicated project RAG/DB       │
                 └────────────────────────────────────────────────┘
```

**The selector ("regulatory route").** A project declares its jurisdiction once (parcel → commune → canton);
the engine activates **only** `Federal core + that canton + that commune`. Everything else stays dormant. This
keeps the *active* rule-set minimal and avoids mixing contradictory communal rules — retrieval is **scoped at
query time over a layered corpus**, not rebuilt as N separate RAGs.

> This *is* the jurisdiction-pack mechanism made concrete: a **pack = a corpus layer**; the **selector =
> per-project pack activation**. Internationalization later = add a federal/canton/commune layer set for another
> country; the selector logic is unchanged.

## The commune layer is a capitalizable, refreshable asset

- A commune's règlement (e.g. Ville de Lausanne) is **ingested once**, canonicalized, **versioned**, and
  **shared across all projects** in that commune. An architect works wherever they find work, so this corpus
  compounds in value across the practice.
- It is not rebuilt per project — it only needs a **refresh when the commune changes its plan/règlement**
  (event-driven, see [`swiss-regulatory-stack.md`](swiss-regulatory-stack.md) on volatility). "Refresh to stay
  canonical" rather than "rebuild".
- **Hybrid cold-start** (confirmed decision): on-demand ingestion of any commune *plus* a **robust seed corpus**
  for the pilot — **Federal + Canton de Vaud + Ville de Lausanne** — giving a real, demonstrable 3-level slice
  even while coverage is thin elsewhere. Lausanne is a deliberately *particular* commune, so it stress-tests the
  model early.

## Project knowledge: context-first, RAG only when it pays

Two regimes, chosen on **economics**, not dogma:

| Project size | Regime | Rationale |
|---|---|---|
| **Small** | **Context-first (repo-like)** — the agent "lives in" the project folder and reasons over its files directly, like a coding agent in a Git working directory. No heavy pre-built index. | Cheap, simple, immediate; indexing overhead isn't justified for a villa/transformation. |
| **Large** | **Dedicated project RAG/DB** — a real indexed memory across many documents, versions, consultants. | Volume justifies the cost; cross-document retrieval becomes essential. |

**Decision (#25):** small projects default to **context-first**. The agent "lives in" the project folder and
uses files + manifest + decision ledger directly. Escalate only when the economics justify it:

- `hybrid_index` when one medium threshold is crossed and the same information is queried repeatedly;
- `project_rag_db` when at least two large thresholds are crossed, or public procurement / formal BIM governance
  requires persistent evidence.

The validated threshold model lives in
[`../architecture/project-knowledge-regime.md`](../architecture/project-knowledge-regime.md) and
`pilot/research/project_knowledge_regime.json`.

## Two-RAG model, restated with this refinement

The original NOMOS "project RAG vs general RAG" split holds, now sharpened into **three corpus families** plus a
project regime:

1. **General Swiss RAG** — reusable, non-project knowledge (SIA, openBIM, CRB, method). Always available.
2. **Regulatory corpus** — the layered Federal/Canton/Commune stack, **canonical + versioned + shared**, queried
   through the per-project selector.
3. **Project knowledge** — **context-first for small, RAG for large** (above).

The engine must **never silently mix** project-specific facts with general/regulatory knowledge: project facts
win for the project; regulatory facts are authoritative for compliance; general knowledge guides structure and
checklists. (Carries forward NOMOS Archi's separation rule.)

## Why this matters for the build

- **Cheaper & faster**: no per-project corpus rebuild; reuse the shared regulatory + general layers.
- **Canonical & safe**: versioned commune layers with refresh = traceable, current, citable (feeds the trust
  contract in [`challenge-and-brainstorm.md`](challenge-and-brainstorm.md) §B8).
- **Scales to the practice**: every commune ingested makes the next project in that commune instant.
- **Internationalizable**: same layered-corpus + selector machinery, new country = new layers.

## Implications for the issue set

- New issue: **"Composable regulatory corpus + per-project selector ('regulatory route')"** — the retrieval
  architecture above.
- New issue: **"Seed 3-level pilot corpus: Federal + Vaud + Ville de Lausanne"** (the hybrid cold-start seed).
- Reframe #7 (RAG project + RAG général) to the **three-corpus + project-regime** model here.
- #25 is now the **project knowledge regime** decision: context-first by default for small projects, with
  validated thresholds for hybrid index and project RAG/DB escalation.
