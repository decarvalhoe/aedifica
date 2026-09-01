#!/usr/bin/env python3
"""Local fixture replay server for the Archicad-shaped JSON bridge.

Serves deterministic product-info and selected-element responses (and injectable
error cases) so the live-adapter path can be exercised in CI without a running
Archicad seat or any external network.

Usage:
    python pilot/replay_server.py --port 8077    # then POST {"command": "API.GetProductInfo"}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import model_bridge_demo  # noqa: E402

DEFAULT_PRODUCT_INFO = {"version": 29, "buildNumber": 3000, "languageCode": "FRA"}
DEFAULT_MODEL_VERSION = "ARCHICAD-REPLAY"
API_FIXTURE = os.path.join(HERE, "model", "archicad_json_api_fixture.json")
CLASSIFICATION_SYSTEM_ID = "33333333-3333-3333-3333-333333333333"


def default_selection() -> list:
    return model_bridge_demo.inspect_selected_elements()["selected_elements"]


def _property_id(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"aedifica.archicad-property:{name}"))


def _guid_value(value):
    return value.get("guid") if isinstance(value, dict) else None


def make_handler(
    selection=None,
    product_info=None,
    fail_command=None,
    command_log=None,
    payload_log=None,
    available_property_names=None,
):
    fixture_mode = (
        selection is None
        and product_info is None
        and available_property_names is None
    )
    selection = selection if selection is not None else default_selection()
    product_info = product_info or DEFAULT_PRODUCT_INFO
    with open(API_FIXTURE, encoding="utf-8") as f:
        fixture_responses = json.load(f)["responses"]
    property_names = (
        list(available_property_names)
        if available_property_names is not None
        else list(
            dict.fromkeys(
                (
                    *model_bridge_demo.REQUIRED_SPACE_PROPERTIES,
                    *(name for item in selection for name in (item.get("properties") or {})),
                )
            )
        )
    )
    property_ids = {name: _property_id(name) for name in property_names}
    classification_ids = {
        item.get("classification"): str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"aedifica.archicad-classification:{item.get('classification')}")
        )
        for item in selection
        if item.get("classification")
    }

    class ReplayHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            try:
                payload = json.loads(raw or "{}")
            except json.JSONDecodeError:
                return self._send(400, {"error": "invalid json"})
            command = payload.get("command")
            if command_log is not None:
                command_log.append(command)
            if payload_log is not None:
                payload_log.append(payload)
            if fail_command and command == fail_command:
                return self._send(500, {"error": f"injected failure for {command}"})
            if fixture_mode and command in fixture_responses:
                return self._send(200, fixture_responses[command])
            if command == "API.GetProductInfo":
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "version": product_info.get("version"),
                            "buildNumber": product_info.get("buildNumber"),
                            "languageCode": product_info.get("languageCode", "FRA"),
                        },
                    },
                )
            if command == "API.GetSelectedElements":
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "elements": [
                                {"elementId": {"guid": item.get("element_id")}}
                                for item in selection
                            ]
                        }
                    },
                )
            if command == "API.GetTypesOfElements":
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "typesOfElements": [
                                {
                                    "typeOfElement": {
                                        "elementId": {"guid": item.get("element_id")},
                                        "elementType": item.get("type"),
                                    }
                                }
                                for item in selection
                            ]
                        },
                    },
                )
            if command == "API.GetAllClassificationSystems":
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "classificationSystems": [
                                {
                                    "classificationSystemId": {"guid": CLASSIFICATION_SYSTEM_ID},
                                    "name": "Aedifica Replay Classification",
                                    "description": "Synthetic classification fixture",
                                    "source": "aedifica.local",
                                    "version": "1",
                                    "date": "2026-01-01",
                                }
                            ]
                        },
                    },
                )
            if command == "API.GetClassificationsOfElements":
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "elementClassifications": [
                                {
                                    "classificationIds": [
                                        {
                                            "classificationId": {
                                                "classificationSystemId": {"guid": CLASSIFICATION_SYSTEM_ID},
                                                "classificationItemId": {
                                                    "guid": classification_ids[item.get("classification")]
                                                },
                                            }
                                        }
                                    ]
                                    if item.get("classification") in classification_ids
                                    else []
                                }
                                for item in selection
                            ]
                        },
                    },
                )
            if command == "API.GetDetailsOfClassificationItems":
                requested = (payload.get("parameters") or {}).get("classificationItemIds") or []
                names_by_id = {guid: name for name, guid in classification_ids.items()}
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "classificationItems": [
                                {
                                    "classificationItem": {
                                        "classificationItemId": item.get("classificationItemId"),
                                        "id": names_by_id.get(_guid_value(item.get("classificationItemId"))),
                                        "name": names_by_id.get(_guid_value(item.get("classificationItemId"))),
                                        "description": "Synthetic replay classification",
                                    }
                                }
                                for item in requested
                            ]
                        },
                    },
                )
            if command == "API.GetAllPropertyNames":
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "properties": [
                                {"type": "UserDefined", "localizedName": ["Aedifica", name]}
                                for name in property_names
                            ]
                        },
                    },
                )
            if command == "API.GetPropertyIds":
                requested = (payload.get("parameters") or {}).get("properties") or []
                return self._send(
                    200,
                    {
                        "succeeded": True,
                        "result": {
                            "properties": [
                                {"propertyId": {"guid": property_ids.get((item.get("localizedName") or [None])[-1], "")}}
                                for item in requested
                            ]
                        },
                    },
                )
            if command == "API.GetPropertyValuesOfElements":
                requested = (payload.get("parameters") or {}).get("properties") or []
                id_to_name = {value: name for name, value in property_ids.items()}
                requested_names = [id_to_name.get((item.get("propertyId") or {}).get("guid")) for item in requested]
                rows = []
                for item in selection:
                    values = []
                    current = item.get("properties") or {}
                    for name in requested_names:
                        value = current.get(name)
                        status = ((item.get("property_states") or {}).get(name) or {}).get("status")
                        if status and status not in {"normal", "userUndefined"}:
                            property_value = {"type": "string", "status": status}
                        else:
                            property_value = {"type": "string", "status": "normal", "value": value} if value is not None else {"type": "string", "status": "userUndefined"}
                        values.append({"propertyValue": property_value})
                    rows.append({"propertyValues": values})
                return self._send(200, {"succeeded": True, "result": {"propertyValuesForElements": rows}})
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
