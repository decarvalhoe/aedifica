"""Reusable Aedifica pilot domain services.

This module keeps regulatory/envelope logic away from command-line renderers so
the same behavior can feed the workspace, reports, and later APIs.
"""
from __future__ import annotations

import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))


class AedificaDomainError(Exception):
    """Structured domain error suitable for API/report rendering."""

    code = "DOMAIN_ERROR"

    def __init__(self, message: str, **details):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class NetworkSourceError(AedificaDomainError):
    code = "NETWORK_SOURCE_ERROR"


class UnsupportedCommuneError(AedificaDomainError):
    code = "UNSUPPORTED_COMMUNE"


class MissingPackError(AedificaDomainError):
    code = "MISSING_PACK"


class AmbiguousZoneError(AedificaDomainError):
    code = "AMBIGUOUS_ZONE"


def polygon_area_m2(rings):
    """Shoelace area (m2) of the outer ring; coords are already in LV95 metres."""
    if not rings:
        return None
    ring = rings[0]
    s = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def load_commune_ruleset(commune: str | None, required: bool = False):
    slug = (commune or "").strip().lower()
    if not slug:
        if required:
            raise UnsupportedCommuneError("Commune is required for a regulatory route.")
        return None
    path = os.path.join(HERE, slug, "rpga_zones.json")
    if not os.path.exists(path):
        if required:
            raise MissingPackError("No ingested commune pack for this commune.", commune=commune, path=path)
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def match_communal_zone(ruleset: dict | None, constraints: dict, strict: bool = False):
    """Map an OEREB zone designation to an ingested communal zone.

    Returns (zone_name, zone_params, match_method). Raises structured errors in
    strict mode; otherwise returns (None, None, None) for unresolved cases.
    """
    if not ruleset:
        if strict:
            raise MissingPackError("Cannot match a zone without a commune ruleset.")
        return None, None, None

    zones = ruleset.get("zones", {})
    demo_parcel_zone = ruleset.get("demo_parcel_zone") or {}
    if demo_parcel_zone.get("communal_zone") and str(demo_parcel_zone.get("parcel")) == str(constraints.get("parcel")):
        name = demo_parcel_zone["communal_zone"]
        matches = [z for z in zones if name == z or name.lower().startswith(z.lower())]
        if len(matches) == 1:
            return matches[0], zones[matches[0]], "demo"
        if len(matches) > 1 and strict:
            raise AmbiguousZoneError("Demo parcel zone maps to multiple commune zones.", matches=matches)

    zone_text = (constraints.get("zone") or "").lower()
    exact_matches = [name for name in zones if name.lower() in zone_text]
    if len(exact_matches) == 1:
        name = exact_matches[0]
        return name, zones[name], "exact"
    if len(exact_matches) > 1 and strict:
        raise AmbiguousZoneError("OEREB zone maps to multiple commune zones.", matches=exact_matches)

    signals = (
        "villa",
        "faible",
        "moyenne",
        "forte",
        "centr",
        "historique",
        "publique",
        "ferrov",
        "parc",
        "rives",
        "forest",
        "verdure",
        "détente",
        "sportif",
    )
    zone_signals = [signal for signal in signals if signal in zone_text]
    keyword_matches = [name for name in zones if any(signal in name.lower() for signal in zone_signals)]
    if len(keyword_matches) == 1:
        name = keyword_matches[0]
        return name, zones[name], "keyword"
    if len(keyword_matches) > 1 and strict:
        raise AmbiguousZoneError("Zone keyword match is ambiguous.", matches=keyword_matches)
    return None, None, None


def calculate_envelope(area_m2, zone_params: dict | None) -> dict:
    """Compute envelope values while preserving unknown numeric fields as None."""
    zone_params = zone_params or {}
    try:
        area = float(area_m2) if area_m2 is not None else None
    except (TypeError, ValueError):
        area = None
    ibus = zone_params.get("ibus")
    ius = zone_params.get("ius")
    ios = zone_params.get("ios")
    index = ibus if ibus is not None else ius
    index_name = "IBUS" if ibus is not None else "IUS"
    return {
        "area_m2": area,
        "index_name": index_name if index is not None else None,
        "index_value": index,
        "ios": ios,
        "max_sbp_m2": round(area * index, 2) if area and index is not None else None,
        "max_footprint_m2": round(area * ios, 2) if area and ios is not None else None,
        "height_corniche_m": zone_params.get("height_corniche_m"),
        "height_faite_m": zone_params.get("height_faite_m"),
        "levels_max": zone_params.get("levels_max"),
        "setback_min_m": zone_params.get("setback_min_m"),
        "provenance": zone_params.get("provenance") or {},
    }


def parse_oereb_extract(extract: dict) -> dict:
    """Domain wrapper around the current OEREB parser."""
    import oereb

    return oereb.parse(extract)

