"""The demo seed must fit its own schema on a length-enforcing database.

SQLite ignores VARCHAR(n); Postgres raises StringDataRightTruncation. The demo
seed is fail-soft, so an oversized value does not crash the API — it silently
skips the whole seed and the deployed demo comes up empty. These tests catch
that class of defect on the SQLite suite, before a Postgres deployment does.
"""
from __future__ import annotations

import json
import pathlib

from sqlalchemy import String, inspect
from sqlalchemy.orm import sessionmaker as make_sessionmaker

from aedifica.db import models as m
from aedifica.ingestion import service as ingestion

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_static_pack_version_fits_its_column():
    data = json.loads((ROOT / "pilot" / "lausanne" / "rpga_zones.json").read_text(encoding="utf-8"))
    prose = data["document"]["version"]
    assert len(prose) > 40, "fixture must still carry the long legal statement this guards"

    version = ingestion._pack_version_id(data["document"], data["source_version"])

    assert len(version) <= 40
    assert version  # never empty: it is half of a unique key


def test_static_pack_version_is_stable_and_keeps_the_statement(engine):
    """Re-seeding must not create a second pack, and the prose must survive."""
    with make_sessionmaker(bind=engine)() as s:
        ingestion.seed_from_static(s)
        s.commit()
        first = s.query(m.CommunePack).filter_by(commune="Lausanne").all()
        ingestion.seed_from_static(s)
        s.commit()
        second = s.query(m.CommunePack).filter_by(commune="Lausanne").all()

        assert len(first) == len(second) == 1, "re-seeding must be idempotent on the unique key"
        pack = second[0]
        assert len(pack.version) <= 40
        assert pack.data.get("document_version", "").startswith("Mis en vigueur")


def _string_columns(model):
    for column in inspect(model).columns:
        if isinstance(column.type, String) and column.type.length:
            yield column.name, column.type.length


def test_every_seeded_string_fits_its_column(engine, monkeypatch):
    """Run the full demo seed, then audit every stored string against its schema."""
    monkeypatch.setenv("AEDIFICA_SEED_DEMO", "true")
    from aedifica.api import seed_demo  # noqa: PLC0415

    sessionmaker = make_sessionmaker(bind=engine)
    seed_demo.maybe_seed_demo(sessionmaker, nomos_enabled=False)

    overflows = []
    with sessionmaker() as session:
        for model in (m.CommunePack, m.Org, m.User, m.Project, m.Intervenant, m.Document, m.CaptureNote):
            limits = dict(_string_columns(model))
            for row in session.query(model).all():
                for name, limit in limits.items():
                    value = getattr(row, name, None)
                    if isinstance(value, str) and len(value) > limit:
                        overflows.append(f"{model.__tablename__}.{name}: {len(value)} > {limit}")

    assert overflows == [], "these values would be rejected by Postgres: " + "; ".join(overflows)
