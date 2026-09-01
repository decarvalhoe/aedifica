# Archicad JSON Live Setup

Status: read-only connector implemented; real-seat acceptance pending #105 / #115.

## Test harness command (no mutation)

One repeatable command runs product info, selection read, missing-metadata audit
and a dry-run diff against the bridge — never mutating the model:

```bash
# Against a running Archicad JSON bridge (or the fixture replay server)
python pilot/archicad_harness.py --endpoint http://127.0.0.1:19723
python pilot/archicad_harness.py --endpoint http://127.0.0.1:8077 --json

# Offline fixture mode (no endpoint)
python pilot/archicad_harness.py

# Deterministic replay server for CI / local testing (no Archicad seat, no network)
python pilot/replay_server.py --port 8077
```

The harness exits non-zero with an actionable message when the endpoint is
unavailable (use `--no-fallback` to fail instead of using fixtures), and returns
a redacted transcript. Live acceptance stays blocked by `#105` / `#115` until a
partner Archicad seat is available.

## Runtime topology

`archicad_harness.py` contacts the endpoint from the machine where the command runs.
The product UI sends the endpoint to FastAPI, which means the **API process** must be
able to reach it. A Fly-hosted API cannot reach `localhost` on an architect's
workstation. For a private local bridge, use the harness directly or run the Aedifica
API locally. Do not expose the bridge publicly just to make the hosted demo reach it.

## Purpose

This document is the handoff from the R1A fixture demo to a live partner-office Archicad JSON bridge.

Official references:

- Graphisoft Archicad JSON Interface: `https://archicadapi.graphisoft.com/JSONInterfaceDocumentation/`
- Graphisoft Python wrapper docs: `https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.html`

## Expected Local Setup

| Item | Expected value |
|---|---|
| Host | `localhost` |
| Port range | `19723-19743` |
| First command to verify | `API.GetProductInfo` |
| Aedifica adapter id | `archicad_json` |
| First safe operation | non-mutating health/product-info probe |
| Second safe operation | non-mutating selected-element inspection |
| First dry-run operation | selected-space metadata update plan |

## Manual Smoke Commands

When Archicad is open and the JSON interface is available, test the port range before any model operation:

```powershell
python pilot/archicad_harness.py
python pilot/archicad_harness.py --json
```

The command accepts a live endpoint:

```powershell
python pilot/archicad_harness.py --endpoint http://localhost:19723 --no-fallback
```

Without `--no-fallback`, an unavailable endpoint falls back to fixtures. Use that
fallback only to rehearse the flow; keep `--no-fallback` for partner acceptance.

## Failure Modes

- Archicad not running: report adapter unavailable and keep fixture mode.
- JSON port not listening: scan or ask for the configured port.
- `API.GetProductInfo` fails: block live mode and preserve fixture fallback.
- Selection is empty: report a human action, such as "select one zone/space and rerun".
- Capability missing: mark planned item unsupported.
- Approval missing: allow the preview, block the traced simulation; live mutation is unavailable.

## Live Acceptance

The first live issue is not complete until the bridge can:

1. connect to a running Archicad JSON endpoint;
2. return product/version information;
3. normalize selected elements to the same shape as `pilot/model/archicad_selection_fixture.json`;
4. produce the same before/after dry-run diff as fixture mode;
5. report `mutated=false`; live mutation is not part of #105 / #115.
