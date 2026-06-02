"""Source + evidence store services (re-exported from ``pilot.evidence_store``)."""
from __future__ import annotations

from . import _bootstrap  # noqa: F401

import evidence_store as _evidence_store

write_source = _evidence_store.write_source
write_evidence = _evidence_store.write_evidence
list_sources = _evidence_store.list_sources
list_evidence = _evidence_store.list_evidence
resolve_source = _evidence_store.resolve_source
resolve_source_ref = _evidence_store.resolve_source_ref
unresolved_source_refs = _evidence_store.unresolved_source_refs
public_source_view = _evidence_store.public_source_view
looks_like_local_path = _evidence_store.looks_like_local_path

__all__ = [
    "write_source",
    "write_evidence",
    "list_sources",
    "list_evidence",
    "resolve_source",
    "resolve_source_ref",
    "unresolved_source_refs",
    "public_source_view",
    "looks_like_local_path",
]
