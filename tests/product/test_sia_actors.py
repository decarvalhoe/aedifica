"""W21-5 — « intervenants par phase » (feuille SIA Vaud) exposed by the API.

The mapping is DERIVED from the checklist template (single source), so the
dashboard card can never drift from the checklist it summarizes.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from aedifica.api import sia_checklist as siacl  # noqa: E402


def test_actors_by_phase_is_derived_and_complete():
    mapping = siacl.actors_by_phase()
    # Every official sub-phase is present, and no phase is silently empty —
    # the SIA sheet has deliverables in each.
    assert list(mapping.keys()) == siacl.PHASE_ORDER
    assert all(mapping[ph] for ph in siacl.PHASE_ORDER), mapping
    # Only known actors, and phase 11 carries the client AND the architect
    # (the SIA 112 'devoirs du MO' insight).
    assert all(a in siacl.ACTORS for actors in mapping.values() for a in actors)
    assert "mo" in mapping["11"] and "architecte" in mapping["11"]
    # Derivation, not declaration: every (phase, actor) pair traces back to a
    # template row.
    template_pairs = {(ph, actor) for ph, actor, _ in siacl.TEMPLATE}
    for ph, actors in mapping.items():
        for a in actors:
            assert (ph, a) in template_pairs


def test_checklist_endpoint_exposes_sia_actors_by_phase(client, owner):
    h = owner["headers"]
    client.post("/api/projects", json={"project_id": "P-ACT", "name": "P", "commune": "Lausanne", "canton": "VD"}, headers=h)
    body = client.get("/api/projects/P-ACT/checklist", headers=h).json()
    assert body["sia_actors_by_phase"] == siacl.actors_by_phase()
