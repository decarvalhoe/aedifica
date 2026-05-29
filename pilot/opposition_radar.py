#!/usr/bin/env python3
"""MVP2 — Opposition / recours-risk radar (issue #26).

INDICATIVE, heuristic scoring of the likelihood and grounds of neighbour opposition for a VD parcel,
*before* the mise à l'enquête. Combines (all sourced / computed, never fabricated):
  - OEREB constraints      : zone, noise DS, alignments, protected-site flags (live)
  - communal zone rules    : order (contigu), heights, setbacks (ingested RPGA)
  - neighbour proximity    : distinct parcels within ~40 m (live swisstopo identify)
  - shadow reach           : worst-case winter-solstice shadow from the zone-max or given height (computed)

NOT legal advice — opposition outcome depends on the actual project design and a jurist's reading.
This flags the levers most likely to trigger opposition and the typical legal grounds + mitigations.

Usage:  python pilot/opposition_radar.py ["address or EGRID"] [hypothetical_height_m]
"""
import json
import math
import os
import sys
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oereb            # noqa: E402
import mvp1_demo as demo  # noqa: E402  (reuse geocode/identify/area/zone matching)

_LEVEL = {"faible": 1, "modéré": 2, "élevé": 3}
_ICON = {"faible": "·", "modéré": "▲", "élevé": "■"}


def neighbours(e, n, half=40):
    """Distinct neighbouring parcels (EGRIDs) within a ~half-metre envelope, excluding self."""
    ext = f"{e-half},{n-half},{e+half},{n+half}"
    q = urllib.parse.urlencode({
        "geometry": ext, "geometryType": "esriGeometryEnvelope", "sr": "2056",
        "layers": f"all:{demo.CADASTRE_LAYER}", "tolerance": "0",
        "mapExtent": ext, "imageDisplay": "500,500,96", "returnGeometry": "false",
    })
    try:
        data = json.loads(demo.get(f"{demo.GEOADMIN}/all/MapServer/identify?{q}"))
        egr = {r.get("attributes", {}).get("egris_egrid") for r in data.get("results", [])}
        egr.discard(None)
        return egr
    except Exception:
        return set()


def winter_shadow_len(height_m, lat=46.52):
    """Shadow length (m) at winter-solstice solar noon — worst case for overshadowing."""
    altitude_deg = max(5.0, 90 - lat - 23.44)  # ~20° at Lausanne's latitude
    return height_m / math.tan(math.radians(altitude_deg))


def resolve(query):
    """query (address or EGRID) -> (oereb_record, E, N, area_from_geometry)."""
    egrid = query if (query[:2] == "CH" and query[2:].isdigit()) else None
    e = n = area = None
    if not egrid:
        g = demo.geocode(query)
        if not g:
            raise SystemExit(f"Adresse introuvable: {query}")
        e, n, _ = g
        p = demo.identify_parcel(e, n)
        if p:
            egrid, area = p["egrid"], demo.polygon_area_m2(p.get("rings"))
    return oereb.get(egrid), e, n, area


def score(o, e, n, area, project_height_m=None):
    commune, zone_label = o.get("commune"), (o.get("zone") or "")
    rpga = demo.load_rpga(commune)
    zname, zp, _ = demo.match_zone(rpga, {"zone": zone_label, "parcel": o.get("parcel")})
    zp = zp or {}
    nb = neighbours(e, n) if e else set()

    grounds = []

    def add(ground, level, basis, mitigation):
        grounds.append({"ground": ground, "level": level, "basis": basis, "mitigation": mitigation})

    zl = zone_label.lower()
    themes = " ".join(t or "" for t in o.get("concerned_themes", [])).lower()
    if "centr" in zl or "histor" in zl or "isos" in themes or "site construit" in themes:
        add("Patrimoine / intégration", "élevé",
            "Centre historique / site protégé — gabarit, matériaux et intégration très scrutés",
            "Étude d'intégration soignée; concertation préalable; calage sur le gabarit du bâti contigu")

    ds = o.get("noise_ds") or ""
    if ds and "III" not in ds and "IV" not in ds:
        add("Bruit (degré de sensibilité)", "modéré",
            f"{ds} — zone calme protégée; installations/usages bruyants contestables",
            "Limiter les sources de bruit; étude acoustique SIA 181; horaires d'exploitation")

    if o.get("alignments"):
        add("Alignements / limites des constructions", "modéré",
            "; ".join(o["alignments"])[:110],
            "Respecter strictement la limite des constructions; faire confirmer par le service")

    nb_count = len(nb)
    if nb_count >= 8:
        add("Densité de voisinage", "élevé",
            f"{nb_count} parcelles voisines (≤40 m) — nombreux opposants potentiels",
            "Information/consultation des voisins en amont de l'enquête")
    elif nb_count >= 3:
        add("Voisinage", "modéré", f"{nb_count} parcelles voisines (≤40 m)",
            "Anticiper vues, ombres et distances vis-à-vis des voisins directs")

    h = project_height_m or zp.get("height_faite_m") or zp.get("height_corniche_m")
    if h:
        shadow = winter_shadow_len(h)
        setback = zp.get("setback_min_m")
        ref = max(setback, 6) if setback is not None else 6
        if shadow > ref:
            add("Ombres portées / ensoleillement", "élevé",
                f"Hauteur ~{h:g} m → ombre hivernale ~{shadow:.0f} m (> recul {ref:g} m) sur le voisinage nord",
                "Réduire la hauteur/retrait côté nord; joindre une étude d'ombres portées")
        else:
            add("Ombres portées", "faible", f"Hauteur ~{h:g} m → ombre hivernale ~{shadow:.0f} m",
                "Joindre une étude d'ombres portées au dossier")

    other = (zp.get("other") or "").lower()
    if "contigu" in other and "non contigu" not in other:
        add("Mitoyenneté / jours et vues", "modéré",
            "Ordre contigu — murs mitoyens, jours et vues droites (art. 684 CC + droit cantonal)",
            "Accord de voisinage sur jours/vues; respect des distances de vues droites")

    total = sum(_LEVEL[g["level"]] for g in grounds)
    overall = "élevé" if total >= 6 else "modéré" if total >= 3 else "faible"
    return {"parcel": o.get("parcel"), "egrid": o.get("egrid"), "commune": commune, "zone": zone_label,
            "area": o.get("area_m2") or area, "neighbours": nb_count, "zone_rpga": zname,
            "height_used": h, "grounds": grounds, "score": total, "overall": overall}


def assess(query, project_height_m=None):
    o, e, n, area = resolve(query)
    return score(o, e, n, area, project_height_m)


def render(r):
    print("=" * 72)
    print("AEDIFICA — Radar de risque d'opposition / recours (MVP2, indicatif)")
    print("=" * 72)
    print(f"[api] Parcelle {r['parcel']} ({r['egrid']}) — {r['commune']}")
    print(f"[api] Zone        : {r['zone'] or '—'}" + (f"  → {r['zone_rpga']}" if r['zone_rpga'] else ""))
    print(f"[api] Surface     : {r['area'] or '—'} m²   Voisins ≤40 m: {r['neighbours']}")
    if r["height_used"]:
        print(f"[hyp] Hauteur considérée: {r['height_used']:g} m")
    print("-" * 72)
    print(f"RISQUE GLOBAL : {r['overall'].upper()}  (score {r['score']})")
    print("-" * 72)
    if not r["grounds"]:
        print("  Aucun facteur de risque saillant détecté à ce stade.")
    for g in sorted(r["grounds"], key=lambda x: -_LEVEL[x["level"]]):
        print(f"  {_ICON[g['level']]} [{g['level'].upper():7}] {g['ground']}")
        print(f"        motif    : {g['basis']}")
        print(f"        mitigation: {g['mitigation']}")
    print("-" * 72)
    print("Indicatif — fondé sur parcelle/zone/voisinage; le résultat réel dépend du projet et d'un")
    print("examen juridique. Préparation sourcée, jamais une autorité (cf. contrat de preuve).")
    print("=" * 72)


def main():
    args = sys.argv[1:]
    height = None
    if args and re_isnum(args[-1]):
        height = float(args[-1]); args = args[:-1]
    query = " ".join(args).strip() or demo.DEMO_ADDR
    render(assess(query, height))
    return 0


def re_isnum(s):
    try:
        float(s); return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
