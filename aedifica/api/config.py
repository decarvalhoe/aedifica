"""Runtime configuration from the environment (12-factor friendly).

All product config comes from env vars so the same image runs in dev (SQLite) and
prod (Postgres) without code changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _optional(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@dataclass
class Settings:
    env: str = field(default_factory=lambda: os.environ.get("AEDIFICA_ENV", "dev"))
    database_url: str = field(default_factory=lambda: os.environ.get("AEDIFICA_DATABASE_URL", "sqlite:///aedifica.db"))
    cors_origins: list = field(default_factory=lambda: _csv("AEDIFICA_CORS_ORIGINS", "http://localhost:3000"))
    create_all: bool = field(default_factory=lambda: os.environ.get("AEDIFICA_CREATE_ALL") == "1")
    nomos_enabled: bool = field(default_factory=lambda: _bool("AEDIFICA_NOMOS_ENABLED", False))
    nomos_bundle_path: str | None = field(default_factory=lambda: _optional("AEDIFICA_NOMOS_BUNDLE_PATH"))
    # W23-6 — seed a fully-functional demo atelier on boot (Fly demo opts in).
    seed_demo: bool = field(default_factory=lambda: _bool("AEDIFICA_SEED_DEMO", False))

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    @property
    def features(self) -> dict[str, bool]:
        return {"nomos": self.nomos_enabled}


def get_settings() -> Settings:
    return Settings()
