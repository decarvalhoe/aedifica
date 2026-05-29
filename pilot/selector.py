"""Regulatory route / selector — composes the active jurisdiction layers for a parcel.

Demonstrates the engine + jurisdiction-pack design (docs/strategy/knowledge-architecture.md):
a parcel's "regulatory route" = Federal core (always) + Canton overlay (selectable) + Commune
overlay (selectable). Only the active layers are consulted; communes are pluggable. Adding a
country = adding a federal/canton/commune layer set — the selector logic is unchanged.

Run:  python pilot/selector.py
"""
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


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_communes():
    """Discover ingested commune rulesets: pilot/<slug>/rpga_zones.json."""
    out = {}
    for p in sorted(glob.glob(os.path.join(HERE, "*", "rpga_zones.json"))):
        d = _load(p)
        out[d.get("commune") or os.path.basename(os.path.dirname(p))] = p
    return out


def federal_layer():
    p = os.path.join(REG, "federal.json")
    return _load(p) if os.path.exists(p) else None


def canton_layer(canton):
    p = os.path.join(REG, f"canton_{(canton or '').lower()}.json")
    return _load(p) if os.path.exists(p) else None


def load_commune(commune):
    slug = (commune or "").strip().lower()
    p = os.path.join(HERE, slug, "rpga_zones.json")
    return _load(p) if os.path.exists(p) else None


def route(country="CH", canton="VD", commune="Lausanne"):
    """Compose the regulatory route: only Federal + the chosen canton + the chosen commune are active."""
    fed, can, com = federal_layer(), canton_layer(canton), load_commune(commune)
    active = []
    if fed:
        active.append(f"{country}/federal  — {len(fed['units'])} actes (LAT, OPB, LHand, AEAI…)")
    if can:
        active.append(f"{canton}/cantonal — {len(can['units'])} actes (LATC, RLATC, LRou…)")
    if com:
        active.append(f"{commune}/communal — {len(com['zones'])} zones ({com['document']['title'][:32]}…)")
    return {"country": country, "canton": canton, "commune": commune,
            "active": active, "federal": fed, "canton_layer": can, "commune_layer": com}


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
