#!/usr/bin/env python3
"""Milestone release-gate command.

Runs the relevant contract validators (and, from the CLI, the offline selfcheck)
for a named milestone, and reports pass/fail with blocked live dependencies shown
SEPARATELY so they never look like code failures. The markdown output is meant to
be pasted into a GitHub issue or PR.

Usage:
    python pilot/release_gate.py R1B
    python pilot/release_gate.py R4 --no-selfcheck
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Live, partner-dependent acceptance that is intentionally blocked, not failing.
# Emptied once #105 / #115 became machine-verifiable: `pilot/partner_preflight.py`
# proves the read-only loop (mode=live, real before value, mutated=false, audit)
# end to end against the official-shaped bridge, with no seat to wait for.
BLOCKED_LIVE = []

MILESTONE_GATES = {
    "R1A": {"contracts": True, "selfcheck": True, "blocked_live": []},
    "R1B": {"contracts": True, "selfcheck": True, "blocked_live": []},
    "R2": {"contracts": True, "selfcheck": True, "blocked_live": []},
    "R3": {"contracts": True, "selfcheck": True, "blocked_live": []},
    "R4": {"contracts": True, "selfcheck": True, "blocked_live": BLOCKED_LIVE},
    "R5": {"contracts": True, "selfcheck": True, "blocked_live": []},
    "R6": {"contracts": True, "selfcheck": True, "blocked_live": []},
    # W-waves: the offline backbone is checked here; the product stack (DB+API)
    # runs as the separate `python -m pytest tests/product` suite (CI product job).
    "W1": {"contracts": True, "selfcheck": True, "blocked_live": []},
}


def _contract_validators():
    contracts_dir = os.path.join(ROOT, "tests", "contracts")
    if contracts_dir not in sys.path:
        sys.path.insert(0, contracts_dir)
    import run_contracts  # noqa: E402

    return run_contracts.VALIDATORS


def run_gate(milestone: str = "R1B") -> dict:
    gate = MILESTONE_GATES.get(milestone)
    if not gate:
        raise ValueError(f"unknown milestone: {milestone}")
    code_errors = []
    validator_count = 0
    if gate["contracts"]:
        for validator in _contract_validators():
            validator_count += 1
            code_errors.extend(getattr(validator(), "errors", []))
    return {
        "milestone": milestone,
        "contracts_passed": not code_errors,
        "validator_count": validator_count,
        "code_errors": code_errors,
        "blocked_live": gate["blocked_live"],
        "selfcheck_required": gate["selfcheck"],
    }


def render_markdown(result: dict, selfcheck_status: str | None = None) -> str:
    lines = [
        f"### Release gate · {result['milestone']}",
        "",
        f"- Contract validators: {'✅ pass' if result['contracts_passed'] else '❌ fail'} "
        f"({result['validator_count']} validators)",
    ]
    if selfcheck_status:
        lines.append(f"- Offline selfcheck: {selfcheck_status}")
    if result["code_errors"]:
        lines.append("- Code failures:")
        lines.extend(f"  - {error}" for error in result["code_errors"])
    if result["blocked_live"]:
        lines.append("- Blocked live dependencies (not code failures):")
        lines.extend(f"  - {dep['id']} {dep['title']} — {dep['reason']}" for dep in result["blocked_live"])
    return "\n".join(lines)


def _run_selfcheck() -> str:
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "selfcheck.py")],
        capture_output=True,
        text=True,
    )
    tail = (proc.stdout.strip().splitlines() or ["(no output)"])[-1]
    return ("✅ " if proc.returncode == 0 else "❌ ") + tail


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Run the milestone release gate.")
    parser.add_argument("milestone", nargs="?", default="R1B", choices=sorted(MILESTONE_GATES))
    parser.add_argument("--no-selfcheck", action="store_true")
    args = parser.parse_args(argv)

    result = run_gate(args.milestone)
    selfcheck_status = None
    if result["selfcheck_required"] and not args.no_selfcheck:
        selfcheck_status = _run_selfcheck()
    print(render_markdown(result, selfcheck_status))
    selfcheck_failed = bool(selfcheck_status and selfcheck_status.startswith("❌"))
    return 0 if result["contracts_passed"] and not selfcheck_failed else 1


if __name__ == "__main__":
    sys.exit(main())
