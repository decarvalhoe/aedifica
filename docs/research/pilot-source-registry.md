# Pilot Source Registry

This is the implementation-facing answer to issue #3. It defines the first prioritized Swiss source corpus for
the Vaud / Lausanne pilot, compatible with NOMOS Archi and the jurisdiction-pack architecture.

Files:

- structured registry: `pilot/research/pilot_source_registry.json`;
- validator: `pilot/validate_research.py`;
- existing pack contract: [`../architecture/jurisdiction-pack-contract.md`](../architecture/jurisdiction-pack-contract.md).

## Registry Rule

The pilot source registry is broader than the jurisdiction packs. Packs hold reusable regulatory content; the
source registry declares every source family that can feed a project:

| Tier | Use |
|---|---|
| `federal` | Fedlex and national rules such as LAT or OPB. |
| `cantonal` | Vaud legal/procedural layer, ACTIS-CAMAC, energy and permit pages. |
| `communal` | Lausanne/Pully zoning rules and commune-specific obligations. |
| `parcel` | RDPPF/OEREB, geo.admin.ch, parcel geometry and binding extract data. |
| `sia` | SIA phase/professional standards as metadata anchors; licensed text required in production. |
| `office` | Internal templates, BIM conventions, drawing standards, checklists. |
| `project` | Brief, uploaded documents, minutes, decisions, photos, model snapshots. |

## NOMOS Compatibility

Every source entry declares:

- `source_id`: stable reference used by canonical units;
- `tier` and `kind`: jurisdiction or project layer;
- `uri`, `version`, `valid_as_of`, `review_due`: temporal traceability;
- `ingestion_status`: live API, registry pack, metadata-only, placeholder, etc.;
- `nomos_unit_types`: which units it can produce (`rule`, `constraint`, `evidence`, `decision`, `check`,
  `action`, etc.);
- `used_for_phases`: where the source matters in the phase matrix;
- `allowed_use`: what Aedifica may do with it.

This avoids the dangerous shortcut "put everything in RAG". Sources are typed before retrieval, and project
documents remain project-scoped unless explicitly promoted into a reusable pack.

## Current Coverage

The current registry covers the first MVP route:

```text
CH federal core + VD canton + Lausanne commune + parcel extract + SIA metadata + office/project placeholders
```

It deliberately includes placeholders for `office` and `project` tiers because those are not public legal
sources. They still need stable IDs and allowed-use rules before they can be safely mixed with official
constraints.

## Validation

```bash
python pilot/validate_research.py
```

The validator fails if any required tier is missing, if a source is missing version/review metadata, or if a
source does not declare which NOMOS unit types and phases it can feed.
