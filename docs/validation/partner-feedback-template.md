# Partner feedback capture template

> Status: R1B. Companion to
> [`partner-agent-demo-protocol.md`](partner-agent-demo-protocol.md). Use this
> after a demo/validation session with the partner architect. **Do not paste any
> private project data** (client names, addresses, model files) — describe the
> workflow, not the case.

Each captured item should become a GitHub issue with an `Epic` (`AED-E##`) and a
`Milestone` (`R1A`…`R6`) label, mirroring
[`planning/epics-and-backlog.md`](../planning/epics-and-backlog.md).

## Session

| Field | Value |
|---|---|
| Date | |
| Surface(s) shown | R1B brief · permit readiness · claim review · adapter dry-run |
| Partner role | architect / draftsperson / fiduciary |
| Time saved (estimate) | |
| Trust / clarity (1-5) | |
| Willingness to test on a real model | yes / no / conditional |

## Feedback items (categorize each)

For every item, fill: **category · title · what · why it matters · proposed epic/milestone**.

### 1. Product feedback (workflow fit, missing step, UX)
- [ ] …

### 2. Data gaps (missing source, commune, registry, unknown that should be sourced)
- [ ] …

### 3. Adapter blockers (Archicad/IFC/Speckle/export capability or live access)
- [ ] …

### 4. Sales objections (pricing, scope doubt, "we already use X")
- [ ] …

## Turning an item into an issue

```
Title:    [AED-1XX] <short imperative>
Epic:     AED-E## …
Milestone: R#
Labels:   product|backend|frontend|data|adapter|validation|docs|security
Body:     Why / Scope / Acceptance criteria (testable) / Dependencies
```

## Privacy reminder

No private project data is required anywhere in this template. If an item needs a
real example, anonymize it (zone, commune and constraint type are enough) and run
shared artifacts through `python pilot/redaction.py` first.
