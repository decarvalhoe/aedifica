# Next Commune Ingestion Checklist

Use this checklist when adding a new commune pack to `pilot/<commune>/rpga_zones.json`.

## Intake

- Confirm country, canton, commune name and official spelling.
- Record official règlement, plan d'affectation and any zone reserve/overlay documents.
- Capture source URLs, in-force dates, publication status and language.
- Decide support state: `seed`, `on_demand`, or `unsupported`.

## Normalize

- Create `schema_version` and `source_version` with `verified_at`, `review_due`, `source_status` and notes.
- Add document metadata: title, version, in-force statement, URL and rule-style note.
- Normalize each zone into numeric-or-null `ius`, `ibus`, `ios`, heights, levels and setbacks.
- Keep geometry, exceptions and non-numeric rules in `other`.
- Attach provenance per zone with article, URL and confidence.

## Validate

- Run `python pilot/validate_packs.py`.
- Run `python pilot/selector.py` and confirm the commune appears as an available layer.
- Add or update a fixture parcel before claiming end-to-end support.
- Run `python pilot/selfcheck.py`.

## Release

- Update the commune support policy.
- Add a source-manifest entry in affected project workspaces.
- Add a freshness review date to the project route.
- Keep production reliance blocked until an architect verifies the pack for the project scope.
