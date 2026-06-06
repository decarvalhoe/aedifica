"""W14.A — honest UX surfaces: ingestion job state, intervenants directory,
foresight thresholds exposed even when no proposal fires.

Doctrine: when a feature can't actually do something (ingestion has no
worker), the UI must reflect that truthfully; when an empty-state could
hide a known threshold (Foresight needs 5 comparables), expose it.
"""
from __future__ import annotations


def _project(client, h, pid="UX1", commune="Lutry"):
    body = {"project_id": pid, "name": pid, "commune": commune, "canton": "VD"}
    client.post("/api/projects", json=body, headers=h)
    return pid


# --- ingestion honest panel ----------------------------------------------


def test_unsupported_commune_lists_required_inputs(client, owner):
    h = owner["headers"]
    r = client.get("/api/communes/Lutry/VD/support", headers=h).json()
    sup = r["support"]
    assert sup["state"] == "unsupported"
    assert sup["usable"] is False
    assert sup["job"] is None
    assert len(sup["required_inputs"]) >= 3
    assert any("PGA" in s or "PACom" in s for s in sup["required_inputs"])


def test_request_ingestion_creates_job_with_age(client, owner):
    h = owner["headers"]
    # Request ingestion for an unsupported commune.
    body = {"commune": "Lutry", "canton": "VD"}
    r = client.post("/api/communes", json=body, headers=h)
    assert r.status_code == 201
    # Now the support endpoint surfaces a job with status='requested'
    sup = client.get("/api/communes/Lutry/VD/support", headers=h).json()["support"]
    assert sup["state"] == "seed"  # honest: not yet usable
    assert sup["usable"] is False
    assert sup["job"] is not None
    assert sup["job"]["status"] == "requested"
    assert "requested_at" in sup["job"]
    assert sup["job"]["age_days"] is not None  # int, can be 0
    # Required inputs still surfaced (the operator hasn't captured them yet).
    assert sup["required_inputs"]


# --- intervenants directory ----------------------------------------------


def test_directory_empty_when_no_intervenants(client, owner):
    r = client.get("/api/orgs/intervenants-directory", headers=owner["headers"]).json()
    assert r["contacts"] == []
    assert r["total"] == 0


def test_directory_aggregates_across_projects_and_dedups(client, owner):
    h = owner["headers"]
    _project(client, h, pid="A1")
    _project(client, h, pid="B1")
    # Same person on both projects
    client.post("/api/projects/A1/intervenants",
                json={"name": "Pierre Martin", "role": "architecte",
                      "email": "pierre@martin.ch", "organization": "Atelier M"},
                headers=h)
    client.post("/api/projects/B1/intervenants",
                json={"name": "Pierre Martin", "role": "architecte",
                      "email": "pierre@martin.ch", "organization": "Atelier M"},
                headers=h)
    # Different person on B1
    client.post("/api/projects/B1/intervenants",
                json={"name": "Jeanne Dupont", "role": "ingénieure civile",
                      "email": "jd@civil.ch", "organization": "BG"},
                headers=h)
    r = client.get("/api/orgs/intervenants-directory", headers=h).json()
    assert r["total"] == 2  # de-duped Pierre, plus Jeanne
    pierre = next(c for c in r["contacts"] if c["name"] == "Pierre Martin")
    assert len(pierre["seen_in_projects"]) == 2
    pids = {p["project_id"] for p in pierre["seen_in_projects"]}
    assert pids == {"A1", "B1"}


def test_directory_excludes_current_project(client, owner):
    h = owner["headers"]
    _project(client, h, pid="A1")
    _project(client, h, pid="B1")
    client.post("/api/projects/A1/intervenants",
                json={"name": "Pierre", "role": "arch", "email": "p@m.ch"}, headers=h)
    client.post("/api/projects/B1/intervenants",
                json={"name": "Jeanne", "role": "ing", "email": "j@m.ch"}, headers=h)
    # From A1, the directory should show ONLY Jeanne (Pierre already there).
    r = client.get("/api/orgs/intervenants-directory?project_id=A1", headers=h).json()
    names = [c["name"] for c in r["contacts"]]
    assert "Jeanne" in names
    assert "Pierre" not in names


# --- foresight thresholds ------------------------------------------------


def test_foresight_thresholds_surfaced_even_when_empty(client, owner):
    h = owner["headers"]; pid = _project(client, h, pid="FS-T1")
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    thr = r["thresholds"]
    assert "duration_adjust" in thr
    assert thr["duration_adjust"]["need_per_phase"] == 5
    assert "samples_by_phase" in thr["duration_adjust"]
    assert thr["cost_factor"]["need"] == 3
    assert "explanation" in thr["duration_adjust"]
    # Risk explanation present even though risks have no count threshold.
    assert "explanation" in thr["risk_alert"]


def test_foresight_thresholds_track_progress(client, owner):
    h = owner["headers"]; pid = _project(client, h, pid="FS-T2")
    # Add 3 done tasks in phase 32 to start populating.
    for i in range(3):
        t = client.post(f"/api/projects/{pid}/tasks",
                        json={"title": f"H{i}", "estimate_hours": 10, "phase_code": "32"},
                        headers=h).json()["task"]
        client.patch(f"/api/projects/{pid}/tasks/{t['id']}",
                     json={"status": "done", "actual_hours": 15}, headers=h)
    r = client.get(f"/api/projects/{pid}/foresight?refresh=true", headers=h).json()
    p32 = r["thresholds"]["duration_adjust"]["samples_by_phase"].get("32")
    assert p32["have"] == 3
    assert p32["need"] == 5
    assert p32["ready"] is False
