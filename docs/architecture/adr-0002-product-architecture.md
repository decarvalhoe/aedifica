# ADR-0002 — Product runtime architecture (delivery substrate for the ArchiOS layer)

> Status: **accepted 2026-06-02; reframed 2026-06-02 (owner: option B)** after the
> direction-alignment check (`../review/direction-alignment.md`). The stdlib engine
> + validators remain the **test backbone**.

## Product center — what this ADR is and is NOT (correction 2026-06-02)

This ADR describes the **delivery substrate** (how the product runs), **not the
product definition**. Per `../product/scope-realignment.md` and `strategy/
decisions.md` (D-001, D-005, **D-006**), the product **is the ArchiOS operating
layer**:

1. a **neutral engine + canonical project memory** (bottom-up), and
2. a **universal multi-software action API + agentic per-phase orchestration**
   (top-down) — `inspect → generate intent → dry-run diff → scoped approval →
   ledger`, across Archicad/IFC/Speckle/… adapters.

The web app, SQL and Docker below are **the runtime that carries that layer** —
they must not redefine the product as a "regulatory workspace SaaS." Guardrail:
the regulatory wedge is one lane; the action loop + memory + next-step
orchestration are first-class and must be exposed in the runtime, not left as
engine contracts (this is the re-balance decided as option B).

## Context

The AED-001→AED-123 waves delivered the full R0→R6 behavior as **offline
contracts + fixtures** (engine in `pilot/` + the `aedifica/` package, 261 green
checks). That backlog is exhausted; only #105/#115 (live partner Archicad) stay
blocked. The owner has set the next phase: a **final multi-project product
vision**, not more static fixtures.

## Decision (runtime substrate)

Run the ArchiOS layer as a **deployed, multi-tenant web application** (this is the
substrate, per the correction above — not the product's identity).

| Concern | Decision | Why |
|---|---|---|
| **App shape** | Web app, deployed (dev-local first, then hosted). Not desktop. | Multi-user, multi-project, one deploy; shared commune-pack cache across all projects. |
| **Backend** | **FastAPI** (Python). Wraps the existing `aedifica` engine — no rewrite. | The whole trust/route/permit/memory/adapter logic is already Python and tested. |
| **Frontend** | **Next.js 14** + the **Datum design system** turned into a real component library (`docs/design-system` tokens/CSS/fonts). | Matches the team's stack; the cockpit already proves Datum-in-the-browser. |
| **Persistence** | **SQL** — SQLite in dev, **Postgres** in prod (SQLAlchemy + Alembic). | The owner chose SQL; replaces `files + manifest`. Scales to multi-tenant + queries. |
| **Communes** | **On-demand ingestion** — choose/add any commune at runtime; pack fetched, ingested, versioned, cached. No hardcoded Lausanne/Pully. | Owner direction; matches the D-003 "hybrid cold-start" strategy. |
| **Tenancy** | `Org → Users → Projects`, **capability-based access** (reuse the RBOK vNext pattern). | Real product needs auth + per-project scoping. |
| **Engine** | Stays neutral and offline-testable; the API/DB are adapters over it. | Keeps the 261-check backbone green; no regression of the trust contract. |

## Target data model (first cut)

```
Org 1─* User
Org 1─* Project
Project 1─* Source 1─* Evidence (hashed)
Project 1─* Claim   (state: sourced|computed|assumption|unknown|conflict|decision)
Project 1─* Report  (content_sha256, source_refs)
Project 1─* LedgerEntry 1─0..1 Approval (scoped)
Project *─1 RegulatoryRoute *─* CommunePack (shared, versioned, freshness)
CommunePack 1─* IngestionJob (on-demand, status, sources, valid_as_of)
```

The trust contract is enforced at the model layer: a `sourced` regulatory claim
without an `Evidence`/`Source` row cannot persist as `sourced`.

## Non-negotiables (carried from the engine)

1. Every regulatory fact is `sourced` (with evidence) or explicitly `unknown` —
   never invented. Enforced in the DB layer, not just the renderer.
2. Adapter mutations: dry-run → **execution-scope approval** → ledger. No mutation
   without an approval row.
3. Privacy: client/model data redactable before any share; evidence stays tenant-scoped.
4. The offline engine + `pilot/selfcheck.py` + contract validators stay green in CI.

## Consequences

- New top-level surfaces appear (`api/` FastAPI, `web/` Next.js, `db/` models +
  migrations) alongside the engine. The `pilot/` engine becomes the domain core.
- "Static packs" (`pilot/<commune>/rpga_zones.json`) become **seed data** for the
  ingestion pipeline, not the runtime source of truth.
- Delivery sequences as **Wave W1 (live & persistent) → W2 (partner pilot) → W3
  (product hardening & deploy)** — see `planning/wave-2-product-backlog.md`.

## Open (decide during W1)

- Auth provider (own JWT vs external IdP).
- Hosting target (the team's Jelastic, or a container PaaS).
- How deep the first on-demand ingestion is automated vs human-reviewed per commune.
