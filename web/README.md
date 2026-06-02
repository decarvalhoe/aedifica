# Aedifica web app (Next.js + Datum)

The product web surface (ADR-0002, AED-127/#166). Next.js 14 app-router, styled
with the validated Datum design system (self-hosted Space Grotesk / IBM Plex Mono
in `public/fonts`, tokens + `ds-ts` components in `app/globals.css`). It loads
projects from the FastAPI product API; **no marketing page** — `/` goes straight
to `/workspace`.

## Run (two processes)

```bash
# 1) Product API (FastAPI) on :8090
cd ..   # repo root
pip install -e ".[product]"
AEDIFICA_CREATE_ALL=1 uvicorn aedifica.api.app:app --port 8090

# 2) Web app on :3000 (proxies /api/* to the API — override with AEDIFICA_API)
cd web
npm install
npm run dev
# open http://localhost:3000  ->  /workspace
```

## What the workspace does

1. **Créer une org démo** → bootstraps an org+owner and stores the bearer token.
2. **Créer le projet démo** → `POST /api/projects`.
3. **Ouvrir & générer le brief** → `POST /api/projects/{id}/intake` (offline
   fallback) then `GET /api/projects/{id}/claims` → renders claims with the Datum
   `ds-ts` trust pills (sourced / computed / unknown…).

## Build

```bash
npm run build   # type-checks + compiles (CI-ready)
```

`node_modules/`, `.next/` and `next-env.d.ts` are git-ignored; `package-lock.json`
is committed for reproducible installs.
