#!/usr/bin/env python3
"""Autonomous Partner Pilot pre-flight and Archicad evidence run (#330, #105, #115).

Runs the whole read-only loop end to end without a human in the seat: it brings up
the official-shaped JSON bridge (the replay stand-in, or a real endpoint when one is
given), reads the selection, audits missing metadata, produces a dry-run diff and
proves the model was not mutated by re-reading it afterwards.

Every check is a machine-verifiable invariant. Values that could carry client data
never leave the process: the shareable evidence keeps structural identifiers and a
fingerprint of the ``before`` value, never the value itself.

Run:
    python pilot/partner_preflight.py --json
    python pilot/partner_preflight.py --endpoint http://127.0.0.1:19723 --write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import archicad_harness  # noqa: E402
import model_bridge_demo  # noqa: E402
import redaction  # noqa: E402
import replay_server  # noqa: E402

EVIDENCE_DIR = os.path.join(os.path.dirname(HERE), "docs", "validation", "evidence")
REPLAY_MODEL = os.path.join(HERE, "partner", "replay_model.json")
DEFAULT_PROPERTY = "RoomUsage"
DEFAULT_PROPOSED = "office"


class PreflightError(Exception):
    """The pre-flight could not be run at all (as opposed to failing a check)."""


def load_replay_model(path: str = REPLAY_MODEL) -> list:
    """Representative in-repo selection: populated, partly empty and non-space elements."""
    with open(path, encoding="utf-8") as f:
        model = json.load(f)
    elements = model.get("selected_elements") or []
    if not elements:
        raise PreflightError(f"replay model {path} carries no element")
    return [{k: v for k, v in item.items() if k != "comment"} for item in elements]


@contextmanager
def _replay_endpoint():
    server = replay_server.make_server("127.0.0.1", 0, selection=load_replay_model())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _fingerprint(value) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _zones(selection: dict) -> list:
    return [
        element
        for element in selection.get("selected_elements", [])
        if element.get("type") == "Zone" or element.get("classification") == "IfcSpace"
    ]


def _target_zone(selection: dict, property_name: str) -> dict | None:
    for zone in _zones(selection):
        if zone.get("properties_available") and property_name in (zone.get("properties") or {}):
            return zone
    return None


def _audit_evidence(selection: dict, expected: tuple) -> dict:
    elements = []
    for zone in _zones(selection):
        properties = zone.get("properties") or {}
        states = zone.get("property_states") or {}
        present = [name for name in expected if properties.get(name) not in (None, "")]
        missing = [name for name in expected if properties.get(name) in (None, "")]
        elements.append(
            {
                "element_id": zone.get("element_id"),
                "classification": zone.get("classification"),
                "expected": list(expected),
                "present": present,
                "missing": missing,
                "property_states": {name: states.get(name, {}).get("status") for name in expected},
            }
        )
    return {
        "expected_properties": list(expected),
        "selected_element_count": len(selection.get("selected_elements", [])),
        "audited_zone_count": len(elements),
        "elements": elements,
        "missing_total": sum(len(item["missing"]) for item in elements),
        "unavailable_properties": selection.get("unavailable_properties") or {},
        "classification_error": selection.get("classification_error"),
    }


def _check(checks: list, check_id: str, ok: bool, detail: str) -> bool:
    checks.append({"id": check_id, "ok": bool(ok), "detail": detail})
    return bool(ok)


def run_preflight(
    endpoint: str | None = None,
    property_name: str = DEFAULT_PROPERTY,
    proposed_value: str = DEFAULT_PROPOSED,
    timeout: float = 2.0,
    expected_properties: tuple = model_bridge_demo.REQUIRED_SPACE_PROPERTIES,
) -> dict:
    """Run the full read-only loop and return checks plus shareable evidence."""
    if endpoint:
        return _run_against(endpoint, "live_seat", property_name, proposed_value, timeout, expected_properties)
    with _replay_endpoint() as replay:
        return _run_against(replay, "replay_stand_in", property_name, proposed_value, timeout, expected_properties)


def _run_against(endpoint, endpoint_kind, property_name, proposed_value, timeout, expected_properties) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    checks: list = []

    product = model_bridge_demo.live_product_info(endpoint, timeout=timeout)
    _check(
        checks,
        "bridge_live",
        product.get("running") is True,
        f"product info running={product.get('running')} error={product.get('error')}",
    )

    selection = model_bridge_demo.live_selected_elements(
        endpoint, timeout=timeout, required_properties=tuple(expected_properties)
    )
    problem = model_bridge_demo.selection_problem(selection)
    _check(checks, "selection_readable", problem is None, problem or "selection normalized without problem")
    _check(
        checks,
        "selection_non_empty",
        len(selection.get("selected_elements", [])) >= 1,
        f"selected elements={len(selection.get('selected_elements', []))}",
    )
    zones = _zones(selection)
    _check(checks, "selection_has_zone", bool(zones), f"zones/spaces={len(zones)}")
    _check(
        checks,
        "classifications_resolved",
        not selection.get("classification_error") and all(z.get("classifications_available") for z in zones),
        selection.get("classification_error") or "every zone carries a resolved classification",
    )
    unavailable = selection.get("unavailable_properties") or {}
    _check(
        checks,
        "expected_properties_resolvable",
        not unavailable,
        "unsupported/ambiguous: " + (json.dumps(unavailable, sort_keys=True) if unavailable else "none"),
    )

    audit = _audit_evidence(selection, tuple(expected_properties))
    accounted = all(
        len(item["present"]) + len(item["missing"]) == len(expected_properties) for item in audit["elements"]
    )
    _check(
        checks,
        "audit_traceable",
        bool(audit["elements"]) and accounted,
        f"{audit['audited_zone_count']} zone(s), every expected property classified present or missing",
    )

    target = _target_zone(selection, property_name)
    before = (target or {}).get("properties", {}).get(property_name) if target else None
    _check(
        checks,
        "dry_run_before_from_model",
        target is not None and property_name in (target.get("properties") or {}),
        f"before value read from selected element for {property_name}",
    )

    harness = archicad_harness.run_harness(
        endpoint,
        timeout=timeout,
        fixture_fallback=False,
        property_name=property_name,
        proposed_value=proposed_value,
    )
    _check(checks, "harness_ok", harness.get("ok") is True, harness.get("message", "harness returned ok"))
    _check(checks, "mode_live", harness.get("mode") == "live", f"mode={harness.get('mode')}")
    _check(
        checks,
        "no_fixture_fallback",
        "endpoint_error" not in (harness.get("transcript") or {}),
        "no fallback to fixtures was used",
    )
    _check(checks, "mutated_false", harness.get("mutated") is False, f"mutated={harness.get('mutated')}")

    after_selection = model_bridge_demo.live_selected_elements(
        endpoint, timeout=timeout, required_properties=tuple(expected_properties)
    )
    after_target = _target_zone(after_selection, property_name)
    after_value = (after_target or {}).get("properties", {}).get(property_name) if after_target else None
    _check(
        checks,
        "model_unchanged_after_dry_run",
        target is not None and after_target is not None and before == after_value,
        "re-read of the same element returns the same value after the dry run",
    )

    transcript = harness.get("transcript") or {}
    leaks = redaction.find_sensitive(transcript)
    _check(checks, "transcript_redacted", not leaks, f"sensitive findings={leaks}")

    ok = all(item["ok"] for item in checks)
    run = {
        "schema_version": "1.0",
        "run_id": f"PARTNER-PREFLIGHT-{started}",
        "started_at": started,
        "endpoint_kind": endpoint_kind,
        "ok": ok,
        "mode": harness.get("mode"),
        "product_info": product.get("product_info"),
        "checks": checks,
    }
    dry_run_evidence = {
        "schema_version": "1.0",
        "evidence_id": "AED-067-DRY-RUN",
        "issue": 105,
        "run_id": run["run_id"],
        "endpoint_kind": endpoint_kind,
        "mode": harness.get("mode"),
        "element_id": (target or {}).get("element_id"),
        "classification": (target or {}).get("classification"),
        "property_name": property_name,
        "before_sha256": _fingerprint(before),
        "before_source": "live selection read from the bridge",
        "before_is_null": before is None,
        "after": proposed_value,
        "mutated": harness.get("mutated"),
        "model_unchanged_after_dry_run": before == after_value,
        "shareable_diff": harness.get("diff"),
    }
    audit_evidence = {
        "schema_version": "1.0",
        "evidence_id": "AED-077-AUDIT",
        "issue": 115,
        "run_id": run["run_id"],
        "endpoint_kind": endpoint_kind,
        "mode": harness.get("mode"),
        "product_info": product.get("product_info"),
        **audit,
    }
    return {
        "ok": ok,
        "run": run,
        "dry_run_evidence": redaction.redact_artifact(dry_run_evidence),
        "audit_evidence": redaction.redact_artifact(audit_evidence),
        "transcript": transcript,
    }


def write_evidence(result: dict, directory: str = EVIDENCE_DIR) -> list:
    os.makedirs(directory, exist_ok=True)
    written = []
    for name, payload in (
        ("partner-preflight.json", result["run"]),
        ("archicad-dry-run-105.json", result["dry_run_evidence"]),
        ("archicad-audit-115.json", result["audit_evidence"]),
    ):
        path = os.path.join(directory, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write("\n")
        written.append(path)
    return written


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Autonomous Partner Pilot pre-flight (read-only).")
    parser.add_argument("--endpoint", default=None, help="Real Archicad JSON endpoint; omit to use the replay stand-in.")
    parser.add_argument("--property", default=DEFAULT_PROPERTY)
    parser.add_argument("--after", default=DEFAULT_PROPOSED)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--write", action="store_true", help="Write the redacted evidence artifacts.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_preflight(
        endpoint=args.endpoint,
        property_name=args.property,
        proposed_value=args.after,
        timeout=args.timeout,
    )
    if args.write:
        result["written"] = write_evidence(result)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        run = result["run"]
        print(f"Partner pre-flight {'OK' if result['ok'] else 'FAILED'} · endpoint={run['endpoint_kind']} · mode={run['mode']}")
        for check in run["checks"]:
            print(f"  [{'x' if check['ok'] else ' '}] {check['id']}: {check['detail']}")
        for path in result.get("written", []):
            print(f"  wrote {os.path.relpath(path, os.path.dirname(HERE))}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
