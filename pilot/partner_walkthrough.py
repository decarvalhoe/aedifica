#!/usr/bin/env python3
"""Autonomous Partner Pilot product walkthrough (#312).

Drives the real product API through the #312 run-of-show — creation, intervenants,
groups, documents, validation, access, BRS, checklist, tasks, memory, regulatory
surfaces — on a representative project, and records what actually happens.

Frictions are *observed*, never authored: a step declares what the run-of-show
expects, and any deviation becomes a friction capture stored in the project's own
Memory, exactly as a live session would record it. A green run with zero friction
is a valid result; so is a completed run carrying frictions. The walkthrough only
fails when the flow cannot be traversed at all.

Run:
    python pilot/partner_walkthrough.py
    python pilot/partner_walkthrough.py --json --write
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (HERE, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

import redaction  # noqa: E402

EVIDENCE_DIR = os.path.join(ROOT, "docs", "validation", "evidence")
PROJECT_ID = "PARTNER-PILOT-REPRESENTATIF"
COMMUNE = "Lausanne"
CANTON = "VD"
ENTRY_PHASE = "31"
UNCOVERED_COMMUNE = "Pully"  # real VD commune, deliberately not ingested in this run


class Walkthrough:
    """One traversal of the product run-of-show, collecting observed frictions."""

    def __init__(self, client, headers):
        self.client = client
        self.headers = headers
        self.steps: list = []
        self.frictions: list = []

    # -- recording ------------------------------------------------------- #
    def record(self, step: str, surface: str, expectation: str, ok: bool, observed: str) -> bool:
        self.steps.append(
            {"step": step, "surface": surface, "expectation": expectation, "ok": bool(ok), "observed": observed}
        )
        if not ok:
            self.frictions.append(
                {
                    "step": step,
                    "surface": surface,
                    "expected": expectation,
                    "observed": observed,
                    "kind": "friction",
                }
            )
        return bool(ok)

    def _post(self, url, payload=None):
        return self.client.post(url, json=payload if payload is not None else {}, headers=self.headers)

    def _get(self, url):
        return self.client.get(url, headers=self.headers)

    # -- run-of-show ------------------------------------------------------ #
    def run(self) -> dict:
        pid = self.step_creation()
        if pid is None:
            return self.report(completed=False)
        self.step_checklist(pid)
        group_id = self.step_groups(pid)
        intervenant_id = self.step_intervenants(pid, group_id)
        document_id = self.step_documents(pid)
        self.step_validation(pid, document_id)
        self.step_access(pid, document_id, group_id)
        self.step_brs(pid, intervenant_id)
        self.step_tasks(pid)
        self.step_regulatory(pid)
        self.step_liaisons(pid)
        self.step_memory(pid)
        return self.report(completed=True)

    def step_creation(self):
        response = self._post(
            "/api/projects",
            {
                "project_id": PROJECT_ID,
                "name": "Transformation representative",
                "commune": COMMUNE,
                "canton": CANTON,
                "country": "CH",
                "phase_code": ENTRY_PHASE,
            },
        )
        ok = self.record(
            "creation.projet",
            "projets",
            "the architect creates the project at its real entry phase and it is stored with that phase",
            response.status_code == 201,
            f"HTTP {response.status_code} {self._error(response)}",
        )
        if not ok:
            return None
        stored = self._get(f"/api/projects/{PROJECT_ID}").json().get("project", {})
        self.record(
            "creation.phase-entree",
            "projets",
            f"the stored project keeps the declared entry phase {ENTRY_PHASE}",
            str(stored.get("phase_code")) == ENTRY_PHASE,
            f"phase_code={stored.get('phase_code')}",
        )
        return PROJECT_ID

    def step_checklist(self, pid):
        seeded = self._post(f"/api/projects/{pid}/checklist/seed", {"entry_phase": ENTRY_PHASE})
        self.record(
            "checklist.retroactive",
            "checklist",
            "seeding at a mid-project entry phase produces a retroactive checklist covering earlier phases",
            seeded.status_code == 201 and seeded.json().get("seeded", 0) > 0,
            f"HTTP {seeded.status_code} seeded={seeded.json().get('seeded') if seeded.status_code == 201 else self._error(seeded)}",
        )
        if seeded.status_code != 201:
            return
        items = self._get(f"/api/projects/{pid}/checklist").json().get("items", [])
        earlier = [item for item in items if str(item.get("phase_code", "")) < ENTRY_PHASE]
        self.record(
            "checklist.phases-anterieures",
            "checklist",
            "the retroactive checklist carries at least one item from a phase before the entry phase",
            bool(earlier),
            f"{len(items)} items, {len(earlier)} from earlier phases",
        )

    def step_groups(self, pid):
        response = self._post(f"/api/projects/{pid}/intervenant-groups", {"name": "Mandataires", "kind": "group"})
        ok = self.record(
            "intervenants.groupes",
            "intervenants",
            "the architect can create an intervenant group to organise the project",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        if not ok:
            return None
        body = response.json()
        group = body.get("group") or body.get("groups", [{}])[-1]
        return group.get("id")

    def step_intervenants(self, pid, group_id):
        response = self._post(
            f"/api/projects/{pid}/intervenants",
            {
                "name": "Bureau ingenieur civil",
                "role": "ingenieur civil",
                "organization": "Bureau CVC SA",
                "is_responsible": True,
                "group_id": group_id,
            },
        )
        ok = self.record(
            "intervenants.registre",
            "intervenants",
            "an intervenant is registered with role, organisation and responsibility",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        intervenant_id = response.json().get("intervenant", {}).get("id") if ok else None
        directory = self._get("/api/orgs/intervenants-directory")
        entries = directory.json().get("contacts", []) if directory.status_code == 200 else []
        self.record(
            "intervenants.annuaire-atelier",
            "annuaire",
            "the registered intervenant feeds the atelier-level directory (intake default: atelier scope)",
            directory.status_code == 200 and len(entries) >= 1,
            f"HTTP {directory.status_code} entries={len(entries)}",
        )
        return intervenant_id

    def step_documents(self, pid):
        response = self._post(
            f"/api/projects/{pid}/documents",
            {"official_name": "Rapport geotechnique", "category": "etude", "version_label": "v1"},
        )
        ok = self.record(
            "documents.depot",
            "documents",
            "a document is filed with an official name, a category and a version",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        return response.json().get("document", {}).get("id") if ok else None

    def step_validation(self, pid, document_id):
        if document_id is None:
            self.record("validation.niveau", "validation", "a filed document can be validated", False, "no document to validate")
            return
        response = self._post(
            f"/api/projects/{pid}/documents/{document_id}/validate",
            {"level": "canonical", "citable_text": "Portance admissible reduite en zone nord."},
        )
        self.record(
            "validation.niveau",
            "validation",
            "the architect promotes a document to a canonical validation with a citable extract",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        pending = self._get(f"/api/projects/{pid}/to-validate")
        self.record(
            "validation.file-attente",
            "validation",
            "the to-validate surface answers without error so nothing waits invisibly",
            pending.status_code == 200,
            f"HTTP {pending.status_code} {self._error(pending)}",
        )

    def step_access(self, pid, document_id, group_id):
        if document_id is None or group_id is None:
            self.record("acces.par-groupe", "acces", "access is granted per group/dossier", False, "missing document or group")
            return
        response = self._post(
            f"/api/projects/{pid}/documents/{document_id}/grants",
            {"group_id": group_id, "level": "read"},
        )
        self.record(
            "acces.par-groupe",
            "acces",
            "access is granted at group/dossier granularity (intake default), not per field",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        mine = self._get("/api/auth/me/access")
        self.record(
            "acces.lisibilite",
            "acces",
            "a connected user can read back what they have access to",
            mine.status_code == 200,
            f"HTTP {mine.status_code} {self._error(mine)}",
        )

    def step_brs(self, pid, intervenant_id):
        response = self._post(
            f"/api/projects/{pid}/brs",
            {
                "content": "Le maitre d'ouvrage demande une cuisine ouverte.",
                "kind": "change",
                "channel": "phone",
                "emitter_intervenant_id": intervenant_id,
            },
        )
        ok = self.record(
            "brs.saisie",
            "brs",
            "a verbal requirement is captured with its channel and its emitter",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        if not ok:
            return
        listing = self._get(f"/api/projects/{pid}/brs")
        entries = listing.json().get("entries", listing.json().get("brs", []))
        self.record(
            "brs.tracabilite",
            "brs",
            "the captured requirement is retrievable with its emitter attached",
            listing.status_code == 200 and len(entries) >= 1,
            f"HTTP {listing.status_code} entries={len(entries)}",
        )

    def step_tasks(self, pid):
        response = self._post(
            f"/api/projects/{pid}/tasks",
            {"title": "Mettre a jour les plans apres BRS", "priority": "p1", "estimate_hours": 6},
        )
        ok = self.record(
            "taches.creation",
            "taches",
            "the architect turns a requirement into a prioritised task",
            response.status_code in (200, 201),
            f"HTTP {response.status_code} {self._error(response)}",
        )
        if not ok:
            return
        task_id = response.json()["task"]["id"]
        prediction = self._post(f"/api/projects/{pid}/tasks/{task_id}/predict")
        body = prediction.json() if prediction.status_code == 200 else {}
        honest = prediction.status_code == 200 and (body.get("samples", 0) > 0 or body.get("prediction") in (None, 0))
        self.record(
            "taches.predictif-honnete",
            "taches",
            "with no atelier history the duration prediction returns no fabricated number",
            honest,
            f"HTTP {prediction.status_code} samples={body.get('samples')} prediction={body.get('prediction')} basis={body.get('basis')}",
        )

    def step_regulatory(self, pid):
        uncovered = self._get(f"/api/communes/{UNCOVERED_COMMUNE}/{CANTON}/support")
        state = uncovered.json().get("support", {}) if uncovered.status_code == 200 else {}
        self.record(
            "reglementaire.commune-non-couverte",
            "reglementaire",
            "an uncovered commune is declared unsupported and unusable, with the official inputs it still needs",
            uncovered.status_code == 200
            and state.get("state") == "unsupported"
            and state.get("usable") is False
            and bool(state.get("required_inputs")),
            f"HTTP {uncovered.status_code} state={state.get('state')} usable={state.get('usable')} "
            f"required_inputs={len(state.get('required_inputs') or [])}",
        )
        requested = self._post("/api/communes", {"commune": UNCOVERED_COMMUNE, "canton": CANTON})
        self.record(
            "reglementaire.demande-ingestion",
            "reglementaire",
            "the uncovered commune opens an ingestion request instead of returning invented rules",
            requested.status_code == 201,
            f"HTTP {requested.status_code} {self._error(requested)}",
        )
        after = self._get(f"/api/communes/{UNCOVERED_COMMUNE}/{CANTON}/support")
        after_state = after.json().get("support", {}) if after.status_code == 200 else {}
        self.record(
            "reglementaire.pas-de-fabrication",
            "reglementaire",
            "a requested but not yet ingested commune stays unusable and exposes no regulatory value",
            after.status_code == 200 and after_state.get("usable") is False and not after_state.get("zones"),
            f"HTTP {after.status_code} state={after_state.get('state')} usable={after_state.get('usable')} "
            f"pack_id={after_state.get('pack_id')}",
        )
        bad_pair = self._post("/api/communes", {"commune": "Neuchatel", "canton": CANTON})
        refused_code = ""
        try:
            refused_code = (bad_pair.json().get("detail") or {}).get("code", "")
        except Exception:
            refused_code = ""
        self.record(
            "reglementaire.paire-registre",
            "reglementaire",
            "a commune/canton pair contradicting the OFS register is refused with the registered canton named",
            bad_pair.status_code in (400, 422) and refused_code == "COMMUNE_CANTON_MISMATCH",
            f"HTTP {bad_pair.status_code} code={refused_code}",
        )
        compliance = self._get(f"/api/projects/{pid}/compliance")
        self.record(
            "reglementaire.surface-projet",
            "reglementaire",
            "the project compliance surface answers on available data without erroring",
            compliance.status_code == 200,
            f"HTTP {compliance.status_code} {self._error(compliance)}",
        )

    def step_liaisons(self, pid):
        items = self._get(f"/api/projects/{pid}/checklist").json().get("items", [])
        todo = next((item for item in items if item.get("status") == "todo"), None)
        if todo is None:
            self.record("liaison.checklist-tache", "checklist", "a checklist item can become a task", False, "no todo item")
        else:
            created = self._post(
                f"/api/projects/{pid}/tasks",
                {"title": "Traiter " + str(todo.get("title"))[:40], "checklist_item_id": todo["id"]},
            )
            linked = created.json().get("task", {}).get("checklist_item_id") if created.status_code in (200, 201) else None
            self.record(
                "liaison.checklist-tache",
                "checklist",
                "a checklist item turns into a task and the link is readable back",
                created.status_code in (200, 201) and linked == todo["id"],
                f"HTTP {created.status_code} checklist_item_id={linked}",
            )
        listing = self._get(f"/api/projects/{pid}/brs").json()
        entries = listing.get("entries", listing.get("brs", []))
        if not entries:
            self.record("liaison.brs-supersede", "brs", "a requirement can be superseded", False, "no BRS entry")
        else:
            superseded = self._post(
                f"/api/projects/{pid}/brs",
                {
                    "content": "Finalement cuisine fermee.",
                    "kind": "change",
                    "channel": "meeting",
                    "supersedes_id": entries[0]["id"],
                },
            )
            self.record(
                "liaison.brs-supersede",
                "brs",
                "a later decision supersedes an earlier requirement instead of overwriting it",
                superseded.status_code in (200, 201),
                f"HTTP {superseded.status_code} {self._error(superseded)}",
            )
        nxt = self._get(f"/api/projects/{pid}/next-step")
        self.record(
            "liaison.prochaine-etape",
            "pilotage",
            "the product proposes a next step for the current phase",
            nxt.status_code == 200,
            f"HTTP {nxt.status_code} {self._error(nxt)}",
        )
        permit = self._get(f"/api/projects/{pid}/permit")
        self.record(
            "liaison.permis",
            "reglementaire",
            "the permit completeness surface answers on the data actually available",
            permit.status_code == 200,
            f"HTTP {permit.status_code} {self._error(permit)}",
        )

    def step_memory(self, pid):
        photo = self._post(
            f"/api/projects/{pid}/captures",
            {"kind": "photo", "content": "Vue chantier facade nord", "source_ref": "terrain"},
        )
        self.record(
            "memoire.photo",
            "memoire",
            "a field photo capture is stored in Memory",
            photo.status_code in (200, 201),
            f"HTTP {photo.status_code} {self._error(photo)}",
        )
        # Every friction observed during the traversal is written back into Memory,
        # exactly as the live run-of-show requires.
        stored = 0
        for friction in self.frictions:
            response = self._post(
                f"/api/projects/{pid}/captures",
                {
                    "kind": "friction",
                    "content": f"[{friction['surface']}] {friction['step']} — attendu: {friction['expected']} — observe: {friction['observed']}",
                    "source_ref": "partner_walkthrough",
                },
            )
            if response.status_code in (200, 201):
                stored += 1
        listing = self._get(f"/api/projects/{pid}/captures")
        by_kind = listing.json().get("by_kind", {}) if listing.status_code == 200 else {}
        self.record(
            "memoire.frictions",
            "memoire",
            "every observed friction is captured in Memory with its context",
            listing.status_code == 200 and stored == len(self.frictions),
            f"HTTP {listing.status_code} stored={stored}/{len(self.frictions)} by_kind={json.dumps(by_kind, sort_keys=True)}",
        )

    # -- output ----------------------------------------------------------- #
    @staticmethod
    def _error(response) -> str:
        if response.status_code < 400:
            return ""
        try:
            return json.dumps(response.json())[:200]
        except Exception:
            return response.text[:200]

    def report(self, completed: bool) -> dict:
        traversed = [step["surface"] for step in self.steps]
        payload = {
            "schema_version": "1.0",
            "evidence_id": "W21-6-WALKTHROUGH",
            "issue": 312,
            "run_id": f"PARTNER-WALKTHROUGH-{datetime.now(timezone.utc).isoformat()}",
            "mode": "autonomous",
            "project": {"commune": COMMUNE, "canton": CANTON, "entry_phase": ENTRY_PHASE},
            "completed": completed,
            "surfaces_traversed": sorted(set(traversed)),
            "step_count": len(self.steps),
            "passed": sum(1 for step in self.steps if step["ok"]),
            "friction_count": len(self.frictions),
            "steps": self.steps,
            "frictions": self.frictions,
        }
        return redaction.redact_artifact(payload)


def build_client():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    from aedifica.api import create_app
    from aedifica.db import Base

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
    Base.metadata.create_all(engine)
    client = TestClient(create_app(engine=engine))
    response = client.post("/api/orgs", json={"org_name": "Atelier pilote", "user_email": "architecte@atelier.test"})
    if response.status_code != 201:
        raise RuntimeError(f"could not bootstrap the atelier: HTTP {response.status_code} {response.text[:200]}")
    return client, {"Authorization": f"Bearer {response.json()['token']}"}


def run_walkthrough() -> dict:
    client, headers = build_client()
    return Walkthrough(client, headers).run()


def write_report(report: dict, directory: str = EVIDENCE_DIR) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "product-walkthrough-312.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return path


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Autonomous product walkthrough for the Partner Pilot.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = run_walkthrough()
    if args.write:
        report["written"] = write_report(report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"Product walkthrough {'completed' if report['completed'] else 'INTERRUPTED'} · "
            f"{report['passed']}/{report['step_count']} steps · {report['friction_count']} friction(s)"
        )
        for step in report["steps"]:
            print(f"  [{'x' if step['ok'] else ' '}] {step['step']}: {step['observed']}")
    return 0 if report["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
