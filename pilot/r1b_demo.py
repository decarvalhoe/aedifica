#!/usr/bin/env python3
"""R1B end-to-end demo — the workspace counterpart of the R1A agent demo.

One offline command: open the Lausanne fixture project, generate the parcel
brief, render + record the trust-state report, and print a summary. Runs in an
explicit offline FIXTURE MODE against a copy of the fixture so the committed demo
project is never mutated.

Usage:
    python pilot/r1b_demo.py [--json] [--work DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import workspace  # noqa: E402

FIXTURE_PROJECT = os.path.join(HERE, "projects", "demo_lausanne_palud")
FIXTURE_MODE = True


def build_r1b_demo(work_dir: str) -> dict:
    """Copy the fixture project into work_dir, run the R1B pipeline, return a summary."""
    project_dir = os.path.join(work_dir, "demo_lausanne_palud")
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    shutil.copytree(FIXTURE_PROJECT, project_dir)

    brief = workspace.generate_offline_parcel_brief(project_dir, write_report=True)

    with open(workspace.report_index_path(project_dir), encoding="utf-8") as f:
        report_index = json.load(f)
    report_paths = [item["path"] for item in report_index.get("reports", [])]
    route = brief.get("regulatory_route", {})

    return {
        "fixture_mode": FIXTURE_MODE,
        "project_id": brief["project_id"],
        "route_id": route.get("route_id"),
        "active_layers": [layer.get("layer_id") for layer in route.get("active_layers", [])],
        "report_paths": report_paths,
        "report_count": len(report_paths),
        "unknowns_count": len(brief.get("residual_unknowns", [])),
        "evidence_count": len(brief.get("evidence_refs", [])),
        "source_count": len(brief.get("source_refs", [])),
        "freshness_warnings": len(brief.get("freshness_warnings", [])),
        "project_dir": project_dir,
    }


def render_summary(summary: dict) -> str:
    mode = "OFFLINE FIXTURE MODE" if summary["fixture_mode"] else "LIVE MODE"
    lines = [
        f"=== Aedifica R1B workspace demo · {mode} ===",
        f"Project       : {summary['project_id']}",
        f"Active route  : {summary['route_id']} ({', '.join(summary['active_layers'])})",
        f"Reports       : {summary['report_count']} -> {', '.join(summary['report_paths'])}",
        f"Unknowns      : {summary['unknowns_count']} residual (rendered, never as zero)",
        f"Evidence/src  : {summary['evidence_count']} evidence ref(s), {summary['source_count']} source ref(s)",
        f"Freshness     : {summary['freshness_warnings']} pack warning(s)",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Run the offline R1B workspace demo.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--work", default=None, help="Work directory (default: a temp dir).")
    args = parser.parse_args(argv)

    if args.work:
        os.makedirs(args.work, exist_ok=True)
        summary = build_r1b_demo(args.work)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            summary = build_r1b_demo(tmp)
            summary["project_dir"] = "(temporary)"

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_summary(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
