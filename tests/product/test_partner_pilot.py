"""Autonomous Partner Pilot rig: pre-flight, intake register, walkthrough, triage.

Covers the four pieces that replace the human-in-the-seat sessions of #330, #312,
#331, #105 and #115 with machine-verifiable runs.
"""
from __future__ import annotations

import json

import pytest

from aedifica import _bootstrap  # noqa: F401

import partner_preflight  # noqa: E402
import partner_triage  # noqa: E402
import partner_walkthrough  # noqa: E402
import validate_partner_intake  # noqa: E402


# --- pre-flight / Archicad evidence (#330, #105, #115) --------------------- #
def test_preflight_is_green_end_to_end_without_a_seat():
    result = partner_preflight.run_preflight()

    assert result["ok"] is True
    assert result["run"]["mode"] == "live"
    assert result["run"]["endpoint_kind"] == "replay_stand_in"
    failed = [check["id"] for check in result["run"]["checks"] if not check["ok"]]
    assert failed == []


def test_preflight_proves_a_real_before_value_and_no_mutation():
    evidence = partner_preflight.run_preflight()["dry_run_evidence"]

    assert evidence["issue"] == 105
    assert evidence["before_is_null"] is False
    assert evidence["before_sha256"] and len(evidence["before_sha256"]) == 64
    assert evidence["mutated"] is False
    assert evidence["model_unchanged_after_dry_run"] is True
    assert evidence["element_id"]


def test_audit_separates_present_missing_and_ignores_non_space_elements():
    evidence = partner_preflight.run_preflight()["audit_evidence"]

    assert evidence["issue"] == 115
    # The representative model carries 4 elements, one of which is a Wall.
    assert evidence["selected_element_count"] == 4
    assert evidence["audited_zone_count"] == 3
    assert evidence["missing_total"] == 2
    clean = [item for item in evidence["elements"] if not item["missing"]]
    assert len(clean) == 1, "a fully documented zone must produce no finding"
    for item in evidence["elements"]:
        assert len(item["present"]) + len(item["missing"]) == len(evidence["expected_properties"])


def test_preflight_fails_loudly_when_the_bridge_is_unavailable():
    result = partner_preflight.run_preflight(endpoint="http://127.0.0.1:1", timeout=0.1)

    assert result["ok"] is False
    failed = {check["id"] for check in result["run"]["checks"] if not check["ok"]}
    assert "bridge_live" in failed and "mode_live" in failed


def test_evidence_carries_no_sensitive_value():
    import redaction

    result = partner_preflight.run_preflight()
    for key in ("dry_run_evidence", "audit_evidence"):
        assert redaction.find_sensitive(result[key]) == []
    # The raw before value never reaches the shareable artifact.
    assert result["dry_run_evidence"]["shareable_diff"]["before"] == "[redacted]"


# --- intake register (#330) ------------------------------------------------ #
def test_intake_register_is_valid_and_leaves_nothing_awaiting_a_partner():
    assert validate_partner_intake.validate() == []


def test_intake_validator_rejects_a_stale_provenance(tmp_path):
    register = tmp_path / "intake.json"
    register.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "id": "produit.x",
                        "category": "produit",
                        "requirement": "r",
                        "status": "resolved_autonomously",
                        "resolution": "res",
                        "provenance": ["pilot/does_not_exist.py"],
                        "impact_if_partner_differs": "i",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_partner_intake.validate(str(register))
    assert any("does not exist" in error for error in errors)
    assert any("covers no entry for" in error for error in errors)


def test_intake_validator_rejects_an_entry_left_blocked(tmp_path):
    register = tmp_path / "intake.json"
    register.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "id": "archicad.x",
                        "category": "archicad",
                        "requirement": "r",
                        "status": "awaiting_partner",
                        "resolution": "res",
                        "provenance": [],
                        "impact_if_partner_differs": "i",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_partner_intake.validate(str(register))
    assert any("awaiting_partner" in error for error in errors)


# --- product walkthrough (#312) -------------------------------------------- #
@pytest.fixture(scope="module")
def walkthrough():
    return partner_walkthrough.run_walkthrough()


def test_walkthrough_traverses_creation_to_memory(walkthrough):
    assert walkthrough["completed"] is True
    assert walkthrough["passed"] == walkthrough["step_count"]
    assert {"projets", "intervenants", "documents", "validation", "acces", "brs", "checklist", "taches", "memoire"} <= set(
        walkthrough["surfaces_traversed"]
    )


def test_walkthrough_never_fabricates_regulatory_values(walkthrough):
    steps = {step["step"]: step for step in walkthrough["steps"]}
    assert steps["reglementaire.commune-non-couverte"]["ok"] is True
    assert steps["reglementaire.demande-ingestion"]["ok"] is True
    assert steps["reglementaire.pas-de-fabrication"]["ok"] is True
    assert steps["reglementaire.paire-registre"]["ok"] is True


def test_walkthrough_prediction_stays_silent_without_history(walkthrough):
    step = next(s for s in walkthrough["steps"] if s["step"] == "taches.predictif-honnete")
    assert step["ok"] is True
    assert "samples=0" in step["observed"] and "prediction=None" in step["observed"]


# --- friction triage (#331) ------------------------------------------------ #
def test_triage_of_an_empty_run_is_explicitly_empty():
    backlog = partner_triage.triage([])

    assert backlog["issue_count"] == 0
    assert "constat" in backlog["note"]


def test_triage_classifies_prioritises_and_routes_each_friction():
    frictions = [
        {"step": "documents.depot", "surface": "documents", "expected": "a document is filed", "observed": "HTTP 500 boom"},
        {"step": "maquette.selection", "surface": "archicad", "expected": "a zone is read", "observed": "entries=0"},
        {"step": "brs.saisie", "surface": "brs", "expected": "a requirement is captured", "observed": "HTTP 409 conflict"},
    ]
    backlog = partner_triage.triage(frictions)

    assert backlog["issue_count"] == 3
    drafts = {item["surface"]: item for item in backlog["backlog"]}
    assert drafts["documents"]["category"] == "bug" and drafts["documents"]["priority"] == "P0"
    assert drafts["archicad"]["parent_issue"] == 171
    assert drafts["brs"]["parent_issue"] == 312
    assert backlog["routed_to"]["171"] == 1 and backlog["routed_to"]["312"] == 2
    for item in backlog["backlog"]:
        assert item["category"] in partner_triage.CATEGORIES
        assert item["priority"] in ("P0", "P1", "P2")
        assert item["acceptance_criteria"] and item["expected_result"] and item["observed_result"]
        assert item["validation"].startswith("python ")
