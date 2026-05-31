#!/usr/bin/env python3
"""Local fixture replay server for the Archicad-shaped JSON bridge.

Serves deterministic product-info and selected-element responses (and injectable
error cases) so the live-adapter path can be exercised in CI without a running
Archicad seat or any external network.

Usage:
    python pilot/replay_server.py --port 8077    # then POST {"command": "GetProductInfo"}
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

import model_bridge_demo  # noqa: E402

DEFAULT_PRODUCT_INFO = {"name": "Archicad", "version": "REPLAY", "buildNumber": "1"}
DEFAULT_MODEL_VERSION = "ARCHICAD-REPLAY"


def default_selection() -> list:
    return model_bridge_demo.inspect_selected_elements()["selected_elements"]


def make_handler(selection=None, product_info=None, fail_command=None):
    selection = selection if selection is not None else default_selection()
    product_info = product_info or DEFAULT_PRODUCT_INFO

    class ReplayHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(raw or "{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid json"})
            command = payload.get("command")
            if fail_command and command == fail_command:
                return self._send(500, {"error": f"injected failure for {command}"})
            if command == "GetProductInfo":
                return self._send(200, {"result": {"productInfo": product_info}})
            if command == "GetSelectedElements":
                return self._send(
                    200,
                    {
                        "result": {
                            "source_model_version": DEFAULT_MODEL_VERSION,
                            "source_model_ref": "replay://archicad",
                            "selected_elements": selection,
                        }
                    },
                )
            return self._send(400, {"error": f"unknown command {command}"})

        def _send(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            return

    return ReplayHandler


def make_server(host: str = "127.0.0.1", port: int = 0, **handler_kwargs) -> HTTPServer:
    return HTTPServer((host, port), make_handler(**handler_kwargs))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the Archicad fixture replay server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8077)
    args = parser.parse_args(argv)
    httpd = make_server(args.host, args.port)
    print(f"Replay server on http://{args.host}:{args.port} (fixture-backed, no external network)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
