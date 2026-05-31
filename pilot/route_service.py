"""Regulatory route service — reusable CH + canton + commune route selection.

Wraps the selector composition into a single product service that returns active
layers, inactive layers, pack versions and freshness warnings, plus an explicit
commune support state (supported / seed / on_demand / unsupported). The selector
CLI keeps working unchanged; this is the importable surface for the API/UI.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import selector  # noqa: E402

ROUTE_SERVICE_VERSION = "1.0"
SUPPORT_STATES = {"supported", "seed", "on_demand", "unsupported"}


def commune_support_state(commune: str) -> dict:
    """Classify a commune against the ingested pack registry.

    ``supported`` = an ingested communal pack exists. Anything else is
    ``unsupported`` here; seed/on_demand are reserved for the ingestion workflow
    (see docs/planning/next-commune-ingestion-checklist.md) and never fabricate
    legal values.
    """
    communes = selector.list_communes()
    if commune in communes:
        return {"commune": commune, "state": "supported", "pack_ref": selector._relative(communes[commune])}
    return {
        "commune": commune,
        "state": "unsupported",
        "pack_ref": None,
        "next_action": "Ingest the commune règlement before relying on numeric envelope values.",
    }


def _pack_versions(route: dict) -> list:
    versions = []
    for layer in route.get("active_layers", []) + route.get("inactive_layers", []):
        versions.append(
            {
                "layer_id": layer.get("layer_id"),
                "level": layer.get("level"),
                "state": layer.get("state"),
                "source_version_id": layer.get("source_version_id"),
                "review_due": (layer.get("source_version") or {}).get("review_due"),
            }
        )
    return versions


def select_route(country: str = "CH", canton: str = "VD", commune: str = "Lausanne") -> dict:
    """Return the structured regulatory route for a project context."""
    route = selector.regulatory_route(country, canton, commune)
    support = commune_support_state(commune)
    active_layers = route.get("active_layers", [])
    communal_active = any(layer.get("level") == "communal" for layer in active_layers)
    return {
        "schema_version": ROUTE_SERVICE_VERSION,
        "route_id": route["route_id"],
        "country": country,
        "canton": canton,
        "commune": commune,
        "support_state": support["state"],
        "supported": support["state"] == "supported",
        "communal_layer_active": communal_active,
        "active_layers": active_layers,
        "inactive_layers": route.get("inactive_layers", []),
        "pack_versions": _pack_versions(route),
        "freshness_warnings": selector.pack_freshness_warnings(route),
        "unsupported": None if support["state"] == "supported" else support,
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    for canton, commune in [("VD", "Lausanne"), ("VD", "Pully"), ("GE", "Genève")]:
        result = select_route("CH", canton, commune)
        print(
            f"{result['route_id']}: support={result['support_state']} "
            f"active={len(result['active_layers'])} inactive={len(result['inactive_layers'])} "
            f"warnings={len(result['freshness_warnings'])}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
