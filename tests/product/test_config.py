"""W3 hardening: readiness, health env, CORS, env-driven config."""
from __future__ import annotations

import os

from aedifica.api.config import get_settings


def test_health_reports_env(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and "env" in r.json()


def test_readiness_checks_db(client):
    r = client.get("/api/ready")
    assert r.status_code == 200 and r.json()["status"] == "ready"


def test_cors_allows_configured_origin(client):
    r = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("AEDIFICA_ENV", "prod")
    monkeypatch.setenv("AEDIFICA_DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("AEDIFICA_CORS_ORIGINS", "https://a.ch, https://b.ch")
    s = get_settings()
    assert s.is_prod and s.database_url.startswith("postgresql+psycopg://")
    assert s.cors_origins == ["https://a.ch", "https://b.ch"]


def test_nomos_feature_flag_defaults_off(monkeypatch):
    monkeypatch.delenv("AEDIFICA_NOMOS_ENABLED", raising=False)
    monkeypatch.delenv("AEDIFICA_NOMOS_BUNDLE_PATH", raising=False)
    s = get_settings()
    assert s.nomos_enabled is False
    assert s.nomos_bundle_path is None
    assert s.features == {"nomos": False}


def test_nomos_feature_flag_can_be_enabled_from_env(monkeypatch):
    monkeypatch.setenv("AEDIFICA_NOMOS_ENABLED", "1")
    monkeypatch.setenv("AEDIFICA_NOMOS_BUNDLE_PATH", "/tmp/nomos-bundle")
    s = get_settings()
    assert s.nomos_enabled is True
    assert s.nomos_bundle_path == "/tmp/nomos-bundle"
    assert s.features == {"nomos": True}


def test_health_exposes_nomos_flag_off_by_default(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["features"]["nomos"] is False
