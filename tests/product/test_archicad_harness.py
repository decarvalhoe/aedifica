"""Read-only Archicad harness against the official-shaped replay contract."""
from __future__ import annotations

from contextlib import contextmanager
import threading

from aedifica import _bootstrap  # noqa: F401

import archicad_harness  # noqa: E402
import model_bridge_demo  # noqa: E402
import redaction  # noqa: E402
import replay_server  # noqa: E402


@contextmanager
def running_replay(**kwargs):
    server = replay_server.make_server("127.0.0.1", 0, **kwargs)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_live_harness_uses_official_read_commands_and_real_before_value(monkeypatch):
    commands = []
    captured = {}
    selection = [
        {
            "element_id": "00000000-0000-0000-0000-000000000101",
            "type": "Zone",
            "classification": "IfcSpace",
            "properties": {"RoomUsage": "meeting", "SIA416SurfaceType": None},
        }
    ]
    real_dry_run = model_bridge_demo.dry_run_property_update

    def capture_before(*args, **kwargs):
        captured["before"] = kwargs.get("before")
        return real_dry_run(*args, **kwargs)

    monkeypatch.setattr(model_bridge_demo, "dry_run_property_update", capture_before)
    with running_replay(selection=selection, command_log=commands) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is True
    assert result["mode"] == "live"
    assert result["mutated"] is False
    assert result["diff"] == {
        "element_id": selection[0]["element_id"],
        "property_name": "RoomUsage",
        "before": "[redacted]",
        "after": "[redacted]",
    }
    assert captured["before"] == "meeting"
    assert commands == [
        "API.GetProductInfo",
        "API.GetSelectedElements",
        "API.GetTypesOfElements",
        "API.GetAllClassificationSystems",
        "API.GetClassificationsOfElements",
        "API.GetDetailsOfClassificationItems",
        "API.GetAllPropertyNames",
        "API.GetPropertyIds",
        "API.GetPropertyValuesOfElements",
    ]
    assert redaction.find_sensitive(result["transcript"]) == []


def test_live_harness_fails_without_fallback_when_endpoint_is_unavailable():
    result = archicad_harness.run_harness(
        "http://127.0.0.1:1",
        timeout=0.1,
        fixture_fallback=False,
    )

    assert result["ok"] is False
    assert result["mode"] == "unavailable"
    assert "endpoint unavailable" in result["message"]


def test_live_harness_fails_on_empty_selection():
    with running_replay(selection=[]) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is False
    assert result["mode"] == "unavailable"
    assert "no selected element" in result["message"]


def test_live_harness_reports_an_absent_property_as_none_before():
    selection = [
        {
            "element_id": "00000000-0000-0000-0000-000000000102",
            "type": "Zone",
            "classification": "IfcSpace",
            "properties": {"SIA416SurfaceType": "SUP"},
        }
    ]
    with running_replay(selection=selection) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is True
    assert result["diff"]["before"] is None
    assert result["diff"]["after"] == "[redacted]"
    assert result["audit_count"] == 1


def test_live_harness_rejects_a_selection_without_a_space():
    selection = [
        {
            "element_id": "00000000-0000-0000-0000-000000000001",
            "type": "Wall",
            "classification": "IfcWall",
            "properties": {"RoomUsage": None},
        }
    ]
    with running_replay(selection=selection) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is False
    assert "no Archicad Zone/IfcSpace" in result["message"]


def test_live_harness_rejects_missing_property_definition():
    with running_replay(available_property_names=["SIA416SurfaceType"]) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is False
    assert "required properties are unavailable: RoomUsage" in result["message"]


def test_live_harness_rejects_ambiguous_property_name():
    with running_replay(
        available_property_names=["RoomUsage", "RoomUsage", "SIA416SurfaceType"]
    ) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is False
    assert "required properties are unavailable: RoomUsage" in result["message"]


def test_live_harness_rejects_unreadable_property_value():
    selection = [
        {
            "element_id": "00000000-0000-0000-0000-000000000103",
            "type": "Zone",
            "classification": "IfcSpace",
            "properties": {"RoomUsage": None, "SIA416SurfaceType": "SUP"},
            "property_states": {"RoomUsage": {"status": "notAvailable"}},
        }
    ]
    with running_replay(selection=selection) as endpoint:
        result = archicad_harness.run_harness(endpoint, fixture_fallback=False)

    assert result["ok"] is False
    assert "property values are unavailable" in result["message"]


def test_property_values_preserve_selection_order_for_mixed_types():
    payloads = []
    selection = [
        {
            "element_id": "00000000-0000-0000-0000-000000000001",
            "type": "Wall",
            "classification": "IfcWall",
            "properties": {"RoomUsage": "wall", "SIA416SurfaceType": None},
        },
        {
            "element_id": "00000000-0000-0000-0000-000000000104",
            "type": "Zone",
            "classification": "IfcSpace",
            "properties": {"RoomUsage": "meeting", "SIA416SurfaceType": None},
        },
    ]
    with running_replay(selection=selection, payload_log=payloads) as endpoint:
        live = model_bridge_demo.live_selected_elements(endpoint)

    values_payload = next(
        payload for payload in payloads if payload["command"] == "API.GetPropertyValuesOfElements"
    )
    assert values_payload["parameters"]["onlySupportedTypes"] is False
    assert live["selected_elements"][1]["properties"]["RoomUsage"] == "meeting"


def test_redaction_rejects_an_identifier_that_contains_contact_data():
    artifact = {"element_id": "client@example.com", "before": "Client Dupont", "after": "Office"}
    redacted = redaction.redact_artifact(artifact)

    assert redacted == {"element_id": "[redacted]", "before": "[redacted]", "after": "[redacted]"}
    assert redaction.find_sensitive(redacted) == []
