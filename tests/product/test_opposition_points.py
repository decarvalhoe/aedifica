"""W21-4 — targeted opposition points derived from the dossier (no invented severity).

Etienne's critique of the generic radar (« c'est toujours élevé… ça ne
m'apprend rien ») is redressed by points that are each anchored to something
verifiable: a claim in conflict, an unsourced neighbor-sensitive claim, the
canonical coverage of the validated pieces. These tests prove the derivation
is mechanical — and that NOTHING fires on a clean dossier.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import reports  # noqa: E402
from aedifica.db import Base, Claim, Org, Project, User, make_engine, make_session_factory  # noqa: E402
from aedifica.db.models import Document  # noqa: E402


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def _project(session) -> Project:
    org = Org(name="Atelier Opposition")
    session.add(org)
    session.flush()
    session.add(User(org_id=org.id, email="owner@test.ch", name="Owner", role="owner"))
    project = Project(org_id=org.id, project_id="P-OPP", name="Rue Centrale", commune="Lausanne", canton="VD")
    session.add(project)
    session.flush()
    return project


def _claim(project, claim_id: str, title: str, state: str, **kw) -> Claim:
    return Claim(project_id=project.id, claim_id=claim_id, title=title, state=state, **kw)


def test_clean_dossier_yields_zero_points(session):
    """Adversarial baseline: a sourced, conflict-free dossier fires NOTHING."""
    project = _project(session)
    session.add(_claim(project, "c-ok", "Hauteur maximale au faîte", "sourced"))
    session.add(Document(project_id=project.id, official_name="RPGA extrait", validation_level="canonical"))
    session.flush()
    view = reports.opposition_view(project)
    assert view["points"] == []
    assert view["doc_basis"]["canonical"] == 1


def test_conflict_and_unsourced_sensitive_claims_become_targeted_points(session):
    project = _project(session)
    session.add(_claim(project, "c-conf", "Indice d'utilisation du sol", "conflict",
                       source_refs=["rdppf", "rpga-art7"]))
    session.add(_claim(project, "c-haut", "Hauteur maximale au faîte", "unknown",
                       next_action="Vérifier l'art. 12 RPGA"))
    # Non-sensitive unknown: must NOT fire (no noise).
    session.add(_claim(project, "c-cad", "Référence cadastrale", "unknown"))
    session.add(Document(project_id=project.id, official_name="Plan situation", validation_level="canonical"))
    session.flush()

    points = reports.opposition_points(project)
    kinds = [p["kind"] for p in points]
    assert kinds.count("conflit_avere") == 1
    assert kinds.count("base_non_sourcee") == 1
    assert "couverture_canonique" not in kinds  # one canonical piece exists

    conflict = next(p for p in points if p["kind"] == "conflit_avere")
    assert conflict["basis"][0]["ref"] == "c-conf"
    assert conflict["basis"][0]["sources"] == ["rdppf", "rpga-art7"]
    unsourced = next(p for p in points if p["kind"] == "base_non_sourcee")
    assert unsourced["basis"][0]["ref"] == "c-haut"
    assert unsourced["action"] == "Vérifier l'art. 12 RPGA"
    # The non-sensitive cadastral unknown produced nothing.
    assert all("c-cad" not in [b.get("ref") for b in p["basis"]] for p in points)


def test_canonical_coverage_and_refused_pieces_fire_dossier_points(session):
    project = _project(session)
    session.add(_claim(project, "c-haut", "Hauteur maximale au faîte", "assumption"))
    session.add(Document(project_id=project.id, official_name="Ancien plan", validation_level="refused"))
    session.flush()

    points = reports.opposition_points(project)
    kinds = {p["kind"] for p in points}
    assert "couverture_canonique" in kinds  # claims exist, zero canonical piece
    assert "piece_refusee" in kinds

    # Revert-and-confirm: validating one canonical piece removes the coverage
    # point (the derivation is live, not declared).
    session.add(Document(project_id=project.id, official_name="RPGA extrait", validation_level="canonical"))
    session.flush()
    session.expire(project)  # drop the cached relationship (a real request re-reads)
    kinds_after = {p["kind"] for p in reports.opposition_points(project)}
    assert "couverture_canonique" not in kinds_after
    assert "piece_refusee" in kinds_after


def test_empty_project_keeps_the_empty_contract(session):
    project = _project(session)
    view = reports.opposition_view(project)
    assert view["data_basis"] == "empty"
    assert view["overall"] is None
    assert view["signals"] == []
    assert view["points"] == []
    assert view["doc_basis"] == {"canonical": 0, "indicative": 0, "refused": 0, "pending": 0}
