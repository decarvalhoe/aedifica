# MVP1A Spec - Agent-To-Architecture-Software Demo

Status: implementation spec, 2026-05-31.

## Purpose

`MVP1A` exists to prove, early and visibly, that Aedifica is not only a regulatory/report surface. It must show
an agent CLI serving an architect through the product's native multi-software API layer.

The demo is deliberately small:

```text
agent CLI -> project context -> adapter capability check -> model selection
  -> missing model information -> generated design/model items
  -> dry-run plan -> before/after diff -> approval boundary -> ledger evidence
```

## Product Message

Aedifica remains ArchiOS Suisse: bottom-up project intelligence plus top-down architectural assistance. The
model/drawing API is not a side experiment. It is how project knowledge becomes controlled work inside
architecture software.

For the first partner meeting, the sentence should be:

> Aedifica can read the project, read the model, propose concrete model/drawing work, show exactly what would
> change, and wait for the architect before anything is written.

## Demo Flow

1. Load the demo project context and ledger.
2. Check the adapter capabilities for `archicad_json`.
3. Inspect selected elements from the Archicad-shaped snapshot.
4. Run a missing metadata audit on selected spaces.
5. Load a structured architect intent fixture.
6. Convert the intent into property/annotation action items.
7. Build a dry-run plan.
8. Render a before/after diff.
9. Keep execution blocked unless a matching approval exists.
10. Write or reference ledger evidence for dry-runs and future executions.

## Inputs

- Project workspace: `pilot/projects/demo_lausanne_palud/`.
- Model snapshot fixture: `pilot/model/archicad_selection_fixture.json`.
- Architect intent fixture: `pilot/model/design_intent_fixture.json`.
- Ledger fixture: `pilot/memory/demo_project_ledger.json`.
- Adapter capability matrix: `pilot/research/adapter_capability_matrix.json`.

## Outputs

- Adapter health/capability report.
- Selected element report.
- Missing metadata audit.
- Structured dry-run action plan.
- Before/after diff text.
- Safety state: blocked or approval-backed.
- Demo CLI summary.

## Live Archicad Path

The fixture path is the offline proof. The live path replaces only the transport:

```text
fixture selected_elements -> Archicad JSON selected_elements response
fixture dry-run commands -> Archicad JSON command payload preview
fixture before/after evidence -> live before/after model snapshot
```

The lifecycle, issue acceptance criteria and ledger records stay identical.

## Safety Requirements

- No mutation without dry-run.
- No mutation without human approval in the ledger.
- No product claim that Archicad is the product identity.
- Every unsupported adapter capability blocks the action with an explicit reason.
- Fixture fallback must be visible in docs and demos.

## Failure Modes To Render

- Adapter unavailable: stay in fixture mode or report the live endpoint failure.
- Capability unavailable: keep the item in the plan but mark it unsupported.
- Approval missing: allow inspection/dry-run, block execution.
- Verification missing: do not claim execution success.
- Source basis weak: mark the item as needing architect confirmation before approval.

## Acceptance Criteria

- `python pilot/demo_run.py` includes the model bridge action count and blocked/approved state.
- `python pilot/agent_software_demo.py` runs the R1A slice directly.
- `python pilot/selfcheck.py` verifies the design intent fixture, dry-run plan and before/after diff.
- The roadmap places `R1A` before `R1B`.
- GitHub issues exist for both completed local proof and future live Archicad work.
- The partner can understand the value without reading code.
