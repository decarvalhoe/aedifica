"""W11.C: the /api/atelier/alerts endpoint surfaces guidance derived from the
multi-project task pool (Gantt + collisions) so the Dashboard can show
actionable items without the architect having to read the Gantt."""
from __future__ import annotations
from datetime import date, timedelta


def _project(client, h, pid="A1"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": "Lausanne"}, headers=h)
    return pid


def test_alerts_empty_when_no_projects(client, owner):
    h = owner["headers"]
    r = client.get("/api/atelier/alerts", headers=h).json()
    assert r["alerts"] == []


def test_overdue_task_surfaces_a_bad_alert(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    yest = (date.today() - timedelta(days=2)).isoformat()
    client.post(f"/api/projects/{pid}/tasks",
                json={"title": "Rendu permis", "priority": "p0", "due_date": yest, "estimate_hours": 8},
                headers=h)
    al = client.get("/api/atelier/alerts", headers=h).json()["alerts"]
    overdue = [a for a in al if a["kind"] == "overdue"]
    assert overdue and overdue[0]["severity"] == "bad"
    assert overdue[0]["project_id"] == pid


def test_p0_within_7_days_surfaces_a_warn_alert(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "A2")
    soon = (date.today() + timedelta(days=3)).isoformat()
    client.post(f"/api/projects/{pid}/tasks",
                json={"title": "P0 imminent", "priority": "p0", "due_date": soon, "estimate_hours": 4},
                headers=h)
    al = client.get("/api/atelier/alerts", headers=h).json()["alerts"]
    near = [a for a in al if a["kind"] == "p0_soon"]
    assert near and near[0]["severity"] == "warn"


def test_overloaded_week_surfaces_an_alert(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "A3")
    # 80 h in one ISO week → above the 40 h/week default capacity
    soon = (date.today() + timedelta(days=4)).isoformat()
    for i in range(3):
        client.post(f"/api/projects/{pid}/tasks",
                    json={"title": f"big {i}", "priority": "p1",
                          "due_date": soon, "estimate_hours": 30}, headers=h)
    al = client.get("/api/atelier/alerts", headers=h).json()["alerts"]
    over = [a for a in al if a["kind"] == "overloaded_week"]
    assert over and over[0]["severity"] == "warn"


def test_quick_wins_open_count_surfaces_info_alert(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "A4")
    for i in range(3):
        client.post(f"/api/projects/{pid}/tasks",
                    json={"title": f"qw {i}", "priority": "p2", "is_quick_win": True,
                          "estimate_hours": 2}, headers=h)
    al = client.get("/api/atelier/alerts", headers=h).json()["alerts"]
    qw = [a for a in al if a["kind"] == "quick_wins_available"]
    assert qw and qw[0]["severity"] == "info"
