# Deploy runbook — Aedifica product stack

The product is a three-service stack — **Postgres + FastAPI API + Next.js web** —
defined in [`docker-compose.yml`](../../docker-compose.yml). Images publish to
GHCR via [`.github/workflows/release.yml`](../../.github/workflows/release.yml).

## Prerequisites
- Docker + Docker Compose v2.
- Production: a host with Docker, a Postgres (managed or the compose `db`), and a
  reverse proxy / TLS terminator in front of the `web` service.

## Environment variables
| Var | Service | Purpose | Example |
|---|---|---|---|
| `AEDIFICA_ENV` | api | environment label | `prod` |
| `AEDIFICA_DATABASE_URL` | api | SQLAlchemy URL | `postgresql+psycopg://aedifica:…@db:5432/aedifica` |
| `AEDIFICA_CORS_ORIGINS` | api | allowed web origins (comma-separated) | `https://app.example.com` |
| `AEDIFICA_CREATE_ALL` | api | **dev only** — auto-create tables. **Do not set in prod** (use Alembic). | _(unset)_ |
| `AEDIFICA_API` | web | API base URL the request-time proxy forwards to — **no `/api` suffix** | `http://api:8090` |

## Local bring-up
```bash
docker compose up --build
#   db   → 5432 (internal)
#   api  → http://localhost:8090   (runs `alembic upgrade head` then uvicorn)
#   web  → http://localhost:3000   → open /workspace
```

## Migrations
- Schema is owned by **Alembic** (`aedifica/db/migrations`). The API image runs
  `alembic upgrade head` at boot.
- **Never** set `AEDIFICA_CREATE_ALL=1` in production — it bypasses migrations.
- Manual: `AEDIFICA_DATABASE_URL=… python -m alembic upgrade head`.

## Health / readiness
- Liveness: `GET /api/health` → `{ "status": "ok" }`.
- Readiness: `GET /api/ready` → `SELECT 1` (503 if the DB is down).
- The web proxies `/api/*` to `AEDIFICA_API` **at request time** (`force-dynamic`),
  so a single web image works across environments.

## Production images (GHCR)
- `release.yml` builds + pushes `…/aedifica-api` and `…/aedifica-web` on `main`/tags.
- Run them against a managed Postgres; set `AEDIFICA_DATABASE_URL`,
  `AEDIFICA_CORS_ORIGINS`, and (web) `AEDIFICA_API`.

## First-run smoke (manual)
1. `/workspace` → **Créer un atelier** → keep the access key.
2. Open the seeded reference project → **Vue d'ensemble**.
3. **Copilote IA** → Demander un aperçu → Valider → Appliquer → check the journal.

(Automated equivalent: the Playwright E2E `web/e2e/*.spec.ts`, run by the CI
`e2e` job and reproducible with `PLAYWRIGHT_BASE_URL=… npm run e2e`.)

## Troubleshooting (lessons from setup)
- **web `ECONNREFUSED` / 404 on `/api/…`** — `AEDIFICA_API` must be the API **base**
  (`http://api:8090`), *without* a trailing `/api`. The proxy appends `/api/`; a
  trailing `/api` produces `/api/api/…` → 404.
- **api boot fails** — check `AEDIFICA_DATABASE_URL` reachability and that
  `alembic upgrade head` applies the full chain.
- **web image build fails on `npm ci`** — requires `web/package-lock.json`
  (committed). Regenerate with `npm install --package-lock-only`.
- **stale schema after an upgrade** — a dev SQLite file created with
  `AEDIFICA_CREATE_ALL` won't gain new columns; delete it or run Alembic.

## Notes
- The default Postgres credentials in `docker-compose.yml` are **local-only** —
  override them in production.
