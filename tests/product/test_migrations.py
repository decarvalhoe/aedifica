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


def test_w19_03_adds_lens_chunk_tables(tmp_path):
    db_path = tmp_path / "aedifica.sqlite"
    cfg = Config(os.path.join(ROOT, "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

    command.upgrade(cfg, "head")

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    inspector = inspect(engine)
    assert {"project_knowledge_chunk", "jurisdiction_knowledge_chunk"}.issubset(set(inspector.get_table_names()))
    project_columns = {column["name"] for column in inspector.get_columns("project_knowledge_chunk")}
    jurisdiction_columns = {column["name"] for column in inspector.get_columns("jurisdiction_knowledge_chunk")}
    expected = {"chunk_id", "text", "source_hash", "source_path", "span", "facets", "embedding"}
    assert {"project_id", *expected}.issubset(project_columns)
    assert {"country", "canton", "commune", *expected}.issubset(jurisdiction_columns)


def test_w19_03_migration_scaffolds_pgvector_and_project_rls():
    migration = os.path.join(ROOT, "aedifica", "db", "migrations", "versions", "j4f7a2c9d8e3_w19_03_lens_chunks.py")
    with open(migration, encoding="utf-8") as f:
        text = f.read()

    assert "CREATE EXTENSION IF NOT EXISTS vector" in text
    assert "ALTER TABLE project_knowledge_chunk ENABLE ROW LEVEL SECURITY" in text
    assert "CREATE POLICY project_knowledge_chunk_project_isolation" in text
