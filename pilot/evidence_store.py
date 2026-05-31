"""Source + evidence store writer for a project workspace.

Aedifica can only claim provenance if source metadata and evidence extracts are
persisted consistently under the project folder. This module writes:

- ``sources/source_manifest.json`` — one entry per source (title, locator,
  retrieval time, valid-as-of, hash when available);
- ``evidence/evidence_manifest.json`` — one entry per stored evidence extract,
  with a project-relative ``file_ref`` and a SHA-256 hash.

It also resolves a claim ``source_ref`` back to a stored source entry, and keeps
sensitive local paths out of any user-facing view. Stdlib-only.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re

import artifacts

SCHEMA_VERSION = "1.0"
SOURCE_MANIFEST_REL = "sources/source_manifest.json"
EVIDENCE_MANIFEST_REL = "evidence/evidence_manifest.json"

# Anything that looks like an absolute local path must never reach a report.
_LOCAL_PATH_RE = re.compile(r"(^[A-Za-z]:[\\/]|^\\\\|/Users/|/home/|/root/|/var/folders/|/private/|AppData)")
_REDACTED = "[local path redacted]"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load(path: str, default: dict) -> dict:
    if not os.path.exists(path):
        return json.loads(json.dumps(default))
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def looks_like_local_path(value) -> bool:
    return bool(isinstance(value, str) and _LOCAL_PATH_RE.search(value))


def safe_locator(value):
    """Redact a locator if it leaks an absolute local path."""
    if looks_like_local_path(value):
        return _REDACTED
    return value


def source_manifest_path(project_dir: str) -> str:
    return os.path.join(project_dir, SOURCE_MANIFEST_REL)


def evidence_manifest_path(project_dir: str) -> str:
    return os.path.join(project_dir, EVIDENCE_MANIFEST_REL)


def write_source(
    project_dir: str,
    source_id: str,
    title: str,
    kind: str,
    valid_as_of: str,
    locator: str | None = None,
    retrieved_at: str | None = None,
    file_ref: str | None = None,
    sha256: str | None = None,
) -> dict:
    """Append/update a source entry. Local paths in locator/file_ref are redacted."""
    path = source_manifest_path(project_dir)
    manifest = _load(path, {"schema_version": SCHEMA_VERSION, "sources": []})
    entry = {
        "source_id": source_id,
        "title": title,
        "kind": kind,
        "valid_as_of": valid_as_of,
        "locator": safe_locator(locator) if locator is not None else None,
        "retrieved_at": retrieved_at or _now_iso(),
    }
    if file_ref is not None:
        entry["file_ref"] = _REDACTED if looks_like_local_path(file_ref) else file_ref.replace("\\", "/")
    if sha256 is not None:
        entry["sha256"] = sha256
    sources = [item for item in manifest.get("sources", []) if item.get("source_id") != source_id]
    sources.append(entry)
    manifest["schema_version"] = SCHEMA_VERSION
    manifest["sources"] = sources
    _write(path, manifest)
    return entry


def write_evidence(
    project_dir: str,
    evidence_id: str,
    kind: str,
    payload: dict,
    source_id: str | None = None,
    valid_as_of: str | None = None,
    retrieved_at: str | None = None,
) -> dict:
    """Write a JSON evidence extract under evidence/ and record it (hashed)."""
    evidence_rel = f"evidence/{evidence_id}.json"
    evidence_abs = os.path.join(project_dir, evidence_rel)
    _write(evidence_abs, payload)
    sha256 = artifacts.sha256_file(evidence_abs)

    path = evidence_manifest_path(project_dir)
    manifest = _load(path, {"schema_version": SCHEMA_VERSION, "evidence": []})
    entry = {
        "evidence_id": evidence_id,
        "kind": kind,
        "file_ref": f"project://{evidence_rel}",
        "sha256": sha256,
        "source_id": source_id,
        "valid_as_of": valid_as_of,
        "retrieved_at": retrieved_at or _now_iso(),
    }
    items = [item for item in manifest.get("evidence", []) if item.get("evidence_id") != evidence_id]
    items.append(entry)
    manifest["schema_version"] = SCHEMA_VERSION
    manifest["evidence"] = items
    _write(path, manifest)
    return {"evidence_id": evidence_id, "kind": kind, "file_ref": entry["file_ref"], "sha256": sha256}


def list_sources(project_dir: str) -> list:
    return _load(source_manifest_path(project_dir), {"sources": []}).get("sources", [])


def list_evidence(project_dir: str) -> list:
    return _load(evidence_manifest_path(project_dir), {"evidence": []}).get("evidence", [])


def resolve_source(project_dir: str, source_id: str) -> dict | None:
    for entry in list_sources(project_dir):
        if entry.get("source_id") == source_id:
            return entry
    return None


def resolve_source_ref(project_dir: str, source_ref: dict) -> dict | None:
    return resolve_source(project_dir, (source_ref or {}).get("source_id"))


def unresolved_source_refs(project_dir: str, source_refs: list) -> list:
    """Return the source_ids in source_refs that do not resolve to a stored source."""
    return [
        ref.get("source_id")
        for ref in source_refs or []
        if resolve_source_ref(project_dir, ref) is None
    ]


def public_source_view(entry: dict) -> dict:
    """A report-safe projection of a source entry: no local paths, no raw hashes path."""
    view = {k: v for k, v in (entry or {}).items() if k not in {"file_ref"}}
    if looks_like_local_path(view.get("locator")):
        view["locator"] = _REDACTED
    return view
