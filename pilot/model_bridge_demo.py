#!/usr/bin/env python3
"""Offline prototype of the local model bridge contract.

It does not connect to Archicad. It proves the first-bridge decision can produce
a dry-run plan from the adapter capability matrix before any mutating command.
"""
import json
import os
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request


HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX_PATH = os.path.join(HERE, "research", "adapter_capability_matrix.json")
SELECTION_FIXTURE = os.path.join(HERE, "model", "archicad_selection_fixture.json")
DESIGN_INTENT_FIXTURE = os.path.join(HERE, "model", "design_intent_fixture.json")
REQUIRED_SPACE_PROPERTIES = ("RoomUsage", "SIA416SurfaceType")


def _load_matrix():
    with open(MATRIX_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def select_adapter(adapter_id="archicad_json"):
    matrix = _load_matrix()
    for adapter in matrix["adapters"]:
        if adapter["adapter_id"] == adapter_id:
            return adapter
    raise KeyError(adapter_id)


def health_check(adapter_id="archicad_json", endpoint=None, timeout=1.0):
    adapter = select_adapter(adapter_id)
    running = False
    error = None
    if endpoint:
        try:
            with urllib.request.urlopen(endpoint, timeout=timeout) as response:
                running = 200 <= response.status < 300
        except (OSError, urllib.error.URLError) as exc:
            error = str(exc)
    return {
        "adapter_id": adapter_id,
        "running": running,
        "endpoint": endpoint,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "read_capabilities": adapter.get("read_capabilities", []),
        "write_capabilities": adapter.get("write_capabilities", []),
        "error": error,
    }


def inspect_selected_elements(snapshot_path=SELECTION_FIXTURE):
    snapshot = _load_json(snapshot_path)
    return {
        "source_model_version": snapshot["model_version"],
        "source_model_ref": snapshot["source_model_ref"],
        "selected_elements": [
            {
                "element_id": item["element_id"],
                "type": item["type"],
                "classification": item["classification"],
                "properties": item.get("properties", {}),
            }
            for item in snapshot.get("selected_elements", [])
        ],
    }


def load_design_intent(path=DESIGN_INTENT_FIXTURE):
    intent = _load_json(path)
    required = {"intent_id", "project_context", "items"}
    missing = sorted(required - set(intent))
    if missing:
        raise ValueError(f"design intent missing fields: {missing}")
    if not isinstance(intent.get("items"), list) or not intent["items"]:
        raise ValueError("design intent requires at least one item")
    return intent


def missing_metadata_audit(selection, required_space_properties=REQUIRED_SPACE_PROPERTIES):
    missing = []
    for element in selection.get("selected_elements", []):
        if element.get("classification") != "IfcSpace":
            continue
        properties = element.get("properties") or {}
        for prop in required_space_properties:
            if properties.get(prop) in (None, ""):
                missing.append(
                    {
                        "element_id": element["element_id"],
                        "classification": element["classification"],
                        "missing_property": prop,
                        "proposed_fix": f"Set {prop} from room program or architect approval.",
                    }
                )
    return {
        "source_model_version": selection.get("source_model_version"),
        "missing_count": len(missing),
        "missing": missing,
    }


def _selected_element_map(selection):
    return {item["element_id"]: item for item in selection.get("selected_elements", [])}


def dry_run_design_intent(intent=None, selection=None, ledger_data=None):
    intent = intent or load_design_intent()
    selection = selection or inspect_selected_elements()
    approved = _has_ledger_approval(ledger_data, scope_keyword="dry-run")
    elements = _selected_element_map(selection)
    actions = []
    for item in intent["items"]:
        if item["kind"] == "property_update":
            target = elements.get(item["target_element_id"], {})
            before = (target.get("properties") or {}).get(item["property_name"])
            actions.append(
                {
                    "item_id": item["item_id"],
                    "action": "set_property",
                    "target_element_id": item["target_element_id"],
                    "property_name": item["property_name"],
                    "before": before,
                    "after": item["proposed_value"],
                    "basis": item.get("basis", {}),
                    "supported": bool(target),
                }
            )
        elif item["kind"] == "drawing_annotation":
            actions.append(
                {
                    "item_id": item["item_id"],
                    "action": "prepare_annotation",
                    "target_view": item["target_view"],
                    "before": None,
                    "after": item["text"],
                    "basis": item.get("basis", {}),
                    "supported": True,
                }
            )
        else:
            actions.append(
                {
                    "item_id": item.get("item_id", "unknown"),
                    "action": "unsupported",
                    "before": None,
                    "after": None,
                    "basis": item.get("basis", {}),
                    "supported": False,
                }
            )
    return {
        "intent_id": intent["intent_id"],
        "adapter_id": intent["project_context"].get("adapter_id"),
        "source_model_version": selection.get("source_model_version"),
        "dry_run": True,
        "blocked": not approved,
        "approval_scope": "dry-run only",
        "action_count": len(actions),
        "unsupported_count": len([action for action in actions if not action["supported"]]),
        "actions": actions,
    }


def render_before_after_diff(dry_run):
    lines = [
        f"Intent: {dry_run['intent_id']}",
        f"Adapter: {dry_run['adapter_id']}",
        f"Model: {dry_run['source_model_version']}",
        f"Blocked: {str(dry_run['blocked']).lower()}",
    ]
    for action in dry_run["actions"]:
        if action["action"] == "set_property":
            lines.append(
                "Before/After: "
                f"{action['target_element_id']}.{action['property_name']} "
                f"{action['before']!r} -> {action['after']!r}"
            )
        elif action["action"] == "prepare_annotation":
            lines.append(
                "Before/After: "
                f"{action['target_view']} annotation None -> {action['after']!r}"
            )
        else:
            lines.append(f"Unsupported: {action['item_id']}")
    return "\n".join(lines)


def _has_ledger_approval(ledger_data, scope_keyword="property update"):
    if not ledger_data:
        return False
    for entry in ledger_data.get("entries", []):
        if entry.get("event_type") == "approval":
            after = entry.get("after_state") or {}
            text = " ".join(str(value).lower() for value in [entry.get("summary"), after.get("approval_scope")])
            if scope_keyword in text or "dry-run" in text:
                return True
        approval = entry.get("approval") or {}
        if approval.get("approved_by") and scope_keyword in approval.get("scope", "").lower():
            return True
    return False


def dry_run_property_update(element_id, property_name, value, ledger_data=None):
    approved = _has_ledger_approval(ledger_data)
    return {
        "action": "set_property",
        "element_id": element_id,
        "property_name": property_name,
        "proposed_value": value,
        "dry_run": True,
        "blocked": not approved,
        "required_approval": None if approved else {
            "approved_by": "required",
            "approved_at": "required",
            "basis": "required",
            "scope": f"Approve property update {element_id}.{property_name}",
        },
    }


def build_bridge_plan(adapter_id="archicad_json", action="inspect_selected_elements"):
    adapter = select_adapter(adapter_id)
    if action == "inspect_selected_elements":
        required_reads = {"selection", "elements", "properties"}
        mutating = False
    elif action == "set_room_usage_property":
        required_reads = {"selection", "elements", "properties"}
        required_write = "set_properties"
        mutating = True
        if required_write not in adapter["write_capabilities"]:
            raise ValueError(f"{adapter_id} cannot {required_write}")
    else:
        raise ValueError(f"unsupported action {action}")
    missing = sorted(required_reads - set(adapter["read_capabilities"]))
    if missing:
        raise ValueError(f"{adapter_id} missing read capabilities: {missing}")
    return {
        "adapter_id": adapter_id,
        "action": action,
        "mutating": mutating,
        "dry_run_required": mutating,
        "approval_required": mutating,
        "steps": [
            "check_adapter_alive",
            "capture_before_snapshot",
            "execute_read_commands" if not mutating else "prepare_write_commands",
            "render_diff_or_report",
            "write_memory_record",
        ],
    }


def build_agent_demo(ledger_path=None):
    ledger_data = _load_json(ledger_path) if ledger_path else None
    health = health_check("archicad_json")
    selection = inspect_selected_elements()
    audit = missing_metadata_audit(selection)
    intent = load_design_intent()
    dry_run = dry_run_design_intent(intent, selection, ledger_data)
    return {
        "demo_id": "AEDIFICA-R1A-AGENT-TO-SOFTWARE",
        "fixture_mode": True,
        "health": health,
        "selection": selection,
        "missing_metadata": audit,
        "design_intent": {
            "intent_id": intent["intent_id"],
            "item_count": len(intent["items"]),
        },
        "dry_run": dry_run,
        "diff": render_before_after_diff(dry_run),
    }


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(health_check("archicad_json"), ensure_ascii=False, indent=2))
    print(json.dumps(inspect_selected_elements(), ensure_ascii=False, indent=2))
    print(json.dumps(missing_metadata_audit(inspect_selected_elements()), ensure_ascii=False, indent=2))
    print(json.dumps(build_agent_demo(), ensure_ascii=False, indent=2))
    for action in ("inspect_selected_elements", "set_room_usage_property"):
        plan = build_bridge_plan("archicad_json", action)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
