# Later Track Spec — Voice-To-Design

Issue: #20

## Goal

Keep the "speak to an AI that works on the project" dream, but route speech through professional safeguards:
transcript, structured intent, project context, constraints, dry-run, preview, human approval, API/MCP execution,
and correction loop.

## Pipeline

```text
speech
  -> transcript
  -> structured architectural intent
  -> project/context resolution
  -> constraint and phase check
  -> dry-run action plan
  -> preview or diff
  -> human approval
  -> MCP/API execution
  -> verification report
  -> correction loop
```

## Intent Contract

Voice produces intent, not raw commands:

```json
{
  "intent_type": "update_model_property",
  "target": {"selection": "current_rooms"},
  "desired_change": {"property": "usage", "value": "housing"},
  "phase_code": "32",
  "requires_adapter": "model_intelligence",
  "approval_required": true
}
```

## Safety

- Never execute raw transcript text.
- Never bypass project constraints or adapter capability checks.
- Every mutating action requires dry-run and approval.
- If intent is ambiguous, ask a clarifying question.
- If preview fails, execution is blocked.

## Success Criteria

- Converts spoken instruction to structured intent.
- Checks project context and constraints before proposing action.
- Shows a dry-run/preview before execution.
- Records approved execution and verification result.
- Allows correction without losing the evidence trail.
