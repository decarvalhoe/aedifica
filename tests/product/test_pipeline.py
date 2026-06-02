"""Live parcel pipeline: offline fallback builds a full brief and persists it."""
from __future__ import annotations

from aedifica.pipeline import build_live_brief


def test_build_live_brief_offline_fallback():
    brief = build_live_brief("Place de la Palud, Lausanne", live=False)
    assert brief["mode"] == "fixture"
    assert any(c["state"] == "sourced" for c in brief["claims"])
    assert brief["source_refs"]


def test_intake_persists(client, owner):
    h = owner["headers"]
    client.post("/api/projects", json={"project_id": "LIVE-P", "name": "Live", "commune": "Lausanne"}, headers=h)
    r = client.post("/api/projects/LIVE-P/intake", json={"query": "Place de la Palud, Lausanne", "live": False}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "fixture"
    assert body["persisted"]["claims"] >= 1
    assert "sourced" in body["claim_state_summary"]
    assert body["project"]["claims"] >= 1 and body["project"]["sources"] >= 1
