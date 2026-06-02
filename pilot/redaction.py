"""Privacy redaction pass for shareable artifacts.

Partner project material can contain client names, addresses, emails, phone
numbers and sensitive local file paths. Before any artifact (demo transcript,
report, adapter evidence export) is shared, it must go through this pass.

Design rules:
- Redaction returns a NEW object; the original evidence stays in the project
  folder and is never mutated here.
- Values under known-sensitive keys are replaced wholesale.
- Free-text strings are scrubbed for emails, Swiss phone numbers and local paths.
- Structural/validation fields (ids, states, hashes, schema versions, source ids)
  are preserved so the redacted artifact still validates.
"""
from __future__ import annotations

import re

import evidence_store

REDACTED = "[redacted]"

# Keys whose value is sensitive regardless of content.
SENSITIVE_KEYS = {
    "client_name",
    "owner_name",
    "contact_name",
    "author",
    "author_email",
    "participants",
    "email",
    "phone",
    "tel",
    "telephone",
    "address",
    "postal_address",
    "local_path",
    "file_path",
    "absolute_path",
    "gps",
    "coordinates",
}

# Keys that must always be kept verbatim (validation/structure).
PRESERVED_KEYS = {
    "schema_version",
    "report_id",
    "claim_id",
    "source_id",
    "evidence_id",
    "state",
    "claim_state",
    "kind",
    "sha256",
    "content_sha256",
    "phase_code",
    "project_id",
}

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+41|0041|0)\s?\d{2}[\s.\-]?\d{3}[\s.\-]?\d{2}[\s.\-]?\d{2}")


def redact_text(value: str) -> str:
    value = _EMAIL_RE.sub(REDACTED, value)
    value = _PHONE_RE.sub(REDACTED, value)
    if evidence_store.looks_like_local_path(value):
        value = REDACTED
    return value


def redact_artifact(obj):
    """Return a deep-redacted copy of obj (dict/list/str/other)."""
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key in PRESERVED_KEYS:
                out[key] = value
            elif key in SENSITIVE_KEYS:
                out[key] = REDACTED
            else:
                out[key] = redact_artifact(value)
        return out
    if isinstance(obj, list):
        return [redact_artifact(item) for item in obj]
    if isinstance(obj, str):
        return redact_text(obj)
    return obj


def find_sensitive(obj, _key=None) -> list:
    """Return a list of (path-ish) findings of unredacted sensitive data."""
    findings: list = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in SENSITIVE_KEYS and value not in (REDACTED, None, [], {}):
                findings.append(f"sensitive key '{key}'")
            findings.extend(find_sensitive(value, key))
    elif isinstance(obj, list):
        for item in obj:
            findings.extend(find_sensitive(item, _key))
    elif isinstance(obj, str):
        if _key in PRESERVED_KEYS:
            return findings
        if _EMAIL_RE.search(obj):
            findings.append("email in text")
        if _PHONE_RE.search(obj):
            findings.append("phone in text")
        if evidence_store.looks_like_local_path(obj):
            findings.append("local path in text")
    return findings


def redaction_report(original, redacted) -> dict:
    """Summarize what the pass removed vs kept."""
    return {
        "sensitive_before": find_sensitive(original),
        "sensitive_after": find_sensitive(redacted),
        "preserved_keys_present": sorted(
            {k for k in PRESERVED_KEYS if _contains_key(original, k)}
        ),
    }


def _contains_key(obj, target) -> bool:
    if isinstance(obj, dict):
        if target in obj:
            return True
        return any(_contains_key(v, target) for v in obj.values())
    if isinstance(obj, list):
        return any(_contains_key(v, target) for v in obj)
    return False
