"""Runtime configuration from the environment (12-factor friendly).

All product config comes from env vars so the same image runs in dev (SQLite) and
prod (Postgres) without code changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


@dataclass
class Settings:
    env: str = field(default_factory=lambda: os.environ.get("AEDIFICA_ENV", "dev"))
    database_url: str = field(default_factory=lambda: os.environ.get("AEDIFICA_DATABASE_URL", "sqlite:///aedifica.db"))
    cors_origins: list = field(default_factory=lambda: _csv("AEDIFICA_CORS_ORIGINS", "http://localhost:3000"))
    create_all: bool = field(default_factory=lambda: os.environ.get("AEDIFICA_CREATE_ALL") == "1")

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"


def get_settings() -> Settings:
    return Settings()
