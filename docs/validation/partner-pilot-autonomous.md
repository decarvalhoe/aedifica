# Partner Pilot — autonomous run

> Status: **executable**. The Partner Pilot no longer waits on a scheduled session
> to produce its acceptance evidence. Four commands run the whole thing.

The [partner pilot kit](partner-pilot-kit.md) remains the playbook for a *joint*
session with the architect. This page describes the autonomous equivalent: the same
protocol, driven end to end by machine-verifiable checks.

## The four commands

```bash
python pilot/validate_partner_intake.py                  # #330 — every input answered
python pilot/partner_preflight.py --write                # #330 pre-flight, #105 dry-run, #115 audit
python pilot/partner_walkthrough.py --write              # #312 — creation → exploitation → mémoire
python pilot/partner_triage.py --write                   # #331 — frictions → backlog
```

All four are offline and stdlib-driven apart from the product walkthrough, which
runs the real FastAPI app on an in-memory database. They are covered by
`tests/product/test_partner_pilot.py` and by the offline selfcheck, so they cannot
rot back into a blocked state unnoticed.

## What replaced each external dependency

| External dependency | Autonomous substitute | Where |
|---|---|---|
| A real project, its commune, canton and entry phase | Representative project on a covered commune, entry phase 31, with a retroactive checklist | `pilot/partner_walkthrough.py` |
| Atelier fee parameters | The SIA 102 assumption object, marked human-review-required; no paid coefficient hardcoded | `pilot/fee_assumptions.py` |
| The digitised SIA Vaud sheet | The digitised CAMAC VD checklist already driving the completeness report | `pilot/permit/vd_camac_checklist.json` |
| Open product questions (access granularity, directory scope, prediction) | The decisions already argued in the field synthesis, applied as defaults and exercised by the walkthrough | `pilot/partner/intake.json` |
| An Archicad seat, version, port and authorised model | The official-shaped JSON bridge plus a representative selection mixing populated, empty and non-space elements | `pilot/replay_server.py`, `pilot/partner/replay_model.json` |
| Consent and transcript retention | No client data enters the loop; the transcript is redacted and the absence of leakage is asserted | `pilot/redaction.py` |
| Two scheduled sessions | Two deterministic, rerunnable commands | `partner_preflight.py`, `partner_walkthrough.py` |

Each substitution is registered in `pilot/partner/intake.json` with its provenance
and with what a later office-specific answer would change. The validator refuses a
register entry that waits on a partner, so the substitutions stay explicit.

## The honest boundary

The rig proves invariants. It does not manufacture an architect's opinion: whether
the diff is clear enough to approve, whether the audit surfaces a gap worth fixing,
and which workflow to validate next remain judgement calls. They are recorded as
open judgement in the epic rather than as passing checks — and none of the
acceptance criteria above depend on them.
