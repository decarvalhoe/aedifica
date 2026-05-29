# NOMOS Archi Schema v0

This is the initial canonical-unit contract for architecture work in Aedifica. It is intentionally small enough
to implement before the product has a database, while still covering regulation, project decisions, evidence,
deliverables, checks, and actions.

## Unit Types

| Type | Purpose |
| --- | --- |
| `source` | A citable instrument, document, API response, model snapshot, meeting record, or office standard. |
| `term` | A normalized concept with localized labels and source-backed definitions. |
| `rule` | A general rule extracted from a source. |
| `requirement` | A project obligation derived from rules, brief, contract, or phase. |
| `constraint` | A measurable limit or condition affecting design, permit, cost, or execution. |
| `formula` | A computable relationship such as surface x index, height rule, fee calculation, or distance rule. |
| `exception` | A conditional carve-out, derogation, or unresolved conflict. |
| `decision` | A human or approved project decision. |
| `evidence` | Proof supporting a claim, result, before/after state, or approval. |
| `deliverable` | A phase-bound output expected from the architect or project team. |
| `check` | A manual, semi-automated, or automated verification. |
| `action` | A proposed or executed operation against a project, file, model, dossier, or external system. |

## Canonical Unit

```yaml
unit_id: CH-VD-LAUSANNE-RPGA-CENTRE-HISTORIQUE-SETBACK
unit_type: constraint
title: "Centre historique: distance aux limites non fixee"
status: active
jurisdiction:
  country: CH
  canton_or_region: VD
  commune: Lausanne
phase_applicability:
  - phase_code: "31"
    label: "Avant-projet"
  - phase_code: "32"
    label: "Projet de l'ouvrage"
  - phase_code: "33"
    label: "Procedure d'autorisation"
domains:
  - zoning
  - envelope
criticality: high
language_neutral_key: centre_historique.setback
localized_labels:
  fr: "Distance aux limites non fixee"
source_refs:
  - source_id: LAUSANNE-RPGA-2006
    locator: "Art. 88.1"
    valid_as_of: "2026-05-29"
    confidence: high
claim:
  text: "La distance aux limites de propriete n'est pas fixee pour le Centre historique."
  claim_type: regulatory
  confidence: high
conditions:
  - "Active only when the commune zoning match resolves to Centre historique."
verification:
  method: human_review
  pass_condition: "Architect verifies zoning match and article reference before relying on the claim."
assumptions: []
conflicts: []
actions:
  - action_type: escalate_review
    reason: "Geometric envelope still depends on contiguous building context."
```

## Required Fields

Every unit must include:

- `unit_id`
- `unit_type`
- `title`
- `status`
- `source_refs`
- `claim` or a type-specific payload
- `confidence`

Regulatory and project-obligation units must also include:

- `valid_as_of`
- `phase_applicability`
- `jurisdiction` when applicable
- `verification.method`
- `verification.pass_condition`

## Status Values

| Status | Meaning |
| --- | --- |
| `draft` | Captured but not reviewed. |
| `active` | Reviewed enough for pilot use with visible confidence. |
| `superseded` | Replaced by a newer unit or source version. |
| `blocked` | Known issue prevents use. |
| `retired` | Intentionally no longer used. |

## Confidence Values

| Value | Meaning |
| --- | --- |
| `high` | Directly supported by an official source or verified extract. |
| `medium` | Supported but needs contextual review before project reliance. |
| `low` | Useful signal, but incomplete, inferred, or awaiting source confirmation. |

## Source Reference Contract

```yaml
source_refs:
  - source_id: VD-LATC
    locator: "BLV 700.11"
    url: "https://prestations.vd.ch/pub/blv-publication/actes/consolide/700.11"
    valid_as_of: "2026-05-29"
    source_version: "live_verified"
    confidence: high
```

No claim may be rendered as regulatory fact without at least one `source_ref`. If a source is missing, the unit
must render as an assumption or open question.

## Relationships

Units may reference each other through typed links:

```yaml
links:
  derives_from:
    - CH-LAT
  constrains:
    - PROJECT-ENVELOPE-001
  verified_by:
    - CHECK-LAUSANNE-ZONE-MATCH
  decided_by:
    - DECISION-2026-05-29-PILOT-VD-LAUSANNE
```

These links are the bridge from a rule corpus to a project matrix and, later, to a database graph.

## Validation Direction

The current pilot keeps the schema as Markdown until the first implementation needs storage. The next technical
step is to convert this contract into `nomos-unit.schema.json` and fixture-based validators once real canonical
unit files appear.
