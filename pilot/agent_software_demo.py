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
    args = parser.parse_args(argv)

    demo = model_bridge_demo.build_agent_demo(args.ledger)
    if args.json:
        print(json.dumps(demo, ensure_ascii=False, indent=2))
    else:
        _print_human(demo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
