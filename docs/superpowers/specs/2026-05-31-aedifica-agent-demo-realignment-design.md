# Aedifica Agent Demo Realignment Design

Status: approved by owner instruction, 2026-05-31.

## Context

The Aedifica brand remains Aedifica / AEDIFICA. The rebranding is considered locked.

The repository already states the correct product scope: Aedifica is ArchiOS Suisse, not a
regulatory report generator, not an Archicad-only plugin, and not a pitch-surface product. The
current weakness is sequencing. The roadmap keeps the multi-software drawing/model proof in `R4`,
while the owner needs an early, visible proof that an agent CLI can serve an architect inside the
tools they already use.

## Product Decision

Insert `R1A Agent-To-Software Demo` before the existing `R1 Project Workspace` productization.

`R1A` must prove the loop:

```text
project context -> agent CLI -> adapter capability check -> selected model snapshot
  -> structured design/drawing intent -> dry-run plan -> before/after diff
  -> human approval boundary -> ledger evidence
```

The first adapter thread remains Archicad JSON because it matches the partner-office context. The
contract must stay adapter-neutral so later IFC, Speckle, Revit, Rhino, SketchUp, AutoCAD/BricsCAD,
Vectorworks, document and construction-management adapters can reuse the same lifecycle.

## User Value

The first partner demo should be emotionally clear to a skeptical architect:

1. Aedifica reads real project/regulatory context.
2. Aedifica reads the model or a controlled model snapshot.
3. Aedifica sees missing room/space information.
4. Aedifica proposes concrete drawing/model items or metadata updates.
5. Aedifica shows a before/after diff before touching anything.
6. The architect remains responsible and approves the scope.
7. The action leaves traceable evidence in the ledger.

The demo can use a fixture when live Archicad is unavailable, but the fixture must be labeled as a
fallback and shaped exactly like the future live path.

## Non-Goals

- Do not mutate a live model without explicit approval and verification.
- Do not define the product as Archicad-only.
- Do not hide the current fixture status.
- Do not move regulatory/project intelligence out of the MVP. It remains the bottom-up spine.
- Do not build a broad UI before the CLI demo contract is strong.

## Components

- `docs/specs/mvp1a-agent-to-architecture-software-demo.md`: product and technical spec.
- `docs/planning/software-roadmap.md`: release map with `R1A` before `R1B`.
- `docs/planning/epics-and-backlog.md`: new epics `AED-E14` to `AED-E23`.
- `docs/strategy/decisions.md`: accepted decision record for the MVP sequence correction.
- `pilot/model/design_intent_fixture.json`: controlled drawing/model intent fixture.
- `pilot/model_bridge_demo.py`: dry-run generation and before/after diff helpers.
- `pilot/demo_run.py`: partner-demo output includes the model bridge proof.
- `pilot/selfcheck.py`: offline checks for the agent-to-software slice.

## Acceptance

- The docs make it impossible to read Aedifica as a regulatory-only product.
- The roadmap visibly promotes the agent/API/software proof to the first demonstrative MVP slice.
- GitHub has issue-ready work packages for the real live Archicad bridge and later adapters.
- Local CI evidence proves the fixture-based demo contract works without network or Archicad.
