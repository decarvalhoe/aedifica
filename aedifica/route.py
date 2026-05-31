"""Regulatory route + pack services.

Re-exports ``pilot.selector`` composition and the structured ``route_service``
(supported / seed / unsupported commune state). See package-boundaries.md.
"""
from __future__ import annotations

from . import _bootstrap  # noqa: F401

import selector as _selector

regulatory_route = _selector.regulatory_route
pack_freshness_warnings = _selector.pack_freshness_warnings
list_communes = _selector.list_communes
resolve_zone = _selector.resolve_zone

try:  # route_service is added in the AED-093 wave; keep import resilient
    import route_service as _route_service

    select_route = _route_service.select_route
    commune_support_state = _route_service.commune_support_state
    SUPPORT_STATES = _route_service.SUPPORT_STATES
except ImportError:  # pragma: no cover - only before route_service exists
    select_route = None
    commune_support_state = None
    SUPPORT_STATES = None

__all__ = [
    "regulatory_route",
    "pack_freshness_warnings",
    "list_communes",
    "resolve_zone",
    "select_route",
    "commune_support_state",
    "SUPPORT_STATES",
]
