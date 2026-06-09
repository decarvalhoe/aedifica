"""Country-aware commune resolver entry point.

The HTTP layer hits ``resolve(country, commune)``; this module dispatches to
the right per-country backend. Adding a new country = adding a new module
under ``aedifica/jurisdictions/`` and registering it here. The return shape
is identical across countries:

    {
        "country": "CH",
        "commune": "<raw input>",
        "canton": "NE"            # only when confidence == "exact"
        "canonical": "Neuchâtel", # only when confidence == "exact"
        "confidence": "exact" | "ambiguous" | "unknown",
        "candidates": [{"canton": "NE", "name": "Neuchâtel"}, ...],
        "all_cantons": [...]      # only when confidence == "unknown"
    }
"""
from __future__ import annotations

from . import swiss

_SUPPORTED_COUNTRIES = ("CH",)


def resolve(country: str, commune: str) -> dict:
    code = (country or "CH").strip().upper()
    if code == "CH":
        return swiss.resolve_swiss(commune)
    return {"country": code, "commune": commune, "confidence": "unknown",
            "candidates": [], "all_cantons": [],
            "error": f"country {code!r} not yet supported — current support: {list(_SUPPORTED_COUNTRIES)}"}


def list_countries() -> list[dict]:
    return [{"country": "CH", "name": "Suisse"}]


def list_regions(country: str) -> list[dict]:
    """Full region list for a country (manual fallback when the commune is
    unknown). ``regions`` is the generic term — cantons in CH, départements
    in FR, Länder in DE, etc."""
    code = (country or "CH").strip().upper()
    if code == "CH":
        return swiss.list_swiss_cantons()
    return []


def freshness(country: str = "CH") -> dict:
    """Snapshot metadata so the UI can show 'Données OFS au 1.1.2025'."""
    code = (country or "CH").strip().upper()
    if code == "CH":
        return {"country": "CH", **swiss.freshness()}
    return {"country": code, "source": None}
