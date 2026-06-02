"""Engine + session factory. SQLite in dev (AEDIFICA_DATABASE_URL to override)."""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

DEFAULT_URL = os.environ.get("AEDIFICA_DATABASE_URL", "sqlite:///aedifica.db")


def make_engine(url: str | None = None, echo: bool = False) -> Engine:
    return create_engine(url or DEFAULT_URL, echo=echo, future=True)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
