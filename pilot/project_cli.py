#!/usr/bin/env python3
"""Create and open an Aedifica project workspace from the command line.

This is the one stable way an architect creates or re-opens a pilot project.
The CLI is a thin wrapper over the workspace + route services; the core
functions (``create_project`` / ``open_project``) are importable and covered by
``pilot/selfcheck.py``.

Usage:
    python pilot/project_cli.py create --id LAUSANNE-PALUD-2 --name "Palud 2" \\
        --country CH --canton VD --commune Lausanne --phase 0 [--root DIR]
    python pilot/project_cli.py open path/to/project_dir
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import selector  # noqa: E402
import trust  # noqa: E402
import validate_manifest  # noqa: E402
import workspace  # noqa: E402

DEFAULT_ROOT = workspace.PROJECTS_DIR
DEFAULT_CLAIM_STATES = ["sourced", "computed", "assumption", "unknown", "conflict", "decision"]


class ProjectCLIError(Exception):
    """Structured CLI error with a machine-readable code."""

    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_manifest(
    project_id: str,
    name: str,
    country: str = "CH",
    canton: str = "VD",
    commune: str = "Lausanne",
    phase_code: str = "0",
    knowledge_regime: str = "context_first",
    parcel: dict | None = None,
    language: str = "fr",
    selected_at: str | None = None,
) -> dict:
    selected_at = selected_at or _now_iso()
    route = selector.regulatory_route(country, canton, commune, selected_at=selected_at, evaluated_at=selected_at)
    manifest = {
        "schema_version": workspace.WORKSPACE_VERSION,
        "project_id": project_id,
        "name": name,
        "phase_code": phase_code,
        "knowledge_regime": knowledge_regime,
        "jurisdiction": {"country": country, "canton": canton, "commune": commune},
        "regulatory_route": route,
        "trust_contract": {
            "language": language,
            "footer_required": True,
            "required_claim_states": DEFAULT_CLAIM_STATES,
        },
    }
    if parcel:
        manifest["parcel"] = parcel
    return manifest


def create_project(root: str = DEFAULT_ROOT, **manifest_kwargs) -> dict:
    """Build a valid manifest and write the project workspace. Returns a summary."""
    manifest = build_manifest(**manifest_kwargs)
    schema_errors = validate_manifest.validate_manifest(manifest)
    if schema_errors:
        raise ProjectCLIError("INVALID_MANIFEST", "Manifest failed schema validation.", errors=schema_errors)
    project_dir = workspace.create_project_workspace(root, manifest)
    project_report = workspace.validate_project(project_dir)
    if project_report.errors:
        raise ProjectCLIError(
            "INVALID_WORKSPACE",
            "Created workspace failed validation.",
            errors=project_report.errors,
        )
    return {
        "project_id": manifest["project_id"],
        "project_dir": project_dir,
        "phase_code": manifest["phase_code"],
        "route_id": manifest["regulatory_route"]["route_id"],
    }


def open_project(project_dir: str) -> dict:
    """Read and validate an existing project. Returns a structured summary."""
    if not os.path.isdir(project_dir):
        raise ProjectCLIError("PROJECT_NOT_FOUND", "Project directory does not exist.", project_dir=project_dir)
    manifest_path = workspace.project_manifest_path(project_dir)
    if not os.path.exists(manifest_path):
        raise ProjectCLIError("MISSING_MANIFEST", "Project folder has no project.json.", project_dir=project_dir)
    report = workspace.validate_project(project_dir)
    if report.errors:
        raise ProjectCLIError("INVALID_PROJECT", "Project failed validation.", errors=report.errors)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    route = manifest.get("regulatory_route", {})
    artifacts_summary = _known_artifacts(project_dir)
    return {
        "project_id": manifest.get("project_id"),
        "name": manifest.get("name"),
        "phase_code": manifest.get("phase_code"),
        "jurisdiction": manifest.get("jurisdiction", {}),
        "route_id": route.get("route_id"),
        "active_layers": [layer.get("layer_id") for layer in route.get("active_layers", [])],
        "freshness_warnings": selector.pack_freshness_warnings(route),
        "artifacts": artifacts_summary,
    }


def _known_artifacts(project_dir: str) -> dict:
    reports = []
    index_path = workspace.report_index_path(project_dir)
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            reports = [item.get("report_id") for item in json.load(f).get("reports", [])]

    def _count(subdir: str) -> int:
        path = os.path.join(project_dir, subdir)
        if not os.path.isdir(path):
            return 0
        return sum(1 for name in os.listdir(path) if not name.startswith("."))

    return {
        "reports": reports,
        "report_count": len(reports),
        "source_count": _count("sources"),
        "evidence_count": _count("evidence"),
        "memory_count": _count("memory"),
    }


def render_open_summary(summary: dict) -> str:
    lines = [
        f"Project   : {summary['project_id']} — {summary.get('name')}",
        f"Phase     : {summary['phase_code']}",
        f"Route     : {summary['route_id']} ({', '.join(summary['active_layers'])})",
        f"Artifacts : {summary['artifacts']['report_count']} report(s), "
        f"{summary['artifacts']['evidence_count']} evidence, {summary['artifacts']['memory_count']} memory",
    ]
    for warning in summary.get("freshness_warnings", []):
        lines.append(f"  ! {warning['layer_id']}: {warning['message']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Create or open an Aedifica project workspace.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a new project workspace.")
    create.add_argument("--id", required=True, dest="project_id")
    create.add_argument("--name", required=True)
    create.add_argument("--country", default="CH")
    create.add_argument("--canton", default="VD")
    create.add_argument("--commune", default="Lausanne")
    create.add_argument("--phase", default="0", dest="phase_code")
    create.add_argument("--root", default=DEFAULT_ROOT)

    open_parser = sub.add_parser("open", help="Open and validate an existing project workspace.")
    open_parser.add_argument("project_dir")

    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create_project(
                root=args.root,
                project_id=args.project_id,
                name=args.name,
                country=args.country,
                canton=args.canton,
                commune=args.commune,
                phase_code=args.phase_code,
            )
            print(f"Created project {result['project_id']} at {result['project_dir']}")
            print(f"Route: {result['route_id']}")
            return 0
        if args.command == "open":
            summary = open_project(args.project_dir)
            print(render_open_summary(summary))
            return 0
    except ProjectCLIError as exc:
        print(f"ERROR [{exc.code}] {exc.message}", file=sys.stderr)
        for detail in exc.details.get("errors", []):
            print(f"  - {detail}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
