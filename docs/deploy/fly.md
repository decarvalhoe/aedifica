# Déploiement Fly.io — `aedifica-demo`

Démo Aedifica en ligne sur **https://aedifica-demo.fly.dev/workspace**.

Un seul VM, image multi-stage : FastAPI (port interne 8090) + Next.js (port 3000
exposé). SQLite persisté sur volume Fly. Auto-stop en idle, auto-start à la
requête. Conçu pour le free-tier (1 vCPU partagé, 512 Mo RAM, 1 Go de volume).

## Fichiers

- `Dockerfile.fly` — image multi-stage. Stage 1 build le bundle Next.js
  (node:20-alpine). Stage 2 (python:3.12-slim) embarque Python + Node 20 runtime
  + le package `aedifica` + le bundle web.
- `fly.toml` — config Fly. Volume `aedifica_data` monté à `/data`, port interne
  3000, force HTTPS, auto-stop.
- `scripts/fly-entrypoint.sh` — PID 1. Applique les migrations Alembic puis
  démarre uvicorn en arrière-plan (loopback) puis Next.js au premier plan.
- `scripts/seed-demo.sh` — script idempotent-ish pour seeder une démo (org +
  projet + checklist seedée + intervenants invités).

## Premier déploiement

```bash
flyctl auth login
flyctl apps create aedifica-demo --org personal
flyctl volumes create aedifica_data --app aedifica-demo --region cdg --size 1 --yes
flyctl deploy --remote-only --app aedifica-demo
bash scripts/seed-demo.sh https://aedifica-demo.fly.dev
```

Le script imprime à la fin :
- les identifiants architecte (`demo@aedifica.ch` / `demo123`)
- un code d'invitation client (MO) — à utiliser dans le mode *« J'ai reçu un
  code d'invitation »* du login
- un code d'invitation mandataire (ingénieur civil) — idem

## Itération

```bash
# Re-déployer (sans toucher au volume)
flyctl deploy --remote-only --app aedifica-demo

# Voir les logs en direct
flyctl logs --app aedifica-demo

# Shell dans la machine
flyctl ssh console --app aedifica-demo

# Repartir d'une DB vierge
flyctl ssh console --app aedifica-demo -C "rm /data/aedifica.db"
flyctl machine restart --app aedifica-demo
bash scripts/seed-demo.sh https://aedifica-demo.fly.dev

# Forcer l'extinction (au-delà de l'auto-stop)
flyctl scale count 0 --app aedifica-demo

# Suppression complète (free up free-tier slot)
flyctl apps destroy aedifica-demo
```

## Notes

- L'avertissement Fly *« The app is not listening on the expected address »* au
  premier `deploy` est un faux positif : Fly scanne les ports avant que
  l'entrypoint ait fini de démarrer Next.js (les migrations + le warmup de l'API
  prennent ~5 s). Le déploiement est en fait sain — vérifiez les logs.
- `AEDIFICA_DATABASE_URL` est embarqué dans `[env]` car ce n'est pas un secret
  (juste un chemin local). Si vous passez à Postgres managé, déplacez-le dans
  les Fly Secrets : `flyctl secrets set AEDIFICA_DATABASE_URL=...`.
- Le free-tier n'inclut PAS d'IP IPv4 dédiée. Le shared IPv4 (`66.241.125.113`
  ici) est partagé entre les apps Fly ; le hostname `*.fly.dev` reste stable.
