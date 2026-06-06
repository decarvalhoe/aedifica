"""W12.C — LLM opt-in scaffolding.

Tests the doctrine, not the model: a fake backend is injected so we can
verify (a) llm_mode gates the call, (b) confidential entries are
filtered out in cloud mode, (c) every call is audited, (d) the LLM
output becomes a Proposal that the architect must decide on.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def fake_llm():
    """Register a deterministic backend for tests; restore after."""
    from aedifica.foresight import llm
    calls = []

    def backend(mode: str, prompt: str) -> str:
        calls.append({"mode": mode, "prompt_len": len(prompt)})
        return f"Résumé fictif ({mode}, {len(prompt)} caractères)"

    old = llm.get_backend()
    llm.set_backend(backend)
    yield calls
    llm.set_backend(old)


def _project(client, h, pid="LLM1"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": "Lausanne"}, headers=h)
    return pid


def _brs(client, h, pid, content="exigence", channel="email", kind="requirement"):
    return client.post(f"/api/projects/{pid}/brs",
                       json={"content": content, "channel": channel, "kind": kind},
                       headers=h).json()


def test_llm_mode_default_is_off(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    r = client.post(f"/api/projects/{pid}/foresight/llm/brs-summary", headers=h)
    assert r.status_code == 400
    assert "LLM_OFF" in r.text


def test_flip_to_local_then_call(client, owner, fake_llm):
    h = owner["headers"]; pid = _project(client, h)
    _brs(client, h, pid, content="Sécuriser le PV de coordination", channel="email")
    r = client.patch(f"/api/projects/{pid}/llm-mode", json={"mode": "local"}, headers=h)
    assert r.status_code == 200
    assert r.json()["llm_mode"] == "local"
    rr = client.post(f"/api/projects/{pid}/foresight/llm/brs-summary", headers=h)
    assert rr.status_code == 201
    p = rr.json()["proposal"]
    assert p["kind"] == "brs_summary"
    assert "Résumé fictif" in p["detail"]
    assert p["confidence"] == 0.0  # LLM output never carries built-in confidence
    assert fake_llm[0]["mode"] == "local"


def test_cloud_mode_filters_pv_channel(client, owner, fake_llm):
    h = owner["headers"]; pid = _project(client, h)
    _brs(client, h, pid, content="Spec routine", channel="email")
    _brs(client, h, pid, content="PV confidentiel", channel="pv")
    client.patch(f"/api/projects/{pid}/llm-mode", json={"mode": "cloud"}, headers=h)
    r = client.post(f"/api/projects/{pid}/foresight/llm/brs-summary", headers=h).json()
    # Only the email BRS should be referenced in basis.
    basis = r["proposal"]["basis"]
    assert len(basis) == 1
    assert basis[0]["source_kind"] == "brs"


def test_flip_and_call_audited(client, owner, fake_llm):
    h = owner["headers"]; pid = _project(client, h)
    _brs(client, h, pid)
    client.patch(f"/api/projects/{pid}/llm-mode", json={"mode": "local"}, headers=h)
    client.post(f"/api/projects/{pid}/foresight/llm/brs-summary", headers=h)
    audit = client.get(f"/api/projects/{pid}/audit", headers=h).json()
    kinds = [e["event_type"] for e in audit["events"]]
    assert "llm_mode_changed" in kinds
    assert "llm_called" in kinds


def test_bad_mode_400(client, owner):
    h = owner["headers"]; pid = _project(client, h)
    r = client.patch(f"/api/projects/{pid}/llm-mode", json={"mode": "magique"}, headers=h)
    assert r.status_code == 400


def test_no_brs_returns_503(client, owner, fake_llm):
    h = owner["headers"]; pid = _project(client, h)
    client.patch(f"/api/projects/{pid}/llm-mode", json={"mode": "local"}, headers=h)
    r = client.post(f"/api/projects/{pid}/foresight/llm/brs-summary", headers=h)
    assert r.status_code == 503
