#!/usr/bin/env python3
"""Validate the pack freshness gate for generated reports (stdlib, offline).

Checks that an expired pack review_due and a stale source valid_as_of both raise
visible, non-blocking warnings — in the structured output and in the rendered
report — while a fresh route stays clean. Uses an explicit ``today`` so the gate
is deterministic regardless of the machine clock.

Run:
    python pilot/validate_freshness.py
"""
from dataclasses import dataclass, field
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import selector  # noqa: E402
import workspace  # noqa: E402

TODAY = "2026-05-31"
DEMO_PROJECT = os.path.join(HERE, "projects", "demo_lausanne_palud")


@dataclass
class FreshnessReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def validate_all() -> FreshnessReport:
    report = FreshnessReport()
    route = selector.regulatory_route("CH", "VD", "Lausanne")

    # Fresh route + fresh source -> no overdue/stale warnings.
    fresh = selector.report_freshness_warnings(
        route, [{"source_id": "VD-OEREB", "valid_as_of": "2026-05-29"}], today=TODAY
    )
    if any(w["code"] in {"pack_review_overdue", "source_stale"} for w in fresh):
        report.add_error(f"fresh route should produce no overdue/stale warnings, got {fresh}")

    # Expired pack review_due -> visible warning.
    stale_route = json.loads(json.dumps(route))
    stale_route["active_layers"][0]["source_version"]["review_due"] = "2000-01-01"
    expired = selector.report_freshness_warnings(stale_route, [], today=TODAY)
    if not any(w["code"] == "pack_review_overdue" for w in expired):
        report.add_error("expired pack review_due must produce a pack_review_overdue warning")

    # Stale source valid_as_of -> visible warning.
    stale_sources = selector.source_freshness_warnings(
        [{"source_id": "OLD-SRC", "valid_as_of": "2000-01-01"}], today=TODAY
    )
    if not any(w["code"] == "source_stale" for w in stale_sources):
        report.add_error("stale source valid_as_of must produce a source_stale warning")

    # Warnings appear in the rendered report; a clean brief does not show them.
    brief = workspace.generate_offline_parcel_brief(DEMO_PROJECT)
    clean_brief = json.loads(json.dumps(brief))
    clean_brief["freshness_warnings"] = []
    if "Avertissements" in workspace.render_brief_html(clean_brief):
        report.add_error("a brief with no freshness warnings must not render the warnings block")
    warned_brief = json.loads(json.dumps(brief))
    warned_brief["freshness_warnings"] = [
        {"severity": "warning", "code": "pack_review_overdue", "layer_id": "Lausanne/communal", "message": "Pack review overdue"}
    ]
    if "Avertissements" not in workspace.render_brief_html(warned_brief):
        report.add_error("a brief with freshness warnings must render the warnings block")

    report.items.append(
        {
            "fresh_warnings": len(fresh),
            "expired_warnings": len(expired),
            "stale_source_warnings": len(stale_sources),
        }
    )
    return report


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    report = validate_all()
    for item in report.items:
        print(f"PASS? fresh={item['fresh_warnings']} expired={item['expired_warnings']} stale_src={item['stale_source_warnings']}")
    if report.errors:
        print("\nFreshness gate validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\npack freshness gate validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
