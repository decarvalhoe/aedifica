# Deployment (W3 / AED-137)

> Status: scaffolding. The product runs as three containers: Postgres + FastAPI
> API + Next.js web. Config is 12-factor (all via env, see `aedifica/api/config.py`).

## Local full stack (Docker)

```bash
docker compose up --build
# API  -> http://localhost:8090  (Postgres-backed, migrations applied on start)
# Web  -> http://localhost:3000
```

The API container runs `alembic upgrade head` then `uvicorn`. The web container
proxies `/api/*` to the `api` service (`AEDIFICA_API`).

## Environment

| Var | Default | Notes |
|---|---|---|
| `AEDIFICA_ENV` | `dev` | `prod` in containers |
| `AEDIFICA_DATABASE_URL` | `sqlite:///aedifica.db` | prod: `postgresql+psycopg://user:pw@host:5432/db` |
| `AEDIFICA_CORS_ORIGINS` | `http://localhost:3000` | comma-separated allowed origins |
| `AEDIFICA_CREATE_ALL` | unset | `1` to `create_all` instead of migrations (dev only) |
| `AEDIFICA_API` (web) | `http://127.0.0.1:8090` | API base the web app proxies to |

## Readiness / health

- `GET /api/health` — liveness (+ env).
- `GET /api/ready` — readiness; runs `SELECT 1`, returns 503 if the DB is down.

Wire these to the orchestrator's liveness/readiness probes.

## Migrations

```bash
AEDIFICA_DATABASE_URL=postgresql+psycopg://... alembic upgrade head
```

## CI/CD & hosting (next)

The repo CI already runs the offline engine + product test suites (`.github/
workflows/ci.yml`). A build-and-publish job (GHCR image) + the target host
(the team's Jelastic, or a container PaaS) are the remaining wiring — tracked on
the **W3 Product Hardening** epic (#172). Docker is not available in the current
build sandbox, so image builds are validated on a Docker host.
