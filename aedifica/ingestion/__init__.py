"""On-demand commune ingestion (AED-129/#168).

Any commune can be requested at runtime and moves seed -> ingested -> supported
as its official règlement is captured and versioned. Static pilot packs become
seed data. No fabricated values: a seed/un-ingested commune is never usable.
"""
from __future__ import annotations

from .service import (
    ingest_pack,
    list_packs,
    promote,
    request_commune,
    seed_from_static,
    support_state,
)
from .nomos_bundle import NomosBundleError, import_nomos_bundle

__all__ = [
    "request_commune",
    "ingest_pack",
    "promote",
    "support_state",
    "seed_from_static",
    "list_packs",
    "NomosBundleError",
    "import_nomos_bundle",
]
