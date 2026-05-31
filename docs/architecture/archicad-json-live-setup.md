# Archicad JSON Live Setup

Status: R4 live-adapter setup note, 2026-05-31.

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
| First command to verify | `GetProductInfo` |
| Aedifica adapter id | `archicad_json` |
| First safe operation | non-mutating health/product-info probe |
| Second safe operation | non-mutating selected-element inspection |
| First dry-run operation | selected-space metadata update plan |

## Manual Smoke Commands

When Archicad is open and the JSON interface is available, test the port range before any model operation:

```powershell
python pilot/agent_software_demo.py
python pilot/agent_software_demo.py --json
```

The current command stays in fixture mode. The live implementation should add an endpoint option such as:

```powershell
python pilot/agent_software_demo.py --endpoint http://localhost:19723
```

## Failure Modes

- Archicad not running: report adapter unavailable and keep fixture mode.
- JSON port not listening: scan or ask for the configured port.
- `GetProductInfo` fails: block live mode and preserve fixture fallback.
- Selection is empty: report a human action, such as "select one zone/space and rerun".
- Capability missing: mark planned item unsupported.
- Approval missing: allow dry-run output, block execution.

## Live Acceptance

The first live issue is not complete until the bridge can:

1. connect to a running Archicad JSON endpoint;
2. return product/version information;
3. normalize selected elements to the same shape as `pilot/model/archicad_selection_fixture.json`;
4. produce the same before/after dry-run diff as fixture mode;
5. leave execution blocked unless the ledger contains a matching approval.
