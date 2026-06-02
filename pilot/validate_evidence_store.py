#!/usr/bin/env python3
"""Validate the source + evidence store writer (stdlib only, offline).

Exercises the writer in a throwaway project and checks the durable contract:
recorded provenance fields, project-relative hashed evidence, source-ref
resolution, and redaction of sensitive local paths.

Run:
    python pilot/validate_evidence_store.py
"""
from dataclasses import dataclass, field
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import artifacts  # noqa: E402
import evidence_store  # noqa: E402


@dataclass
class EvidenceStoreReport:
    items: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def _exercise(project_dir: str, report: EvidenceStoreReport) -> None:
    evidence_ref = evidence_store.write_evidence(
        project_dir,
        evidence_id="EVID-OEREB-TEST",
        kind="api_extract",
        payload={"egrid": "CH000000000000", "zone": "Zone test 15 LAT"},
        source_id="VD-OEREB",
        valid_as_of="2026-05-29",
    )
    if not evidence_ref["file_ref"].startswith("project://evidence/"):
        report.add_error("evidence file_ref must be a project-relative project:// ref")
    if not artifacts.is_sha256(evidence_ref["sha256"]):
        report.add_error("evidence entry must carry a SHA-256 hash")

    source_entry = evidence_store.write_source(
        project_dir,
        source_id="VD-OEREB",
        title="Vaud RDPPF/OEREB parsed extract",
        kind="parcel_evidence",
        valid_as_of="2026-05-29",
        locator="EGRID CH000000000000",
        file_ref=evidence_ref["file_ref"],
        sha256=evidence_ref["sha256"],
    )
    for key in ("title", "locator", "retrieved_at", "valid_as_of"):
        if not source_entry.get(key):
            report.add_error(f"source entry missing {key}")

    if evidence_store.resolve_source_ref(project_dir, {"source_id": "VD-OEREB"}) is None:
        report.add_error("a written source_ref must resolve to a stored source entry")
    if not evidence_store.unresolved_source_refs(project_dir, [{"source_id": "DOES-NOT-EXIST"}]):
        report.add_error("unknown source_ref should be reported as unresolved")
    if evidence_store.unresolved_source_refs(project_dir, [{"source_id": "VD-OEREB"}]):
        report.add_error("known source_ref should resolve cleanly")

    # Redaction: an absolute local path must never be stored verbatim.
    leaky = evidence_store.write_source(
        project_dir,
        source_id="LEAKY",
        title="Source with a leaky locator",
        kind="local_file",
        valid_as_of="2026-05-29",
        locator=r"C:\Users\architect\secret\client_plan.pdf",
        file_ref=r"C:\Users\architect\secret\client_plan.pdf",
    )
    if evidence_store.looks_like_local_path(leaky.get("locator")):
        report.add_error("source locator must be redacted when it leaks a local path")
    if evidence_store.looks_like_local_path(leaky.get("file_ref")):
        report.add_error("source file_ref must be redacted when it leaks a local path")
    if evidence_store.looks_like_local_path(evidence_store.public_source_view(leaky).get("locator")):
        report.add_error("public source view must not expose a local path")

    report.items.append(
        {
            "project_dir": os.path.basename(project_dir),
            "source_count": len(evidence_store.list_sources(project_dir)),
            "evidence_count": len(evidence_store.list_evidence(project_dir)),
        }
    )


def validate_all() -> EvidenceStoreReport:
    report = EvidenceStoreReport()
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = os.path.join(tmp, "evidence-store-project")
        os.makedirs(project_dir, exist_ok=True)
        _exercise(project_dir, report)
    return report


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    report = validate_all()
    for item in report.items:
        print(f"PASS? {item['project_dir']}: {item['source_count']} sources, {item['evidence_count']} evidence")
    if report.errors:
        print("\nEvidence store validation errors:")
        for error in report.errors:
            print(f"  - {error}")
        return 1
    print("\nevidence store writer validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
