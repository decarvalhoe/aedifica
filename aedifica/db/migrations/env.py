"""Alembic environment — targets aedifica.db.Base metadata."""
from __future__ import annotations

import os
import sys

from alembic import context
from sqlalchemy import create_engine, pool

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.db.base import Base  # noqa: E402
import aedifica.db.models  # noqa: E402,F401  (registers the tables)

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    return os.environ.get("AEDIFICA_DATABASE_URL") or config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool, future=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
