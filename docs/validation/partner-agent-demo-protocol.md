# Partner Agent Demo Validation Protocol

Status: R1A validation protocol, 2026-05-31.

## Purpose

This protocol records whether the R1A demo convinces an architect that an agent CLI can help real architectural
work through an API/adapter layer.

## Demo To Run

```powershell
python pilot/agent_software_demo.py
python pilot/agent_software_demo.py --json
python pilot/demo_run.py
```

## Record Before The Demo

- Partner office:
- Architect role:
- Archicad version:
- JSON bridge availability:
- Project phase:
- Model type shown:
- Sensitive data restrictions:

## Questions During The Demo

1. Does the selected-model inspection match something you do manually today?
2. Are the generated room metadata and drawing annotation items understandable?
3. Is the before/after diff clear enough to approve or reject?
4. Does fixture mode reduce trust, or is it acceptable as a local proof before live connection?
5. Which workflow would you test next on a real model: room data, drawing annotations, export checks, sheets, or quantities?

## Success Measures

- The architect can restate the loop: context -> model -> generated items -> diff -> approval.
- The architect identifies at least one task this could save time on.
- The architect does not read the product as Archicad-only.
- The architect accepts the approval boundary as necessary rather than friction.
- The architect agrees to provide or run a controlled live model test.

## Output

Create follow-up issues for:

- live Archicad setup blockers;
- missing action types;
- confusing copy or trust states;
- data-privacy constraints;
- next model workflow to validate.
