# Local workspace HTTP API (slice)

> Status: R1B slice. **Local-first, non-production.** No authentication. Do not
> expose to a network. Backed by offline fixture projects.

The API gives the UI and future agent flows a stable local surface instead of
importing pilot scripts directly. Routing logic lives in
`pilot/workspace_api.py::route_request` (socket-free, unit-testable); `serve`
wraps it in the stdlib `http.server`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Liveness: `{"status":"ok","api_version":"1.0"}` |
| `GET` | `/api/projects` | List project ids under the root |
| `GET` | `/api/projects/<id>` | Open + validate a project (id, route, phase, artifacts) |
| `POST` | `/api/projects` | Create a project (JSON: `project_id`, `name`, opt. `country/canton/commune/phase`) |
| `POST` | `/api/projects/<id>/brief` | Generate the parcel brief + report, return a summary |

Errors are structured: `{"error": {"code", "message", "details"}}` with the
appropriate HTTP status (400 invalid input, 404 unknown project/route).

## Startup

```bash
# Serve the bundled fixture projects (read/brief only is safe; create writes here)
python pilot/workspace_api.py --port 8088 --root pilot/projects

# Or serve a scratch root you can create into without touching the repo
python pilot/workspace_api.py --port 8088 --root .tmp_projects
```

## Smoke test

```bash
curl -s localhost:8088/api/health
curl -s localhost:8088/api/projects
curl -s localhost:8088/api/projects/DEMO-LAUSANNE-PALUD
curl -s -X POST localhost:8088/api/projects/DEMO-LAUSANNE-PALUD/brief
# create
curl -s -X POST localhost:8088/api/projects \
  -H 'content-type: application/json' \
  -d '{"project_id":"NEW-PROJECT-1","name":"New project","commune":"Lausanne"}'
```

Offline contract coverage: `python pilot/selfcheck.py` exercises `route_request`
for health, create, missing-field (400) and unknown-project (404) cases, the
brief endpoint against a fixture copy, and one live HTTP request through the
socket.
