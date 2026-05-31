#!/usr/bin/env python3
"""Offline prototype of the local model bridge contract.

It does not connect to Archicad. It proves the first-bridge decision can produce
a dry-run plan from the adapter capability matrix before any mutating command.
"""
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX_PATH = os.path.join(HERE, "research", "adapter_capability_matrix.json")


def _load_matrix():
    with open(MATRIX_PATH, encoding="utf-8") as f:
        return json.load(f)


def select_adapter(adapter_id="archicad_json"):
    matrix = _load_matrix()
    for adapter in matrix["adapters"]:
        if adapter["adapter_id"] == adapter_id:
            return adapter
    raise KeyError(adapter_id)


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


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for action in ("inspect_selected_elements", "set_room_usage_property"):
        plan = build_bridge_plan("archicad_json", action)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
