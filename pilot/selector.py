"""Regulatory route / selector — composes the active jurisdiction layers for a parcel.

Demonstrates the engine + jurisdiction-pack design (docs/strategy/knowledge-architecture.md):
a parcel's "regulatory route" = Federal core (always) + Canton overlay (selectable) + Commune
overlay (selectable). Only the active layers are consulted; communes are pluggable. Adding a
country = adding a federal/canton/commune layer set — the selector logic is unchanged.

Run:  python pilot/selector.py
"""
from datetime import date, datetime, timezone
import glob
import json
import os
import sys

try:  # show accents/box chars correctly on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(HERE, "registry")
ROUTE_SCHEMA_VERSION = "1.0"


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _relative(path):
    return os.path.relpath(path, HERE).replace("\\", "/") if path else None


def _source_version_id(source_version):
    if not isinstance(source_version, dict):
        return None
    status = source_version.get("source_status")
    verified = source_version.get("verified_at")
    return f"{status}@{verified}" if status and verified else None


def _layer(
    layer_id,
    level,
    jurisdiction,
    data,
    path,
    state,
    evaluated_at,
    selected_at=None,
    inactive_reason=None,
):
    source_version = (data or {}).get("source_version") or {}
    out = {
        "layer_id": layer_id,
        "level": level,
        "jurisdiction": jurisdiction,
        "state": state,
        "evaluated_at": evaluated_at,
        "source_ref": _relative(path),
        "schema_version": (data or {}).get("schema_version"),
        "source_version_id": _source_version_id(source_version),
        "source_version": source_version,
    }
    if selected_at:
        out["selected_at"] = selected_at
    if inactive_reason:
        out["inactive_reason"] = inactive_reason
    return out


def list_communes():
    """Discover ingested commune rulesets: pilot/<slug>/rpga_zones.json."""
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "*", "rpga_zones.json"))):
        d = _load(p)
        out[d.get("commune") or os.path.basename(os.path.dirname(p))] = p
    return out


def _registry_path(canton):
    return os.path.join(REG, f"canton_{(canton or '').lower()}.json")


def _commune_path(commune):
    slug = (commune or "").strip().lower()
    return os.path.join(HERE, slug, "rpga_zones.json")


def federal_layer():
    p = os.path.join(REG, "federal.json")
    return _load(p) if os.path.exists(p) else None


def canton_layer(canton):
    p = _registry_path(canton)
    return _load(p) if os.path.exists(p) else None


def load_commune(commune):
    p = _commune_path(commune)
    return _load(p) if os.path.exists(p) else None


def regulatory_route(country="CH", canton="VD", commune="Lausanne", selected_at=None, evaluated_at=None):
    """Build the durable route object used by project manifests and reports."""
    selected_at = selected_at or _now_iso()
    evaluated_at = evaluated_at or selected_at
    route = {
        "schema_version": ROUTE_SCHEMA_VERSION,
        "route_id": f"{country}-{canton}-{commune}".upper().replace(" ", "-"),
        "country": country,
        "canton": canton,
        "commune": commune,
        "selected_at": selected_at,
        "evaluated_at": evaluated_at,
        "active_layers": [],
        "inactive_layers": [],
        "freshness_warnings": [],
    }

    federal_path = os.path.join(REG, "federal.json")
    fed = _load(federal_path) if os.path.exists(federal_path) else None
    if country == "CH" and fed:
        route["active_layers"].append(
            _layer("CH/federal", "federal", "CH", fed, federal_path, "active", evaluated_at, selected_at)
        )
    elif fed:
        route["inactive_layers"].append(
            _layer(
                "CH/federal",
                "federal",
                "CH",
                fed,
                federal_path,
                "inactive",
                evaluated_at,
                inactive_reason="country_not_selected",
            )
        )

    canton_path = _registry_path(canton)
    can = _load(canton_path) if os.path.exists(canton_path) else None
    if can:
        route["active_layers"].append(
            _layer(f"{canton}/cantonal", "cantonal", canton, can, canton_path, "active", evaluated_at, selected_at)
        )
    else:
        route["inactive_layers"].append(
            {
                "layer_id": f"{canton}/cantonal",
                "level": "cantonal",
                "jurisdiction": canton,
                "state": "inactive",
                "evaluated_at": evaluated_at,
                "inactive_reason": "missing_pack",
                "source_ref": None,
                "schema_version": None,
                "source_version_id": None,
                "source_version": {},
            }
        )

    selected_commune_path = _commune_path(commune)
    selected_commune = _load(selected_commune_path) if os.path.exists(selected_commune_path) else None
    if selected_commune:
        route["active_layers"].append(
            _layer(
                f"{commune}/communal",
                "communal",
                commune,
                selected_commune,
                selected_commune_path,
                "active",
                evaluated_at,
                selected_at,
            )
        )
    else:
        route["inactive_layers"].append(
            {
                "layer_id": f"{commune}/communal",
                "level": "communal",
                "jurisdiction": commune,
                "state": "inactive",
                "evaluated_at": evaluated_at,
                "inactive_reason": "missing_pack",
                "source_ref": None,
                "schema_version": None,
                "source_version_id": None,
                "source_version": {},
            }
        )

    for other_commune, path in list_communes().items():
        if other_commune == commune:
            continue
        data = _load(path)
        route["inactive_layers"].append(
            _layer(
                f"{other_commune}/communal",
                "communal",
                other_commune,
                data,
                path,
                "inactive",
                evaluated_at,
                inactive_reason="not_selected_for_project",
            )
        )

    route["freshness_warnings"] = pack_freshness_warnings(route)
    return route


def pack_freshness_warnings(route_obj, today=None):
    """Return non-blocking freshness warnings for expired or malformed review_due values."""
    today_date = date.fromisoformat(today) if isinstance(today, str) else today
    today_date = today_date or date.today()
    warnings = []
    for layer in (route_obj or {}).get("active_layers", []) + (route_obj or {}).get("inactive_layers", []):
        source_version = layer.get("source_version") or {}
        review_due = source_version.get("review_due")
        if not review_due:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "missing_review_due",
                    "layer_id": layer.get("layer_id"),
                    "message": "Pack has no review_due; re-check before relying on this route.",
                }
            )
            continue
        try:
            due = date.fromisoformat(review_due)
        except ValueError:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "invalid_review_due",
                    "layer_id": layer.get("layer_id"),
                    "review_due": review_due,
                    "message": "Pack review_due is not an ISO date; re-check source freshness.",
                }
            )
            continue
        if due < today_date:
            warnings.append(
                {
                    "severity": "warning",
                    "code": "pack_review_overdue",
                    "layer_id": layer.get("layer_id"),
                    "review_due": review_due,
                    "message": f"Pack review was due on {review_due}; re-check source before project reliance.",
                }
            )
    return warnings


def route(country="CH", canton="VD", commune="Lausanne"):
    """Compose the regulatory route: only Federal + the chosen canton + the chosen commune are active."""
    route_obj = regulatory_route(country, canton, commune)
    fed, can, com = federal_layer(), canton_layer(canton), load_commune(commune)
    active = []
    if fed:
        active.append(f"{country}/federal  — {len(fed['units'])} actes (LAT, OPB, LHand, AEAI…)")
    if can:
        active.append(f"{canton}/cantonal — {len(can['units'])} actes (LATC, RLATC, LRou…)")
    if com:
        active.append(f"{commune}/communal — {len(com['zones'])} zones ({com['document']['title'][:32]}…)")
    route_obj.update({"active": active, "federal": fed, "canton_layer": can, "commune_layer": com})
    return route_obj


def resolve_zone(commune, zone_name):
    com = load_commune(commune)
    return (com or {}).get("zones", {}).get(zone_name) if com else None


def _zone_density(zp):
    if zp.get("ius") is not None:
        return f"IUS {zp['ius']:g}"
    if zp.get("ibus") is not None:
        return f"IBUS {zp['ibus']:g}"
    if zp.get("ios") is not None:
        return f"IOS {zp['ios']:g} (emprise au sol)"
    return "pas d'indice (densité géométrique)"


if __name__ == "__main__":
    communes = list_communes()
    print("Communes ingérées :", ", ".join(communes) or "(aucune)")
    for canton, commune in [("VD", "Lausanne"), ("VD", "Pully")]:
        r = route("CH", canton, commune)
        print(f"\n■ Route réglementaire — CH / {canton} / {commune}")
        for a in r["active"]:
            print("    + " + a)
        com = r["commune_layer"]
        if com:
            print(f"    style de règles : {com['document'].get('note','')[:90]}…")
            for zname, zp in list(com["zones"].items())[:3]:
                bits = [_zone_density(zp)]
                if zp.get("height_faite_m") is not None:
                    bits.append(f"faîte {zp['height_faite_m']:g} m")
                if zp.get("height_corniche_m") is not None:
                    bits.append(f"corniche {zp['height_corniche_m']:g} m")
                if zp.get("levels_max") is not None:
                    bits.append(f"{zp['levels_max']:g} niveaux")
                print(f"        · {zname}: " + "; ".join(bits))
    print("\nLe sélecteur n'active que Federal + le canton choisi + la commune choisie.")
    print("Mêmes contrats (unité canonique, provenance, contrat de preuve) ; styles de règles différents.")
