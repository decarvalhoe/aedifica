# Trust Contract And Decision Ledger

Aedifica is a preparation and evidence system. It must help an architect reason, verify, and decide; it must not
present itself as a legal authority or silently take responsibility away from the professional.

## Output Trust Contract

Every user-facing claim must render in one of these states:

| State | Meaning | Required payload |
| --- | --- | --- |
| `sourced` | Directly backed by source references. | Source title/ref, locator, valid-as-of date, confidence. |
| `computed` | Calculated from sourced inputs. | Formula, inputs, source refs for every input. |
| `assumption` | Useful but not proven. | Assumption text and required human check. |
| `unknown` | Missing or inaccessible information. | Missing source/data and next action. |
| `conflict` | Active sources disagree or scope is ambiguous. | Conflicting refs and escalation path. |
| `decision` | Human-approved project choice. | Actor, timestamp, decision basis, approval evidence. |

Rules:

- Regulatory facts require at least one source reference.
- Computed values require both formula and input provenance.
- Assumptions must never be styled as facts.
- Legal uncertainty must be surfaced as `unknown` or `conflict`, not smoothed over.
- Actions that mutate files, models, dossiers, or submissions require a ledger entry.

## Ledger Entry Schema

```yaml
ledger_id: LEDGER-2026-05-29-0001
timestamp: "2026-05-29T10:00:00+02:00"
project_id: DEMO-LAUSANNE-PALUD
actor:
  actor_type: human
  name: "Architect"
  role: "liable professional"
event_type: decision
phase:
  phase_code: "31"
  label: "Avant-projet"
summary: "Use Lausanne Centre historique rules for the pilot parcel envelope."
basis:
  source_refs:
    - source_id: LAUSANNE-RPGA-2006
      locator: "Art. 83-94"
      valid_as_of: "2026-05-29"
  evidence_refs:
    - EVIDENCE-OEREB-CH915772367853-2026-05-29
claims:
  - claim_id: CLAIM-ZONE-MATCH-001
    state: sourced
approval:
  required: true
  status: approved
  approved_by: "Architect"
  approved_at: "2026-05-29T10:00:00+02:00"
before_state: null
after_state:
  selected_communal_zone: "Centre historique"
risks:
  - "Gabarit still depends on contiguous built context."
next_actions:
  - "Verify servitudes in land register."
```

## Event Types

| Type | Use |
| --- | --- |
| `source_ingested` | A source or pack is added or refreshed. |
| `claim_created` | A canonical claim is created from source or calculation. |
| `claim_updated` | A claim changes because source, context, or confidence changed. |
| `decision` | A human project decision is recorded. |
| `approval` | A proposed action or interpretation is approved/rejected. |
| `adapter_dry_run` | A mutating command produced a plan but did not execute. |
| `adapter_execution` | A command executed against a file, model, dossier, or system. |
| `verification` | A check passed, failed, or was marked manual-only. |
| `exception` | A deviation from normal gates is approved and justified. |

## Evidence Reference Schema

```yaml
evidence_id: EVIDENCE-OEREB-CH915772367853-2026-05-29
evidence_type: api_extract
source_id: VD-OEREB
locator: "EGRID CH915772367853"
captured_at: "2026-05-29T09:00:00+02:00"
captured_by: "pilot/oereb.py"
hash: null
url: "https://www.rdppf.vd.ch/..."
valid_as_of: "2026-05-29"
retention: project_record
```

## Enforcement Points

The contract is enforced progressively:

1. Pilot output uses visible provenance tags such as `[api]`, `[RPGA]`, `[calc]`, `[assumption]`, and
   `[unknown]`.
2. Jurisdiction packs require source version metadata and confidence fields.
3. Canonical units must include source refs or render as assumptions/open questions.
4. Mutating adapter commands must create ledger entries before execution becomes available.
5. Project reports must include residual unknowns and required human checks.

## Minimum Output Footer

Any generated report or recommendation that uses regulatory facts must include:

```text
Preparation sourced by Aedifica. Not an authority.
The architect verifies the cited sources, assumptions, conflicts, and project-specific facts before relying on it.
```

## Open Implementation Work

- Convert the ledger schema to JSON Schema when the first persistent project record exists.
- Add hashes for captured official extracts and generated reports.
- Add a renderer that refuses to emit `sourced` regulatory claims without `source_refs`.
- Add an approval store before any mutating adapter is enabled.
