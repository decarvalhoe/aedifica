"""Domain services — envelope, OEREB and parcel logic.

Re-exported from ``pilot.domain`` so product code imports a stable namespace.
"""
from __future__ import annotations

from . import _bootstrap  # noqa: F401

import domain as _domain

AedificaDomainError = _domain.AedificaDomainError
NetworkSourceError = _domain.NetworkSourceError
UnsupportedCommuneError = _domain.UnsupportedCommuneError
MissingPackError = _domain.MissingPackError
AmbiguousZoneError = _domain.AmbiguousZoneError

polygon_area_m2 = _domain.polygon_area_m2
load_commune_ruleset = _domain.load_commune_ruleset
match_communal_zone = _domain.match_communal_zone
calculate_envelope = _domain.calculate_envelope
parse_oereb_extract = _domain.parse_oereb_extract

__all__ = [
    "AedificaDomainError",
    "NetworkSourceError",
    "UnsupportedCommuneError",
    "MissingPackError",
    "AmbiguousZoneError",
    "polygon_area_m2",
    "load_commune_ruleset",
    "match_communal_zone",
    "calculate_envelope",
    "parse_oereb_extract",
]
