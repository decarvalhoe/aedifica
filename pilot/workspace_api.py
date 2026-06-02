#!/usr/bin/env python3
"""Local-first workspace HTTP API slice (stdlib only).

Gives the UI and future agent flows a stable local API instead of importing
pilot scripts directly. The routing logic lives in ``route_request`` so it is
unit-testable without a socket; ``serve`` wraps it in ``http.server``.

This is explicitly a LOCAL, non-production surface: there is no auth, and it must
not be exposed to a network. Run against offline fixture projects.

Endpoints:
    GET  /api/health                      -> {"status": "ok"}
    GET  /api/projects                    -> {"projects": [...]}
    GET  /api/projects/<id>               -> open/validate summary
    POST /api/projects                    -> create project (json body)
    POST /api/projects/<id>/brief         -> generate brief + report, summary

Usage:
    python pilot/workspace_api.py --port 8088 --root <projects_dir>
    curl -s localhost:8088/api/health
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import project_cli  # noqa: E402
import workspace  # noqa: E402

API_VERSION = "1.0"


def _error(code: str, message: str, status: int = 400, **details):
    return status, {"error": {"code": code, "message": message, "details": details}}


def _project_dir(root: str, project_id: str) -> str:
    """Resolve a project folder by id.

    Created projects live in ``<id>.lower()``; fixtures may use a different folder
    name, so fall back to scanning manifests for a matching ``project_id``.
    """
    direct = os.path.join(root, (project_id or "").lower())
    if os.path.exists(workspace.project_manifest_path(direct)):
        return direct
    for candidate in workspace.iter_project_dirs(root):
        try:
            with open(workspace.project_manifest_path(candidate), encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("project_id") == project_id:
            return candidate
    return direct


def route_request(method: str, path: str, body: dict | None, root: str):
    """Pure router: returns (http_status, json_dict). No socket involved."""
    parts = [segment for segment in path.split("?")[0].strip("/").split("/") if segment]

    if parts == ["api", "health"] and method == "GET":
        return 200, {"status": "ok", "api_version": API_VERSION, "root": os.path.basename(root)}

    if parts == ["api", "projects"]:
        if method == "GET":
            projects = [os.path.basename(p) for p in workspace.iter_project_dirs(root)]
            return 200, {"projects": projects}
        if method == "POST":
            body = body or {}
            missing = [k for k in ("project_id", "name") if not body.get(k)]
            if missing:
                return _error("MISSING_FIELDS", f"Missing required fields: {missing}", 400, fields=missing)
            try:
                result = project_cli.create_project(
                    root=root,
                    project_id=body["project_id"],
                    name=body["name"],
                    country=body.get("country", "CH"),
                    canton=body.get("canton", "VD"),
                    commune=body.get("commune", "Lausanne"),
                    phase_code=body.get("phase", "0"),
                )
                return 201, {"created": result}
            except project_cli.ProjectCLIError as exc:
                return _error(exc.code, exc.message, 400, **exc.details)

    if len(parts) >= 3 and parts[0] == "api" and parts[1] == "projects":
        project_id = parts[2]
        project_dir = _project_dir(root, project_id)
        if len(parts) == 3 and method == "GET":
            try:
                return 200, {"project": project_cli.open_project(project_dir)}
            except project_cli.ProjectCLIError as exc:
                status = 404 if exc.code in {"PROJECT_NOT_FOUND", "MISSING_MANIFEST"} else 400
                return _error(exc.code, exc.message, status, **exc.details)
        if len(parts) == 4 and parts[3] == "brief" and method == "POST":
            if not os.path.isdir(project_dir):
                return _error("PROJECT_NOT_FOUND", "Project does not exist.", 404, project_id=project_id)
            brief = workspace.generate_offline_parcel_brief(project_dir, write_report=True)
            return 200, {
                "brief_id": brief["brief_id"],
                "project_id": brief["project_id"],
                "claim_state_summary": brief["claim_state_summary"],
                "unknowns_count": len(brief.get("residual_unknowns", [])),
                "source_count": len(brief.get("source_refs", [])),
            }

    return _error("NOT_FOUND", f"No route for {method} {path}", 404)


def make_handler(root: str):
    class WorkspaceAPIHandler(BaseHTTPRequestHandler):
        def _respond(self, method: str):
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            try:
                body = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                status, payload = _error("INVALID_JSON", "Request body is not valid JSON.", 400)
            else:
                status, payload = route_request(method, self.path, body, root)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._respond("GET")

        def do_POST(self):
            self._respond("POST")

        def log_message(self, *_args):
            return

    return WorkspaceAPIHandler


def serve(host: str = "127.0.0.1", port: int = 8088, root: str = workspace.PROJECTS_DIR) -> HTTPServer:
    return HTTPServer((host, port), make_handler(root))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the local workspace API (non-production).")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    parser.add_argument("--root", default=workspace.PROJECTS_DIR)
    args = parser.parse_args(argv)
    httpd = serve(args.host, args.port, args.root)
    print(f"Aedifica workspace API on http://{args.host}:{args.port} (root={args.root}) — local only, no auth")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
