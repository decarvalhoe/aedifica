"""Alembic migration smoke tests for additive product schema changes."""
from __future__ import annotations

import os
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def test_w19_02_adds_facet_columns_to_claim_and_source(tmp_path):
    db_path = tmp_path / "aedifica.sqlite"
    cfg = Config(os.path.join(ROOT, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    inspector = inspect(engine)
    claim_columns = {column["name"] for column in inspector.get_columns("claim")}
    source_columns = {column["name"] for column in inspector.get_columns("source")}
    assert {"trust_tier", "provenance", "facets"}.issubset(claim_columns)
    assert {"trust_tier", "provenance", "facets"}.issubset(source_columns)
