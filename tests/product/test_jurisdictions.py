"""W17 — commune → canton resolver + project creation without canton."""
from __future__ import annotations


# --- Pure resolver tests --------------------------------------------------- #


def test_resolver_exact_neuchatel():
    from aedifica import jurisdictions
    r = jurisdictions.resolve("CH", "Neuchâtel")
    assert r["confidence"] == "exact"
    assert r["canton"] == "NE"


def test_resolver_normalises_diacritics_and_case():
    from aedifica import jurisdictions
    for raw in ("Geneve", "GENÈVE", "  genève  ", "GenÈve"):
        r = jurisdictions.resolve("CH", raw)
        assert r["confidence"] == "exact", raw
        assert r["canton"] == "GE", raw


def test_resolver_ambiguous_homonyms():
    """Wald is a real Swiss homonym across cantons — resolver must NOT
    silently pick one."""
    from aedifica import jurisdictions
    r = jurisdictions.resolve("CH", "Wald")
    assert r["confidence"] == "ambiguous"
    codes = {c["canton"] for c in r["candidates"]}
    assert "ZH" in codes and "AR" in codes


def test_resolver_buchs_three_cantons():
    from aedifica import jurisdictions
    r = jurisdictions.resolve("CH", "Buchs")
    assert r["confidence"] == "ambiguous"
    codes = {c["canton"] for c in r["candidates"]}
    assert codes >= {"AG", "SG", "ZH"}


def test_resolver_unknown_commune():
    """Made-up commune name → resolver returns unknown + the full canton
    list so the UI can offer a manual pick."""
    from aedifica import jurisdictions
    r = jurisdictions.resolve("CH", "Glubzy-sur-Mer")
    assert r["confidence"] == "unknown"
    assert r["candidates"] == []
    assert "VD" in r["all_cantons"] and "NE" in r["all_cantons"]
    assert len(r["all_cantons"]) == 26


def test_resolver_empty_input():
    from aedifica import jurisdictions
    r = jurisdictions.resolve("CH", "")
    assert r["confidence"] == "unknown"
    assert r["candidates"] == []


def test_resolver_unsupported_country():
    from aedifica import jurisdictions
    r = jurisdictions.resolve("FR", "Annecy")
    assert r["confidence"] == "unknown"
    assert "not yet supported" in r.get("error", "")


def test_list_swiss_regions_has_26_cantons():
    from aedifica import jurisdictions
    regions = jurisdictions.list_regions("CH")
    codes = {r["canton"] for r in regions}
    assert len(codes) == 26
    assert "NE" in codes and "VD" in codes and "GE" in codes and "ZH" in codes


# --- HTTP endpoint tests -------------------------------------------------- #


def test_jurisdiction_resolve_endpoint_exact(client, owner):
    r = client.get("/api/jurisdictions/resolve?country=CH&commune=Neuch%C3%A2tel").json()
    assert r["confidence"] == "exact"
    assert r["canton"] == "NE"


def test_jurisdiction_resolve_endpoint_ambiguous(client, owner):
    r = client.get("/api/jurisdictions/resolve?commune=Wald").json()
    assert r["confidence"] == "ambiguous"


def test_jurisdiction_regions_endpoint(client, owner):
    r = client.get("/api/jurisdictions/regions?country=CH").json()
    assert r["country"] == "CH"
    assert len(r["regions"]) == 26


# --- POST /api/projects without explicit canton --------------------------- #


def _create(client, h, **overrides):
    body = {"project_id": "W17", "name": "W17 test", "commune": "Neuchâtel"}
    body.update(overrides)
    return client.post("/api/projects", json=body, headers=h)


def test_create_project_resolves_canton_when_omitted(client, owner):
    """The original bug: creating a project in Neuchâtel landed it in VD
    because canton defaulted to VD. The resolver now infers NE."""
    r = _create(client, owner["headers"])
    assert r.status_code == 201, r.text
    summary = r.json()["created"]
    assert summary["jurisdiction"]["canton"] == "NE"
    assert summary["jurisdiction"]["commune"] == "Neuchâtel"


def test_create_project_keeps_explicit_canton(client, owner):
    r = _create(client, owner["headers"], project_id="W17X", commune="Lausanne", canton="VD")
    assert r.status_code == 201
    assert r.json()["created"]["jurisdiction"]["canton"] == "VD"


def test_create_project_ambiguous_commune_rejects(client, owner):
    """Real homonym → backend must NOT silently land in some canton."""
    r = _create(client, owner["headers"], project_id="W17A", commune="Wald")
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "CANTON_REQUIRED"
    assert detail["resolver"]["confidence"] == "ambiguous"


def test_create_project_unknown_commune_rejects(client, owner):
    r = _create(client, owner["headers"], project_id="W17U", commune="Glubzy-sur-Mer")
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert detail["code"] == "CANTON_REQUIRED"
    assert detail["resolver"]["confidence"] == "unknown"


def test_create_project_ambiguous_works_with_explicit_canton(client, owner):
    """The architect picked the canton via the dropdown — backend accepts."""
    r = _create(client, owner["headers"], project_id="W17B", commune="Wald", canton="ZH")
    assert r.status_code == 201
    assert r.json()["created"]["jurisdiction"]["canton"] == "ZH"
