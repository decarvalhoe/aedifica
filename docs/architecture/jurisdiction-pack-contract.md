# Jurisdiction Pack Contract

Aedifica's pilot uses small jurisdiction packs to keep regulatory knowledge explicit,
traceable, and replaceable:

- `pilot/registry/federal.json` for the Swiss federal layer.
- `pilot/registry/canton_vd.json` for the Vaud cantonal layer.
- `pilot/<commune>/rpga_zones.json` for commune zoning rules.

The selector activates only the route needed by a project:

```text
Federal core + selected canton + selected commune
```

Project manifests store the selected route as a durable object, not only a
display string: active layers, inactive layers, selection timestamps, source
versions, and non-blocking freshness warnings.

## Version Contract

Every pack must declare:

```json
{
  "schema_version": "1.0",
  "source_version": {
    "source_status": "official_document_ingested",
    "verified_at": "2026-05-29",
    "review_due": "2026-11-29"
  }
}
```

`schema_version` describes the local data shape. `source_version` describes the
legal/source review state. A future legal update can change `source_version`
without changing `schema_version`; a data-model change must bump
`schema_version`.

## Validation

The enforced contract is `pilot/validate_packs.py`. It is stdlib-only so it can
run before the project has packaging or third-party dependencies.

```bash
python pilot/validate_packs.py
python pilot/selfcheck.py
```

The human-readable JSON Schema lives at
`pilot/schemas/jurisdiction-pack.schema.json`. CI currently enforces the same
shape through the Python validator.

## Minimum Rules

Registry packs must include a level, jurisdiction, description, and at least one
legal unit with `id`, `title`, `ref`, `url`, `scope`, and confidence.

Commune packs must include source metadata, document metadata, at least one
zone, numeric-or-null envelope fields, a free-text rule summary, and provenance
with article, URL, and confidence.

Confidence is intentionally narrow: `high`, `medium`, or `low`.

## Review Cadence

Pilot packs use a six-month `review_due` by default. Review sooner when:

- a commune adopts or publishes a revised PACom/RPGA/RCATC;
- a canton changes procedure, energy, road, or construction law;
- an API or official legal URL changes;
- a project relies on a zone where the current pack confidence is `medium` or
  `low`.

This contract does not make the output authoritative. It makes the evidence
state visible enough for an architect to verify and decide.

Commune availability is governed by
[`commune-support-policy.md`](commune-support-policy.md). New commune packs
should follow
[`../planning/next-commune-ingestion-checklist.md`](../planning/next-commune-ingestion-checklist.md).
