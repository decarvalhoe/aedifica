#!/bin/bash
# Fly.io entrypoint — applies SQLite migrations, then runs FastAPI (background)
# and the Next.js server (foreground, PID 1). Next.js proxies /api/* to the API
# over the loopback (AEDIFICA_API). The DB persists on the mounted /data volume.
set -e

mkdir -p /data
cd /app
echo "[boot] applying migrations…"
alembic upgrade head

echo "[boot] starting FastAPI on 127.0.0.1:8090…"
uvicorn aedifica.api.app:app --host 127.0.0.1 --port 8090 --log-level warning &
API_PID=$!

# If the API dies, take the container down (Fly will restart).
trap 'kill -TERM ${API_PID} 2>/dev/null || true' EXIT

# Wait briefly for the API to become responsive (avoids 502 on first request).
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf http://127.0.0.1:8090/api/health > /dev/null 2>&1; then
    echo "[boot] API healthy."
    break
  fi
  sleep 1
done

cd /app/web
echo "[boot] starting Next.js on 0.0.0.0:${PORT:-3000}…"
exec npm run start -- -H 0.0.0.0 -p "${PORT:-3000}"
