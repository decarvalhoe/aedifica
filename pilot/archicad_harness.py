#!/usr/bin/env python3
"""Archicad live test harness — one repeatable command for the partner endpoint.

Runs product info, selection read, missing-metadata audit and a dry-run diff
WITHOUT mutating the model. Accepts an endpoint, a timeout and a fixture-fallback
setting; exits with an actionable message when the endpoint is unavailable. A
successful run returns a redacted transcript (no client/local data leaks).

Live acceptance is tracked as blocked by #105 and #115 until partner access.

Usage:
    python pilot/archicad_harness.py --endpoint http://127.0.0.1:8077
    python pilot/archicad_harness.py            # offline fixture mode
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import model_bridge_demo  # noqa: E402
import redaction  # noqa: E402


def run_harness(endpoint: str | None = None, timeout: float = 2.0, fixture_fallback: bool = True) -> dict:
    transcript = {"steps": []}

    if endpoint:
        product = model_bridge_demo.live_product_info(endpoint, timeout=timeout)
        if product.get("running"):
            mode = "live"
            selection = model_bridge_demo.live_selected_elements(endpoint, timeout=timeout)
        elif fixture_fallback:
            mode = "fixture_fallback"
            transcript["endpoint_error"] = product.get("error")
            selection = model_bridge_demo.inspect_selected_elements()
        else:
            return {
                "ok": False,
                "mode": "unavailable",
                "message": f"Archicad endpoint unavailable at {endpoint}: {product.get('error')}. "
                f"Start the JSON bridge or run without --endpoint for fixture mode.",
            }
    else:
        mode = "fixture"
        product = {"running": False, "product_info": model_bridge_demo.PRODUCT_INFO_FIXTURE if hasattr(model_bridge_demo, "PRODUCT_INFO_FIXTURE") else {"name": "Archicad", "version": "FIXTURE"}}
        selection = model_bridge_demo.inspect_selected_elements()

    audit = model_bridge_demo.missing_metadata_audit(selection)
    first = (selection.get("selected_elements") or [{}])[0]
    dry_run = model_bridge_demo.dry_run_property_update(first.get("element_id", "AC-SPACE-101"), "RoomUsage", "office")

    transcript["steps"] = [
        {"step": "product_info", "running": product.get("running"), "product": product.get("product_info")},
        {"step": "selection", "version": selection.get("source_model_version"), "count": len(selection.get("selected_elements", []))},
        {"step": "missing_metadata_audit", "missing_count": audit["missing_count"]},
        {"step": "dry_run", "blocked": dry_run.get("blocked"), "mutating": False},
    ]
    return {
        "ok": True,
        "mode": mode,
        "mutated": False,
        "audit_count": audit["missing_count"],
        "transcript": redaction.redact_artifact(transcript),
    }


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Archicad live test harness (no mutation).")
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--no-fallback", action="store_true", help="Fail instead of falling back to fixtures.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_harness(args.endpoint, timeout=args.timeout, fixture_fallback=not args.no_fallback)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print(f"Archicad harness OK · mode={result['mode']} · missing metadata={result['audit_count']} · mutated={result['mutated']}")
    else:
        print(result["message"], file=sys.stderr)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
