"""W9 operating layer: intervenants registry, document 3-level validation, access grants."""
from __future__ import annotations

from aedifica.db import make_session_factory, models as m


def _project(client, h, pid="P1"):
    client.post("/api/projects", json={"project_id": pid, "name": "Test", "commune": "Lausanne"}, headers=h)
    return pid


def test_intervenants_registry_crud(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    empty = client.get(f"/api/projects/{pid}/intervenants", headers=h).json()
    assert empty["groups"] == [] and empty["people"] == []
    # group (a discipline) + a sourced, responsible person inside it
    g = client.post(f"/api/projects/{pid}/intervenant-groups",
                    json={"name": "Ingénieurs", "kind": "discipline"}, headers=h).json()["group"]
    p = client.post(f"/api/projects/{pid}/intervenants",
                    json={"name": "A. Civil", "role": "ingénieur civil", "email": "a@civ.ch",
                          "is_responsible": True, "group_id": g["id"]}, headers=h).json()["intervenant"]
    assert p["group_id"] == g["id"] and p["is_responsible"]
    listing = client.get(f"/api/projects/{pid}/intervenants", headers=h).json()
    assert len(listing["groups"]) == 1 and len(listing["people"]) == 1
    # patch keeps untouched fields
    p2 = client.patch(f"/api/projects/{pid}/intervenants/{p['id']}", json={"phone": "+41 21 000"}, headers=h).json()["intervenant"]
    assert p2["phone"] == "+41 21 000" and p2["role"] == "ingénieur civil"
    # deleting a group un-groups its members (the person survives)
    client.delete(f"/api/projects/{pid}/intervenant-groups/{g['id']}", headers=h)
    after = client.get(f"/api/projects/{pid}/intervenants", headers=h).json()
    assert after["groups"] == [] and len(after["people"]) == 1 and after["people"][0]["group_id"] is None
    client.delete(f"/api/projects/{pid}/intervenants/{p['id']}", headers=h)
    assert client.get(f"/api/projects/{pid}/intervenants", headers=h).json()["people"] == []


def test_document_three_level_validation(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    d = client.post(f"/api/projects/{pid}/documents",
                    json={"official_name": "Permis 2019", "version_label": "v1", "source": "manual"}, headers=h).json()["document"]
    assert d["validation_level"] == "pending" and d["latest"] == "v1"
    # the lead architect validates the document as canonical
    d2 = client.post(f"/api/projects/{pid}/documents/{d['id']}/validate", json={"level": "canonical"}, headers=h).json()["document"]
    assert d2["validation_level"] == "canonical" and d2["validated_by"]
    # an unknown level is rejected
    assert client.post(f"/api/projects/{pid}/documents/{d['id']}/validate", json={"level": "bogus"}, headers=h).status_code == 400
    # confidential flag (LPD)
    d3 = client.patch(f"/api/projects/{pid}/documents/{d['id']}", json={"confidential": True}, headers=h).json()["document"]
    assert d3["confidential"] is True
    s = client.get(f"/api/projects/{pid}/documents", headers=h).json()["summary"]
    assert s["total"] == 1 and s["by_level"]["canonical"] == 1 and s["pending"] == 0


def test_access_grant_group_then_revoke(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    g = client.post(f"/api/projects/{pid}/intervenant-groups", json={"name": "Maître d'ouvrage"}, headers=h).json()["group"]
    d = client.post(f"/api/projects/{pid}/documents", json={"official_name": "Plan situation"}, headers=h).json()["document"]
    granted = client.post(f"/api/projects/{pid}/documents/{d['id']}/grants",
                          json={"group_id": g["id"], "level": "read"}, headers=h).json()["document"]
    assert len(granted["grants"]) == 1 and granted["grants"][0]["group_id"] == g["id"]
    gid = granted["grants"][0]["id"]
    revoked = client.delete(f"/api/projects/{pid}/documents/{d['id']}/grants/{gid}", headers=h).json()["document"]
    assert revoked["grants"] == []


def test_write_requires_capability(client, engine):
    """A viewer can read the registry but cannot create intervenants/documents."""
    with make_session_factory(engine)() as s:
        org = m.Org(name="V Org")
        s.add(org)
        s.flush()
        s.add(m.User(org_id=org.id, email="v@v.ch", name="V", role="viewer", api_token="VTOK"))
        s.add(m.Project(org_id=org.id, project_id="VP", name="VP", commune="Lausanne"))
        s.commit()
    h = {"Authorization": "Bearer VTOK"}
    assert client.get("/api/projects/VP/intervenants", headers=h).status_code == 200
    r = client.post("/api/projects/VP/intervenant-groups", json={"name": "X"}, headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "FORBIDDEN"


def test_brs_register_sourced_attributed_versioned(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    e1 = client.post(f"/api/projects/{pid}/brs",
                     json={"content": "Ajouter un garage", "channel": "phone", "emitter_label": "M. Client"}, headers=h).json()["entry"]
    assert e1["channel"] == "phone" and e1["emitter"] == "M. Client" and e1["status"] == "active"
    # a later entry supersedes the first (requirements evolve)
    client.post(f"/api/projects/{pid}/brs",
                json={"content": "Finalement un carport", "channel": "email", "supersedes_id": e1["id"]}, headers=h)
    lst = client.get(f"/api/projects/{pid}/brs", headers=h).json()
    assert lst["summary"]["total"] == 2 and lst["summary"]["by_channel"]["phone"] == 1
    assert next(x for x in lst["entries"] if x["id"] == e1["id"])["status"] == "superseded"
    # invalid channel rejected
    assert client.post(f"/api/projects/{pid}/brs", json={"content": "x", "channel": "telepathy"}, headers=h).status_code == 400
    # lock a baseline
    locked = client.patch(f"/api/projects/{pid}/brs/{e1['id']}", json={"status": "locked"}, headers=h).json()["entry"]
    assert locked["status"] == "locked"


def test_checklist_seed_retroactive_and_parametric(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    # onboard the project at phase 33 → earlier-phase steps are flagged retroactive
    seeded = client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "33"}, headers=h).json()
    assert seeded["seeded"] > 0
    cl = client.get(f"/api/projects/{pid}/checklist", headers=h).json()
    assert cl["summary"]["seeded"] and cl["summary"]["retroactive"] > 0
    p11 = next(i for i in cl["items"] if i["phase_code"] == "11")
    p41 = next(i for i in cl["items"] if i["phase_code"] == "41")
    assert p11["is_retroactive"] and not p41["is_retroactive"]
    # re-seed is rejected
    assert client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h).status_code == 409
    # a step is parametric: todo -> done; bad status rejected
    assert client.patch(f"/api/projects/{pid}/checklist/{p11['id']}", json={"status": "done"}, headers=h).json()["item"]["status"] == "done"
    assert client.patch(f"/api/projects/{pid}/checklist/{p41['id']}", json={"status": "bogus"}, headers=h).status_code == 400


def test_to_validate_queue(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    client.post(f"/api/projects/{pid}/documents", json={"official_name": "A valider"}, headers=h)  # pending
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h)
    tv = client.get(f"/api/projects/{pid}/to-validate", headers=h).json()
    assert tv["counts"]["documents"] == 1 and tv["counts"]["checklist_todo"] > 0
