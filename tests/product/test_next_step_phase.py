"""W11.A: the /next-step endpoint must track the project's actual SIA phase.
Before the fix, a fresh project (phase_code = "0") would return the full permit
gabarit as 4 phase-33 steps, regardless of where the project actually was."""
from __future__ import annotations


def _project(client, h, pid="W11A", commune="Lausanne"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": commune}, headers=h)
    return pid


def test_unset_project_only_surfaces_phase_11_next_steps(client, owner):
    h = owner["headers"]
    pid = _project(client, h)
    # Seed the checklist so the next-step source has real items to surface
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h)
    ns = client.get(f"/api/projects/{pid}/next-step", headers=h).json()
    # Window is just phase 11 for an unset project
    assert ns["window"] == ["11"]
    # No phase-33 permit blocker leaks into 'steps' on a project that hasn't
    # even started its definition-of-objectives phase
    assert all(s["phase"] in ("11",) for s in ns["steps"])
    # The phase-33 permit items are still available, but in 'upcoming' — not
    # passed off as "what to do now"
    assert any(s.get("phase") == "33" for s in ns["upcoming"])


def test_window_follows_phase_patch(client, owner):
    h = owner["headers"]
    pid = _project(client, h, "W11A2")
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h)
    # Move the project to phase 31 (avant-projet) — the rail should drive this
    client.patch(f"/api/projects/{pid}", json={"phase_code": "31"}, headers=h)
    ns = client.get(f"/api/projects/{pid}/next-step", headers=h).json()
    # Window is now phase 31 + phase 32 (current + 1 look-ahead)
    assert set(ns["window"]) == {"31", "32"}
    # No phase-11 steps in 'steps' anymore (those phases are behind us — they
    # appear in upcoming OR are filtered out depending on status)
    assert all(s["phase"] in {"31", "32"} for s in ns["steps"])


def test_explicit_phase_query_still_works(client, owner):
    """Explicitly asking ?phase=33 still returns phase 33 steps even when the
    project is at phase 11 — useful for the dossier-de-permis surface."""
    h = owner["headers"]
    pid = _project(client, h, "W11A3")
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h)
    ns = client.get(f"/api/projects/{pid}/next-step?phase=33", headers=h).json()
    assert ns["window"] == ["33"]
    assert ns["steps"] and all(s["phase"] == "33" for s in ns["steps"])


def test_checklist_unfinished_items_appear_in_next_step(client, owner):
    """W11.A also wires the seeded SIA checklist as a next-step source — for
    each phase, the unfinished items ARE the prochain pas."""
    h = owner["headers"]
    pid = _project(client, h, "W11A4")
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h)
    client.patch(f"/api/projects/{pid}", json={"phase_code": "11"}, headers=h)
    ns = client.get(f"/api/projects/{pid}/next-step", headers=h).json()
    # Some of the steps must be checklist items (not just permit blockers)
    assert any(s["kind"] == "checklist" for s in ns["steps"])
