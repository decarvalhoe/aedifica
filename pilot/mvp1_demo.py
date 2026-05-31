#!/usr/bin/env python3
"""Aedifica — MVP1 end-to-end demo.

Parcel (Ville de Lausanne) -> sourced constraints + buildable envelope.

Pipeline (validated, see docs/strategy/poc-lausanne-parcel.md):
  1. address -> LV95 coords        (swisstopo SearchServer)
  2. coords  -> EGRID + geometry   (swisstopo identify, cadastral layer)  -> parcel area (shoelace)
  3. EGRID   -> binding constraints (VD OEREB extract: zone, DS noise, alignments, laws)
  4. zone    -> building params     (Lausanne RPGA ruleset, ingested -> pilot/lausanne/rpga_zones.json)
  5. compute -> buildable envelope  (area x IUS/IBUS/IOS, heights, levels), every line with provenance

Stdlib only. Honest by design: each output line is tagged
  [api] sourced from a public API   [RPGA] sourced from the communal règlement (document)
  [calc] computed from sourced inputs   [assumption]   [unknown]
The system is a preparation/evidence tool, never an authority (trust contract, see the spec).

Usage:  python pilot/mvp1_demo.py ["address or EGRID"]
Default: Place de la Palud, Lausanne (demo parcel 10072 / EGRID CH915772367853).
"""
import json, math, os, re, ssl, sys, textwrap, urllib.parse, urllib.request

try:  # show accents/m² correctly on Windows consoles
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import domain  # noqa: E402
import oereb  # noqa: E402  (local module in pilot/)
import trust  # noqa: E402

GEOADMIN = "https://api3.geo.admin.ch/rest/services"
VD_OEREB = "https://www.rdppf.vd.ch/ws/RdppfSVC.svc"
CADASTRE_LAYER = "ch.kantone.cadastralwebmap-farbe"
HEADERS = {"User-Agent": "Aedifica-MVP1-demo/0.1 (pilot; +https://github.com/decarvalhoe/aedifica)"}
CTX = ssl.create_default_context()
HERE = os.path.dirname(os.path.abspath(__file__))
RPGA_PATH = os.path.join(HERE, "lausanne", "rpga_zones.json")

DEMO_EGRID = "CH915772367853"
DEMO_ADDR = "Place de la Palud 1 Lausanne"

# Constraints verified live in the PoC for the demo parcel (fallback if OEREB parsing changes).
POC_CACHE = {
    DEMO_EGRID: {
        "zone": "Zone centrale (15 LAT)",
        "ds": "Degré de sensibilité III",
        "alignments": ["Limite des constructions définie par un plan approuvé"],
        "laws": ["LATC (RSV 700.11)", "LAT (fedlex RS 700)"],
        "not_concerned": ["sites pollués", "zones de protection des eaux", "distances à la forêt"],
        "_source": "VD OEREB extract, verified 2026-05-29 (PoC)",
    }
}


def get(url, timeout=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=timeout, context=CTX) as r:
        return r.read()


def geocode(text):
    """Address -> (E, N) in LV95 (EPSG:2056). geoadmin attrs: x=North, y=East."""
    q = urllib.parse.urlencode({"searchText": text, "type": "locations", "sr": "2056", "limit": "1"})
    data = json.loads(get(f"{GEOADMIN}/api/SearchServer?{q}"))
    res = data.get("results") or []
    if not res:
        return None
    a = res[0]["attrs"]
    return float(a["y"]), float(a["x"]), a.get("label", "").replace("<b>", "").replace("</b>", "")


def identify_parcel(e, n):
    """(E,N) -> {egrid, number, rings} via the cadastral layer."""
    ext = f"{e-60},{n-60},{e+60},{n+60}"
    q = urllib.parse.urlencode({
        "geometry": f"{e},{n}", "geometryType": "esriGeometryPoint", "sr": "2056",
        "layers": f"all:{CADASTRE_LAYER}", "tolerance": "1",
        "mapExtent": ext, "imageDisplay": "100,100,96", "returnGeometry": "true",
    })
    data = json.loads(get(f"{GEOADMIN}/all/MapServer/identify?{q}"))
    for r in data.get("results", []):
        attrs = r.get("attributes", {})
        egrid = attrs.get("egris_egrid") or attrs.get("egrid")
        if egrid:
            geom = r.get("geometry", {})
            return {"egrid": egrid, "number": attrs.get("number"), "rings": geom.get("rings")}
    return None


def polygon_area_m2(rings):
    """Shoelace area (m²) of the outer ring; coords already in metres (LV95)."""
    return domain.polygon_area_m2(rings)


def _walk_strings(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)
    elif isinstance(obj, str):
        yield obj


def fetch_constraints(egrid):
    """EGRID -> binding constraints via the robust OEREB parser (works for any VD parcel).
    Falls back to verified PoC values only if the live service is unreachable."""
    try:
        o = oereb.get(egrid)
        return {
            "_source": f"VD OEREB extract (live, {o['_bytes']} o)",
            "commune": o.get("commune"),
            "zone": o.get("zone"),
            "ds": o.get("noise_ds"),
            "alignments": o.get("alignments") or [],
            "laws": [f"{law['title']} ({law['number']})" for law in o.get("laws", [])],
            "not_concerned": o.get("not_concerned") or [],
            "area_official": o.get("area_m2"),
            "parcel": o.get("parcel"),
            "plans": o.get("plans") or [],
        }
    except Exception as ex:
        c = dict(POC_CACHE.get(egrid, {}))
        c["_source"] = f"PoC fallback (live indisponible: {type(ex).__name__})"
        return c


def load_rpga(commune):
    """Load the ingested ruleset for a commune (pilot/<slug>/rpga_zones.json)."""
    return domain.load_commune_ruleset(commune)


def match_zone(rpga, constraints):
    """Map the OEREB harmonized zone designation to a communal zone entry.
    Returns (zone_name, params, how) where how in {demo, exact, keyword}."""
    return domain.match_communal_zone(rpga, constraints)


def tag(provenance):
    return {"api": "[api]", "rpga": "[RPGA]", "calc": "[calc]", "assumption": "[assumption]", "unknown": "[unknown]"}[provenance]


def fmt(value, unit=""):
    return f"{value:g}{unit}" if isinstance(value, (int, float)) else "—"


def main():
    arg = " ".join(sys.argv[1:]).strip()
    egrid_in = arg if re.fullmatch(r"CH\d{12}", arg or "") else None
    address = None if egrid_in else (arg or DEMO_ADDR)

    print("=" * 72)
    print("AEDIFICA — Fiche parcelle & enveloppe (MVP1, pilote Lausanne/VD)")
    print("=" * 72)

    egrid, number, area = egrid_in, None, None
    if address:
        try:
            g = geocode(address)
            if not g:
                print(f"[unknown] Adresse introuvable: {address}"); return 1
            e, n, label = g
            print(f"[api] Adresse        : {label}")
            print(f"[api] Coordonnées    : E={e:.1f} N={n:.1f} (LV95)")
            p = identify_parcel(e, n)
            if p:
                egrid, number = p["egrid"], p["number"]
                area = polygon_area_m2(p["rings"])
        except Exception as ex:
            print(f"[unknown] swisstopo indisponible ({type(ex).__name__}); bascule sur la parcelle de démo.")
            egrid = DEMO_EGRID
    egrid = egrid or DEMO_EGRID
    c = fetch_constraints(egrid)
    if c.get("area_official"):
        area = float(c["area_official"])

    print(f"[api] Parcelle nº     : {number or c.get('parcel') or '—'}")
    print(f"[api] EGRID          : {egrid}")
    src_area = "registre foncier" if c.get("area_official") else "calculée"
    print(f"[api] Surface parcelle: {fmt(area,' m²') if area else '—'} ({src_area})")

    print("-" * 72)
    print("CONTRAINTES (sources officielles)")
    print(f"      · source       : {c.get('_source','—')}")
    print(f"[api] Zone affectation: {c.get('zone') or '—'}")
    print(f"[api] Sensibilité bruit: {c.get('ds') or '—'}")
    print(f"[api] Alignements     : {', '.join(c.get('alignments') or []) or '—'}")
    print(f"[api] Lois applicables: {', '.join(c.get('laws') or []) or '—'}")
    nc = c.get("not_concerned") or []
    if nc:
        print(f"[api] Non concerné par : {', '.join(nc[:4])}" + (f" … (+{len(nc)-4})" if len(nc) > 4 else ""))
    if c.get("plans"):
        print(f"[api] Plans légalisés : {len(c['plans'])} document(s) liés")

    print("-" * 72)
    print("ENVELOPPE CONSTRUCTIBLE (règlement communal + calcul)")
    rpga = load_rpga(c.get("commune"))
    zname, zp, how = match_zone(rpga, c)
    if not rpga:
        print(f"[unknown] Ruleset communal non ingéré pour « {c.get('commune','?')} » (couche commune à ajouter).")
    elif not zp:
        print(f"[unknown] Zone communale non appariée pour « {c.get('zone','?')} » ({c.get('commune','?')}).")
    else:
        prov = zp.get("provenance") or {}
        print(f"      · zone RPGA    : {zname}  [{c.get('commune','?')}]")
        print(f"      · source       : {prov.get('article','?')} — confiance {prov.get('confidence','?')}")
        if how == "keyword":
            print("      · note         : appariement type OEREB → zone communale APPROXIMATIF (à confirmer sur le plan)")
        ibus, ius, ios = zp.get("ibus"), zp.get("ius"), zp.get("ios")
        idx = ibus if ibus is not None else ius
        idx_name = "IBUS" if ibus is not None else "IUS"
        if idx is not None:
            print(f"[RPGA] {idx_name:14}: {idx:g}")
            if area:
                print(f"[calc] SBP max       : {area*idx:,.0f} m²  (= {area:,.0f} m² × {idx_name} {idx:g})".replace(",", "'"))
        else:
            print("[RPGA] Indice IUS/IBUS : non fixé — densité régie géométriquement (gabarit)")
        if ios is not None:
            print(f"[RPGA] IOS            : {ios:g}")
            if area:
                print(f"[calc] Emprise sol max: {area*ios:,.0f} m²".replace(",", "'"))
        hc, hf = zp.get("height_corniche_m"), zp.get("height_faite_m")
        if hc is not None:
            print(f"[RPGA] Hauteur corniche: {hc:g} m")
        if hf is not None:
            print(f"[RPGA] Hauteur faîte  : {hf:g} m")
        if hc is None and hf is None:
            print("[RPGA] Hauteur        : non fixée numériquement (gabarit / contiguïté — voir règles)")
        if zp.get("levels_max") is not None:
            print(f"[RPGA] Niveaux max     : {zp.get('levels_max'):g}")
        if zp.get("setback_min_m") is not None:
            print(f"[RPGA] Distance limites: {zp.get('setback_min_m'):g} m (min.)")
        if zp.get("other"):
            print("[RPGA] Gabarit / règles:")
            for line in textwrap.wrap(zp["other"], 66):
                print(f"         {line}")

    print("-" * 72)
    print("INCONNUES / DÉCISIONS REQUISES")
    print("      · Indices/hauteurs non exposés en open data CH -> ingestion du règlement (couche commune).")
    print("      · Servitudes (registre foncier) à vérifier manuellement (accès restreint).")
    for line in trust.render_footer("fr").splitlines():
        print(f"      · {line}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
