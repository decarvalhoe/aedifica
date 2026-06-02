# Package boundaries — pilot → `aedifica` product package

> Status: accepted 2026-05-31 for the `AED-081`…`AED-123` implementation wave (R1B → R6).
> Scope note: this document defines **module boundaries and public contracts**. It does not
> change runtime behavior — the stdlib pilot keeps working and CI stays green.

## Why this exists

The pilot (`pilot/*.py`) proved the regulatory/workspace/adapter behavior as a set of scripts.
Product work (HTTP API, UI shell, durable ledger, multi-software adapters) needs **stable import
points** instead of importing scripts directly. We therefore introduce an `aedifica/` product
package that is the public namespace, while `pilot/` remains the stdlib implementation exercised
by `pilot/selfcheck.py` and the CI contract validators.

```
aedifica/        ← public product package (stable imports for API, UI, adapters)
  └─ re-exports + thin product services over …
pilot/           ← stdlib implementation + validators + selfcheck (CI source of truth)
```

The single coupling point is `aedifica/_bootstrap.py`, which puts `pilot/` on `sys.path`. As
logic matures it can migrate physically into `aedifica/` with `pilot/` shims, without changing the
public contract below.

## Boundaries

### 1. Domain (regulatory + envelope + parcel)
- **Owner of:** OEREB parsing, communal zone matching, envelope math, structured domain errors.
- **Implementation:** `pilot/domain.py`, `pilot/oereb.py`, `pilot/parcel_intake.py`.
- **Public surface:** `aedifica.domain` →
  `calculate_envelope`, `parse_oereb_extract`, `load_commune_ruleset`, `match_communal_zone`,
  `polygon_area_m2`, `AedificaDomainError` (+ subclasses).
- **Non-goals:** no rendering, no file IO beyond reading ingested packs, no network.

### 2. Regulatory route / packs
- **Owner of:** `CH + canton + commune` route composition, active/inactive layers, pack versions,
  freshness warnings, supported/seed/unsupported commune state.
- **Implementation:** `pilot/selector.py`, `pilot/route_service.py`, `pilot/registry/*.json`,
  `pilot/<commune>/rpga_zones.json`.
- **Public surface:** `aedifica.route` →
  `regulatory_route`, `select_route`, `pack_freshness_warnings`, `list_communes`,
  `commune_support_state`.
- **Non-goals:** does not decide trust state of individual claims; does not write reports.

### 3. Claims / trust contract
- **Owner of:** the claim envelope and the rule that a sourced regulatory fact cannot render
  without evidence.
- **Implementation:** `pilot/claims.py`, `pilot/trust.py`.
- **Public surface:** `aedifica.claims` →
  `make_claim`, `unknown_claim`, `validate_claim`, `validate_claims`, `CLAIM_STATES`,
  `ClaimValidationError`, `render_footer`.
- **Non-goals:** does not know about projects or files.

### 4. Workspace (durable project object)
- **Owner of:** project folder/manifest lifecycle, source+evidence store, brief generation,
  trust-state report rendering, report index + hashes, report-derived memory records.
- **Implementation:** `pilot/workspace.py`, `pilot/artifacts.py`, `pilot/datum_html.py`,
  `pilot/projects/*`, schemas in `pilot/schemas/`.
- **Public surface:** `aedifica.workspace` →
  `create_project_workspace`, `validate_project`, `validate_all`,
  `generate_offline_parcel_brief`, `render_brief_html`, `record_report`,
  `report_index_path`, `report_memory_path`.
- **Non-goals:** no adapter mutation, no permit "ready" decision, no network.

### 5. Adapters (multi-software action lifecycle)
- **Owner of:** capability manifests, transaction contract (dry-run → approval → execute),
  model inspection, snapshot normalization, export intents, live harness.
- **Implementation:** `pilot/model_bridge_demo.py`, `pilot/adapter_snapshots.py`,
  `pilot/adapter_contract.py`, `pilot/model/*.json`.
- **Public surface:** `aedifica.adapters` (added in R4 wave) → capability + transaction services.
- **Non-goals:** never executes a mutation without an execution-scope approval in the ledger.

### 6. Memory + ledger (liability layer)
- **Owner of:** durable decision/approval/evidence records, approval scopes, carryover queries.
- **Implementation:** `pilot/ledger.py`, `pilot/ledger_writer.py`, `pilot/validate_memory.py`,
  `pilot/validate_ledger.py`, `pilot/projects/<id>/memory/*`.
- **Public surface:** `aedifica.ledger` (added in R3 wave) → writer + approval-scope services.
- **Non-goals:** approval is always scoped; a report approval can never authorize adapter mutation.

### 7. Reports / surfaces (rendering)
- **Owner of:** human-readable Datum-styled HTML for briefs, permit readiness, opposition,
  cost, site/handover, and the workspace shell.
- **Implementation:** `pilot/datum_html.py` + `render_*` functions in the relevant modules,
  `pilot/ui/*.html`.
- **Public surface:** `render_brief_html` and the per-domain `render_*_html` helpers.
- **Non-goals:** rendering never upgrades a claim's trust state; it only displays it.

## R1B-facing modules: owner responsibility + non-goals

| Module (public) | Responsibility | Non-goals |
|---|---|---|
| `aedifica.domain` | envelope + OEREB + zone match | rendering, network, persistence |
| `aedifica.route` | route composition + pack freshness | claim trust state, reports |
| `aedifica.claims` | claim envelope + trust rule | project/file knowledge |
| `aedifica.workspace` | project lifecycle + brief + report + index | adapter mutation, permit "ready" |

## Scripts that remain thin wrappers

These keep their current CLI behavior and call the modules above:
`mvp1_demo.py`, `fiche.py`, `opposition_radar.py`, `selector.py`, `demo_run.py`,
`agent_software_demo.py`. New product entry points (`project_cli.py`, `workspace_api.py`,
`r1b_demo.py`) are also thin wrappers over the package services.

## Invariants (do not regress)

1. `pilot/selfcheck.py` and `tests/contracts/run_contracts.py` stay green on Python 3.11/3.12.
2. No third-party runtime dependency is required for the offline path.
3. A sourced regulatory claim without `source_refs` must refuse to render as `sourced`.
4. No mutation/permit-ready/tender-export before trust renderer + ledger primitives exist.
