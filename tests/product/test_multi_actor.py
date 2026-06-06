"""W10 multi-actor: per-actor SIA checklist, coordination, scoped external access.

Grounded in `docs/strategy/session-2026-06-05-etienne-DEEP.md` §5: each step has a
responsible actor (mo/architecte/mandataire/entreprise) ; the architect sees the four
panes of Coordination (who-owes-what, blockers, documents, validation queue) ; an
intervenant invited as an external user redeems a token to log in and sees only their
slice (their devoirs, their documents) with a 1-click done.
"""
from __future__ import annotations


def _project(client, h, pid="W10A"):
    client.post("/api/projects", json={"project_id": pid, "name": "T", "commune": "Lausanne"}, headers=h)
    return pid


def _seed(client, h, pid, entry="11"):
    return client.post(f"/api/projects/{pid}/checklist/seed",
                       json={"entry_phase": entry}, headers=h).json()


# ---- Exhaustive per-actor checklist (the SIA Vaud sheet, verbatim) -------- #

def test_seeded_checklist_is_exhaustive_and_tagged_per_actor(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    seeded = _seed(client, h, pid)
    # The deep template covers all phases through 61, ≥ 40 items, > 8 phases.
    assert seeded["seeded"] >= 40
    phases = sorted({c["phase_code"] for c in seeded["items"]})
    # All official SIA sub-phases represented (per the SIA Vaud sheet).
    for code in ("11", "21", "22", "31", "32", "33", "41", "51", "52", "53", "61"):
        assert code in phases
    # Every step carries its responsible actor (no silent fallback to "architecte" for all).
    actors = {c["actor"] for c in seeded["items"]}
    assert actors == {"mo", "architecte", "mandataire", "entreprise"}
    # Specific devoirs we should find (proof the template is not just a generic list).
    titles = {(c["phase_code"], c["actor"], c["title"]) for c in seeded["items"]}
    assert any("besoins" in t.lower() or "rêves" in t.lower() or "budget" in t.lower()
               for (p, a, t) in titles if p == "11" and a == "mo")  # client devoirs phase 11
    assert any("contrat sia" in t.lower() for (p, a, t) in titles if a == "mo")
    assert any("plans d'exécution" in t.lower() for (p, a, t) in titles if p == "51")


def test_list_checklist_summarises_by_actor_and_external_todo(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    _seed(client, h, pid)
    lst = client.get(f"/api/projects/{pid}/checklist", headers=h).json()
    # by_actor returns a slot per category with done/todo counts.
    by_actor = lst["summary"]["by_actor"]
    assert set(by_actor.keys()) >= {"mo", "architecte", "mandataire", "entreprise"}
    assert by_actor["mo"]["total"] >= 2 and by_actor["mo"]["todo"] >= 2  # MO has devoirs
    assert lst["summary"]["external_todo"] >= by_actor["mo"]["todo"]
    # actor labels are surfaced for the UI.
    assert lst["actors"]["mo"].startswith("Maître")
    # Items declare is_external on non-architect rows.
    ext = [c for c in lst["items"] if c["actor"] != "architecte"]
    assert ext and all(c["is_external"] for c in ext)


def test_external_blockers_surface_in_to_validate(client, owner):
    """External-actor steps overdue (retroactive or in a reached phase) are blockers."""
    h = owner["headers"]
    pid = _project(client, h, "W10B")
    # entry phase = 31 → phases 11 and 21 are retroactive (back-fill).
    _seed(client, h, pid, entry="31")
    tv = client.get(f"/api/projects/{pid}/to-validate", headers=h).json()
    # MO devoirs in phase 11 (retroactive) are external blockers.
    assert tv["counts"]["external_blockers"] >= 1
    assert any(b["actor"] == "mo" for b in tv["external_blockers"])


# ---- Coordination — single point of truth -------------------------------- #

def test_coordination_returns_four_panes(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "W10C")
    _seed(client, h, pid)
    # Drop a pending document so the validation queue is non-empty.
    client.post(f"/api/projects/{pid}/documents",
                json={"official_name": "Permis CAMAC 2026-42", "category": "permit"}, headers=h)
    coord = client.get(f"/api/projects/{pid}/coordination", headers=h).json()
    assert coord["project"]["project_id"] == pid
    # (1) who-owes-what is bucketed per actor and lists their todo steps.
    assert set(coord["who_owes_what"].keys()) >= {"mo", "architecte", "mandataire", "entreprise"}
    assert coord["who_owes_what"]["mo"], "MO should have devoirs to fulfil at the start"
    # (2) blockers split internal vs external.
    assert "external" in coord["blockers"] and "atelier" in coord["blockers"]
    # (3) documents — pending one bubbles to the top.
    assert coord["documents"]["items"][0]["validation_level"] == "pending"
    # (4) architect validation queue.
    assert coord["to_validate"]["documents"][0]["official_name"] == "Permis CAMAC 2026-42"


# ---- Multi-actor access: invite + accept + scoped /me ------------------- #

def test_invite_intervenant_creates_external_user_with_token(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "W10D")
    iv = client.post(f"/api/projects/{pid}/intervenants",
                     json={"name": "Mme Cliente", "role": "maître de l'ouvrage"},
                     headers=h).json()["intervenant"]
    inv = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                      json={"email": "cliente@example.org"}, headers=h).json()
    assert inv["invite_token"] and inv["user"]["role"] == "external"
    assert inv["user"]["linked_intervenant_id"] == iv["id"]
    # Duplicate email for same org rejected.
    bad = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                      json={"email": "cliente@example.org"}, headers=h)
    assert bad.status_code == 409


def test_accept_invite_then_scoped_views(client, owner):
    """The full external user flow: architect invites, intervenant accepts, sees own slice."""
    h = owner["headers"]
    pid = _project(client, h, "W10E")
    _seed(client, h, pid)
    # MO intervenant invited
    iv = client.post(f"/api/projects/{pid}/intervenants",
                     json={"name": "M. Owner", "role": "maître de l'ouvrage"},
                     headers=h).json()["intervenant"]
    inv = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                      json={"email": "owner@example.org"}, headers=h).json()
    # Intervenant accepts (sets password)
    r = client.post("/api/auth/accept-invite",
                    json={"token": inv["invite_token"], "password": "s3cret!", "name": "M. Owner"}).json()
    assert r["role"] == "external" and r["linked_intervenant"]["id"] == iv["id"]
    # Can no longer redeem twice (token cleared)
    again = client.post("/api/auth/accept-invite",
                        json={"token": inv["invite_token"], "password": "x"})
    assert again.status_code == 404
    # And can also log in with email+password
    login = client.post("/api/auth/login",
                        json={"email": "owner@example.org", "password": "s3cret!"}).json()
    assert login["role"] == "external" and login["linked_intervenant_id"] == iv["id"]
    ext_h = {"Authorization": f"Bearer {login['token']}"}
    # /external/me returns the scoped context.
    me = client.get("/api/external/me", headers=ext_h).json()
    assert me["intervenant"]["actor_category"] == "mo"
    assert me["project"]["project_id"] == pid
    # /external/me/checklist returns ONLY MO devoirs (no architect/mandataire/entreprise steps).
    mine = client.get("/api/external/me/checklist", headers=ext_h).json()
    assert mine["summary"]["actor_category"] == "mo"
    assert mine["summary"]["total"] >= 2
    # Client vocabulary: phase 11 label is the "On définit ensemble..." copy, not the
    # technical "Définition des objectifs".
    p11 = next(r for r in mine["items"] if r["phase_code"] == "11")
    assert "définit" in p11["phase_label"].lower() and "objectifs" not in p11["phase_label"].lower()
    # One-click done: external can tick one of their own steps to done.
    item_id = mine["items"][0]["id"]
    tick = client.patch(f"/api/external/me/checklist/{item_id}",
                        json={"status": "done"}, headers=ext_h).json()
    assert tick["item"]["status"] == "done"
    # And cannot touch a step that's not theirs (an architecte step).
    full = client.get(f"/api/projects/{pid}/checklist", headers=owner["headers"]).json()
    archi_id = next(c["id"] for c in full["items"] if c["actor"] == "architecte")
    forbidden = client.patch(f"/api/external/me/checklist/{archi_id}",
                             json={"status": "done"}, headers=ext_h)
    assert forbidden.status_code == 404


def test_external_documents_scope_via_access_grants(client, owner):
    """An external sees only the docs an AccessGrant gives them (group OR person)."""
    h = owner["headers"]
    pid = _project(client, h, "W10F")
    grp = client.post(f"/api/projects/{pid}/intervenant-groups",
                      json={"name": "Ingénieurs", "kind": "discipline"}, headers=h).json()["group"]
    iv = client.post(f"/api/projects/{pid}/intervenants",
                     json={"name": "Civil Eng.", "role": "ingénieur civil", "group_id": grp["id"]},
                     headers=h).json()["intervenant"]
    inv = client.post(f"/api/projects/{pid}/intervenants/{iv['id']}/invite",
                      json={"email": "civ@eng.ch"}, headers=h).json()
    client.post("/api/auth/accept-invite",
                json={"token": inv["invite_token"], "password": "pw1!", "name": "Civ"})
    login = client.post("/api/auth/login", json={"email": "civ@eng.ch", "password": "pw1!"}).json()
    ext_h = {"Authorization": f"Bearer {login['token']}"}
    # Two docs, one granted to the group, one private.
    d_public = client.post(f"/api/projects/{pid}/documents",
                           json={"official_name": "Plan civil v1", "category": "plan"}, headers=h).json()["document"]
    d_private = client.post(f"/api/projects/{pid}/documents",
                            json={"official_name": "PV interne", "category": "minutes"}, headers=h).json()["document"]
    g = client.post(f"/api/projects/{pid}/documents/{d_public['id']}/grants",
                    json={"group_id": grp["id"], "level": "read"}, headers=h)
    assert g.status_code == 201, g.text
    # External sees the granted one only.
    seen = client.get("/api/external/me/documents", headers=ext_h).json()
    titles = {d["official_name"] for d in seen["documents"]}
    assert "Plan civil v1" in titles and "PV interne" not in titles
    assert seen["count"] == 1
