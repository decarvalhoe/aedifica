#!/usr/bin/env python3
"""Dedicated R1A agent-to-software demo entrypoint."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_bridge_demo  # noqa: E402


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEDGER = os.path.join(HERE, "memory", "demo_project_ledger.json")


def _print_human(demo):
    print(f"Demo: {demo['demo_id']}")
    print(f"Fixture mode: {demo['fixture_mode']}")
    print(f"Adapter: {demo['health']['adapter_id']}")
    print(f"Selected elements: {len(demo['selection']['selected_elements'])}")
    print(f"Missing metadata: {demo['missing_metadata']['missing_count']}")
    print(f"Generated items: {demo['dry_run']['action_count']}")
    print(f"Blocked: {demo['dry_run']['blocked']}")
    print()
    print(demo["diff"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Aedifica R1A agent-to-software demo.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER, help="Ledger fixture used for approval state.")
    parser.add_argument("--endpoint", help="Optional live Archicad JSON endpoint, e.g. http://localhost:19723.")
    args = parser.parse_args(argv)

    demo = model_bridge_demo.build_agent_demo(args.ledger)
    if args.endpoint:
        demo["live_probe"] = model_bridge_demo.live_product_info(args.endpoint)
        live_selection = model_bridge_demo.live_selected_elements(args.endpoint)
        if live_selection["selected_elements"]:
            demo["fixture_mode"] = False
            demo["selection"] = live_selection
            demo["missing_metadata"] = model_bridge_demo.missing_metadata_audit(live_selection)
            intent = model_bridge_demo.load_design_intent()
            ledger_data = model_bridge_demo._load_json(args.ledger) if args.ledger else None
            dry_run = model_bridge_demo.dry_run_design_intent(intent, live_selection, ledger_data)
            demo["dry_run"] = dry_run
            demo["diff"] = model_bridge_demo.render_before_after_diff(dry_run)
    if args.json:
        print(json.dumps(demo, ensure_ascii=False, indent=2))
    else:
        _print_human(demo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
