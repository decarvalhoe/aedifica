# Wave 2 backlog — multi-project product (AED-124+)

> Status: proposed 2026-06-02, after the AED-001→AED-123 contract waves closed.
> Implements [ADR-0002](../architecture/adr-0002-product-architecture.md):
> a deployed multi-tenant web app (FastAPI + Next.js, SQL, on-demand communes).
> Milestones: **W1 Product Foundation → W2 Partner Pilot → W3 Product Hardening**.

## Epics

| Epic | Milestone | Priority | Outcome |
|---|---|---|---|
| **AED-E32** Live & Persistent Foundation | W1 | P0 | The engine becomes a real multi-project web app on SQL, with on-demand communes. |
| **AED-E33** Partner Pilot & Live Adapters | W2 | P1 | A real partner project runs end-to-end on live data; #105/#115 unblocked. |
| **AED-E34** Product Hardening & Deploy | W3 | P1 | Auth, security, deployment and scale make it shippable. |

## W1 — AED-E32 Live & Persistent Foundation

| Issue | P | Title | Definition of Done |
|---|---|---|---|
| AED-124 | P0 | SQL data model + first migration | SQLAlchemy models (Org, User, Project, Source, Evidence, Claim, Report, LedgerEntry, Approval, RegulatoryRoute, CommunePack, IngestionJob) + Alembic baseline applying on SQLite; the trust invariant (a `sourced` regulatory claim requires evidence) is enforced by a DB constraint/guard; model tests. |
| AED-125 | P0 | Persistence repositories over the engine | Repositories mirror the current file writers (project/source/evidence/claim/report/ledger); a project round-trips through the DB store with identical trust states; offline engine contract preserved. |
| AED-126 | P0 | FastAPI product API | Projects CRUD + generate brief/permit/memory endpoints over engine+DB; structured errors; OpenAPI schema; contract tests against SQLite. |
| AED-127 | P1 | Next.js app + Datum component library | Datum tokens/CSS/fonts packaged as a component lib; workspace shell + claim review as React components; app loads a project from the API; no marketing page before the working surface. |
| AED-128 | P0 | Multi-tenant + capability access | Org/User + auth; projects scoped per org; capability checks gate mutations (reuse the vNext pattern); a user never sees another org's projects. |
| AED-129 | P0 | On-demand commune ingestion service | Choose/add any commune at runtime → fetch official sources → ingest → version → `CommunePack`; states seed→ingested→supported; freshness + provenance; **no fabricated values**; static packs become seed data only. |
| AED-130 | P1 | Live parcel pipeline end-to-end | Address/EGRID → live OEREB → **persisted** project + sourced brief + evidence (productizes the cockpit live path into the app). |
| AED-131 | P0 | CI parity gate | Offline engine selfcheck + contract validators stay green AND a new DB/API suite runs; migration check in CI. |

## W2 — AED-E33 Partner Pilot & Live Adapters

| Issue | P | Title | Definition of Done |
|---|---|---|---|
| AED-132 | P1 | Ingest the partner's commune (real sources) | The partner office's commune is ingested via the on-demand service, versioned and supported. |
| AED-133 | P1 | Real partner project end-to-end | One real project: intake → brief → permit readiness → memory, on live data, reviewed by the architect. |
| AED-134 | P1 | Live Archicad bridge (unblocks #105/#115) | The live JSON bridge runs against the partner Archicad seat via `archicad_harness.py`; before/after dry-run evidence captured; mutation still approval-gated. |
| AED-135 | P2 | Partner feedback → backlog | Feedback captured with the partner template becomes labelled AED-136+ issues. |

## W3 — AED-E34 Product Hardening & Deploy

| Issue | P | Title | Definition of Done |
|---|---|---|---|
| AED-136 | P1 | Auth, security & privacy hardening | Tenant isolation, secrets management, redaction enforced in the product path, no client data leaves the tenant. |
| AED-137 | P1 | Deployment (container + CI/CD) | Dockerized API + web, CI/CD pipeline, a hosted environment; the cockpit demo is superseded by the real app. |
| AED-138 | P2 | Observability & audit surface | Ledger/audit surfaced in-app; structured logs + error tracking. |
| AED-139 | P2 | Pack cache & query performance | Shared commune-pack cache across projects; query/index performance for multi-project orgs. |

## Guardrails (unchanged)

The engine's non-negotiables hold in the product: sourced-or-unknown (never
invented), dry-run→approval→ledger for mutations, redactable client/model data,
and a green offline engine backbone in CI.
