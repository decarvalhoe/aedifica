"""Privacy redaction services (re-exported from ``pilot.redaction``)."""
from __future__ import annotations

from . import _bootstrap  # noqa: F401

import redaction as _redaction

REDACTED = _redaction.REDACTED
SENSITIVE_KEYS = _redaction.SENSITIVE_KEYS
PRESERVED_KEYS = _redaction.PRESERVED_KEYS
redact_text = _redaction.redact_text
redact_artifact = _redaction.redact_artifact
find_sensitive = _redaction.find_sensitive
redaction_report = _redaction.redaction_report

__all__ = [
    "REDACTED",
    "SENSITIVE_KEYS",
    "PRESERVED_KEYS",
    "redact_text",
    "redact_artifact",
    "find_sensitive",
    "redaction_report",
]
