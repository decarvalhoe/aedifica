"""W19-01 NOMOS bundle import adapter tests."""
from __future__ import annotations

import copy
import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import create_app  # noqa: E402
from aedifica.api.config import Settings  # noqa: E402
from aedifica.db import (  # noqa: E402
    Base,
    Claim,
    CommunePack,
    Evidence,
    Org,
    Project,
    Source,
    User,
    make_engine,
    make_session_factory,
)
from aedifica.ingestion import service as ingestion  # noqa: E402
from aedifica.ingestion.nomos_bundle import NomosBundleError, import_nomos_bundle  # noqa: E402


@pytest.fixture()
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as s:
        yield s


def _project(session) -> Project:
    org = Org(name="Atelier NOMOS")
    session.add(org)
    session.flush()
    session.add(User(org_id=org.id, email="owner@test.ch", name="Owner", role="owner"))
    project = Project(org_id=org.id, project_id="P-NOMOS", name="Rue Centrale", commune="Lausanne", canton="VD")
    session.add(project)
    session.flush()
    return project


def _bundle(text: str = "Zone centre: indice d'utilisation du sol 0.7.", include_trace: bool = True) -> dict:
    trace_manifest = {"bundle_sha256": "b" * 64, "feed_sha256": "c" * 64} if include_trace else None
    return {
        "schema_version": "ckm-bundle-v1",
        "bundle_id": "nomos-built-environment-stub",
        "version": "2026.06-stub",
        "feeds": [
            {
                "feed_id": "vd-lausanne-rpga",
                "version": "vd-lausanne-rpga-2026-06",
                "jurisdiction": {"commune": "Lausanne", "canton": "VD"},
                "source_authority": "Commune de Lausanne",
                "valid_as_of": "2026-06-01",
                "review_due": "2026-12-01",
                "trace_manifest": trace_manifest,
                "rag_metadata": {"node-zone-centre": {"chunk_id": "chunk-1"}},
                "nodes": [
                    {
                        "node_id": "node-zone-centre",
                        "text": text,
                        "source_path": "reglements/lausanne-rpga.pdf",
                        "source_hash": "a" * 64,
                        "span": {"start": 120, "end": 176},
                        "parent_chain": ["rpga", "art-7"],
                        "facets": {
                            "nature": "regulatory",
                            "scope_level": "local",
                            "trust_tier": "certified",
                            "provenance": "official",
                            "confidentiality": "public",
                        },
                        "claim": {
                            "claim_id": "lausanne-zone-centre",
                            "title": "Zone centre IUS",
                            "zone": "Zone centre",
                            "value": {"ius": 0.7},
                        },
                    }
                ],
            }
        ],
    }


def test_nomos_bundle_import_maps_feed_to_pack_claim_source_and_evidence(session):
    project = _project(session)

    result = import_nomos_bundle(session, project, _bundle(), nomos_enabled=True, activate=True)
    session.commit()

    assert result["packs"] == 1
    assert result["sources"] == 1
    assert result["evidence"] == 1
    assert result["claims"] == 1
    assert result["activated"] == ["vd-lausanne-rpga-2026-06"]

    support = ingestion.support_state(session, "Lausanne", "VD")
    assert support["usable"] is True
    assert support["version"] == "vd-lausanne-rpga-2026-06"

    pack = session.query(CommunePack).one()
    assert pack.data["zones"] == {"Zone centre": {"ius": 0.7}}
    assert pack.data["nomos"]["bundle_id"] == "nomos-built-environment-stub"
    assert pack.data["nomos"]["trace_manifest"]["feed_sha256"] == "c" * 64

    source = session.query(Source).one()
    assert source.source_id == "nomos:vd-lausanne-rpga:aaaaaaaaaaaa"
    assert source.sha256 == "a" * 64
    assert source.trust_tier == "certified"
    assert source.provenance == "official"
    assert source.facets["scope_level"] == "local"

    evidence = session.query(Evidence).one()
    assert evidence.evidence_id == "nomos:vd-lausanne-rpga:node-zone-centre"
    assert evidence.file_ref == "reglements/lausanne-rpga.pdf"
    assert evidence.source_id == source.source_id

    claim = session.query(Claim).one()
    assert claim.state == "sourced"
    assert claim.value == {"ius": 0.7}
    assert claim.source_refs == [
        {
            "source_id": source.source_id,
            "node_id": "node-zone-centre",
            "source_hash": "a" * 64,
            "source_path": "reglements/lausanne-rpga.pdf",
            # Legacy {start, end} spans are normalized to the emitted contract form.
            "span": {"start_line": 120, "end_line": 176},
            "parent_chain": ["rpga", "art-7"],
        }
    ]


def test_nomos_bundle_import_is_flag_gated(session):
    project = _project(session)

    with pytest.raises(NomosBundleError, match="disabled"):
        import_nomos_bundle(session, project, _bundle(), nomos_enabled=False, activate=True)

    assert session.query(CommunePack).count() == 0
    assert session.query(Source).count() == 0
    assert session.query(Evidence).count() == 0
    assert session.query(Claim).count() == 0


def test_nomos_bundle_import_refuses_unusable_text_or_missing_trace_and_rolls_back(session):
    project = _project(session)
    bundle = _bundle()
    bundle["feeds"].append(copy.deepcopy(_bundle(text="   ")["feeds"][0]))
    bundle["feeds"][1]["version"] = "vd-lausanne-rpga-2026-07"

    with pytest.raises(NomosBundleError, match="text"):
        import_nomos_bundle(session, project, bundle, nomos_enabled=True, activate=True)

    assert session.query(CommunePack).count() == 0
    assert session.query(Source).count() == 0
    assert session.query(Evidence).count() == 0
    assert session.query(Claim).count() == 0

    with pytest.raises(NomosBundleError, match="trace"):
        import_nomos_bundle(session, project, _bundle(include_trace=False), nomos_enabled=True)

    assert session.query(CommunePack).count() == 0
    assert session.query(Source).count() == 0
    assert session.query(Evidence).count() == 0
    assert session.query(Claim).count() == 0


def test_nomos_bundle_feed_version_is_immutable(session):
    project = _project(session)
    import_nomos_bundle(session, project, _bundle(), nomos_enabled=True)
    session.commit()

    with pytest.raises(NomosBundleError, match="immutable"):
        import_nomos_bundle(session, project, _bundle(), nomos_enabled=True)

    assert session.query(CommunePack).count() == 1
    assert session.query(CommunePack).one().data["zones"] == {"Zone centre": {"ius": 0.7}}


def test_nomos_bundle_duplicate_feed_version_in_bundle_is_refused(session):
    project = _project(session)
    bundle = _bundle()
    duplicate = copy.deepcopy(bundle["feeds"][0])
    duplicate["feed_id"] = "vd-lausanne-rpga-copy"
    bundle["feeds"].append(duplicate)

    with pytest.raises(NomosBundleError, match="immutable"):
        import_nomos_bundle(session, project, bundle, nomos_enabled=True)

    assert session.query(CommunePack).count() == 0
    assert session.query(Source).count() == 0
    assert session.query(Evidence).count() == 0
    assert session.query(Claim).count() == 0


def test_nomos_bundle_schema_version_gate_rejects_absent_and_unknown(session):
    """W20-1 adversarial: the importer refuses any contract it does not speak."""
    project = _project(session)

    absent = _bundle()
    del absent["schema_version"]
    with pytest.raises(NomosBundleError, match="schema_version") as excinfo:
        import_nomos_bundle(session, project, absent, nomos_enabled=True)
    assert excinfo.value.code == "NOMOS_BUNDLE_SCHEMA_UNSUPPORTED"

    unknown = _bundle()
    unknown["schema_version"] = "ckm-bundle-v999"
    with pytest.raises(NomosBundleError, match="ckm-bundle-v999") as excinfo:
        import_nomos_bundle(session, project, unknown, nomos_enabled=True)
    assert excinfo.value.code == "NOMOS_BUNDLE_SCHEMA_UNSUPPORTED"

    assert session.query(CommunePack).count() == 0
    assert session.query(Claim).count() == 0


def test_nomos_bundle_accepts_emitted_start_line_span_form(session):
    """The real emitter ships {start_line, end_line}; both forms normalize identically."""
    project = _project(session)
    bundle = _bundle()
    bundle["feeds"][0]["nodes"][0]["span"] = {"start_line": 3, "end_line": 9}

    import_nomos_bundle(session, project, bundle, nomos_enabled=True)
    session.commit()

    claim = session.query(Claim).one()
    assert claim.source_refs[0]["span"] == {"start_line": 3, "end_line": 9}


def test_nomos_bundle_span_missing_bounds_is_refused(session):
    project = _project(session)
    bundle = _bundle()
    bundle["feeds"][0]["nodes"][0]["span"] = {"locator": "p.4"}

    with pytest.raises(NomosBundleError, match="start/end"):
        import_nomos_bundle(session, project, bundle, nomos_enabled=True)
    assert session.query(CommunePack).count() == 0


def test_nomos_bundle_derives_feed_version_when_absent(session):
    """The real emitter has no feeds[].version: derive bundle_id@generated_at."""
    project = _project(session)
    bundle = _bundle()
    bundle["generated_at"] = "2026-06-11T00:00:00Z"
    del bundle["feeds"][0]["version"]

    result = import_nomos_bundle(session, project, bundle, nomos_enabled=True)
    session.commit()

    derived = "nomos-built-environment-stub@2026-06-11T00:00:00Z"
    # Longer than CommunePack.version's 40 chars -> deterministic hash tail.
    assert len(result["versions"][0]) <= 40
    assert result["versions"][0].startswith(derived[:31])

    # Determinism doubles as immutability: re-importing the same emission is refused.
    again = _bundle()
    again["generated_at"] = "2026-06-11T00:00:00Z"
    del again["feeds"][0]["version"]
    with pytest.raises(NomosBundleError, match="immutable"):
        import_nomos_bundle(session, project, again, nomos_enabled=True)


def test_nomos_bundle_defaults_jurisdiction_from_project(session):
    """The emitter carries no jurisdiction; the project-scoped endpoint supplies it."""
    project = _project(session)  # commune=Lausanne, canton=VD
    bundle = _bundle()
    del bundle["feeds"][0]["jurisdiction"]

    import_nomos_bundle(session, project, bundle, nomos_enabled=True)
    session.commit()

    pack = session.query(CommunePack).one()
    assert pack.commune == "Lausanne"
    assert pack.canton == "VD"


def test_nomos_bundle_joins_bundle_level_rag_metadata_list(session):
    """The emitted rag_metadata is a bundle-level list; it must join, not vanish."""
    project = _project(session)
    bundle = _bundle()
    del bundle["feeds"][0]["rag_metadata"]
    bundle["rag_metadata"] = [
        {"node_id": "node-zone-centre", "chunk_id": "chunk:node-zone-centre", "source_path": "reglements/lausanne-rpga.pdf"}
    ]

    import_nomos_bundle(session, project, bundle, nomos_enabled=True)
    session.commit()

    pack = session.query(CommunePack).one()
    stored = pack.data["nomos"]["rag_metadata"]
    assert stored["node-zone-centre"]["chunk_id"] == "chunk:node-zone-centre"


def test_nomos_bundle_orphan_rag_metadata_is_refused(session):
    project = _project(session)
    bundle = _bundle()
    bundle["rag_metadata"] = [{"node_id": "GHOST-NODE", "chunk_id": "chunk:ghost"}]

    with pytest.raises(NomosBundleError, match="GHOST-NODE"):
        import_nomos_bundle(session, project, bundle, nomos_enabled=True)
    assert session.query(CommunePack).count() == 0


def _bootstrap_project(client: TestClient) -> dict:
    owner = client.post("/api/orgs", json={"org_name": "Atelier Test", "user_email": "owner@test.ch"})
    assert owner.status_code == 201
    headers = {"Authorization": f"Bearer {owner.json()['token']}"}
    project = client.post(
        "/api/projects",
        json={"project_id": "P-NOMOS", "name": "Rue Centrale", "commune": "Lausanne", "canton": "VD"},
        headers=headers,
    )
    assert project.status_code == 201
    return headers


def test_api_nomos_import_endpoint_is_flag_gated(engine):
    app = create_app(engine=engine, settings=Settings(nomos_enabled=False))
    client = TestClient(app)
    headers = _bootstrap_project(client)

    response = client.post(
        "/api/projects/P-NOMOS/nomos/import",
        json={"bundle": _bundle(), "activate": True},
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NOMOS_DISABLED"
    with make_session_factory(engine)() as session:
        assert session.query(CommunePack).count() == 0
        assert session.query(Source).count() == 0
        assert session.query(Evidence).count() == 0
        assert session.query(Claim).count() == 0
