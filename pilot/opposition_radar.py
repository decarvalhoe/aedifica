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
import domain           # noqa: E402
import datum_html       # noqa: E402
import mvp1_demo as demo  # noqa: E402  (reuse geocode/identify/area/zone matching)
import trust            # noqa: E402

_LEVEL = {"faible": 1, "modéré": 2, "élevé": 3}
_ICON = {"faible": "·", "modéré": "▲", "élevé": "■"}

# Structured evidence category per signal (heritage / noise / neighbor / shadow / visibility).
SIGNAL_EVIDENCE_CATEGORY = {
    "OPP-HERITAGE": "heritage",
    "OPP-NOISE": "noise",
    "OPP-ALIGNMENTS": "alignment",
    "OPP-NEIGHBOURS": "neighbor",
    "OPP-NEIGHBOURS-DENSE": "neighbor",
    "OPP-NEIGHBOURS-UNKNOWN": "neighbor",
    "OPP-SHADOW": "shadow",
    "OPP-SHADOW-UNKNOWN": "shadow",
    "OPP-MITOYENNETE": "visibility",
}
EVIDENCE_CATEGORIES = {"heritage", "noise", "neighbor", "shadow", "visibility", "alignment", "other"}
NON_PREDICTION_DISCLAIMER = (
    "Indicatif: fondé sur parcelle, zone et voisinage. Ce n'est pas une prédiction de la "
    "décision de l'autorité ni un avis juridique."
)


def _source_ref(source_id, locator, confidence="medium", valid_as_of="live"):
    return {
        "source_id": source_id,
        "locator": locator,
        "valid_as_of": valid_as_of,
        "confidence": confidence,
    }


def _signal(signal_id, ground, level, basis, mitigation, evidence_state, source_refs=None, confidence="medium", affected=None, required_check=None):
    missing_evidence = [required_check] if (evidence_state in {"unknown", "assumption"} and required_check) else []
    return {
        "signal_id": signal_id,
        "ground": ground,
        "level": level,
        "basis": basis,
        "mitigation": mitigation,
        "evidence_state": evidence_state,
        "evidence_category": SIGNAL_EVIDENCE_CATEGORY.get(signal_id, "other"),
        "confidence": confidence,
        "affected": affected or {},
        "source_refs": source_refs or [],
        "required_check": required_check,
        "missing_evidence": missing_evidence,
        "claims_prediction": False,
    }


def evidence_model(score_result):
    """Structured opposition evidence model: categories, missing evidence, no prediction."""
    signals = score_result.get("signals", [])
    by_category = {}
    for signal in signals:
        by_category.setdefault(signal.get("evidence_category", "other"), []).append(signal["signal_id"])
    return {
        "claims_prediction": False,
        "disclaimer": NON_PREDICTION_DISCLAIMER,
        "categories": sorted(by_category),
        "signals_by_category": by_category,
        "supported_categories": sorted(set(SIGNAL_EVIDENCE_CATEGORY.values())),
        "missing_evidence": [
            {"signal_id": s["signal_id"], "category": s["evidence_category"], "missing": s["missing_evidence"]}
            for s in signals
            if s.get("missing_evidence")
        ],
    }


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
            egrid, area = p["egrid"], domain.polygon_area_m2(p.get("rings"))
    return oereb.get(egrid), e, n, area


def score(o, e, n, area, project_height_m=None):
    commune, zone_label = o.get("commune"), (o.get("zone") or "")
    rpga = domain.load_commune_ruleset(commune)
    zname, zp, _ = domain.match_communal_zone(rpga, {"zone": zone_label, "parcel": o.get("parcel")})
    zp = zp or {}
    nb = neighbours(e, n) if e else set()

    signals = []

    def add(signal_id, ground, level, basis, mitigation, evidence_state="sourced", source_refs=None, confidence="medium", required_check=None):
        signals.append(
            _signal(
                signal_id,
                ground,
                level,
                basis,
                mitigation,
                evidence_state,
                source_refs=source_refs,
                confidence=confidence,
                affected={"parcel": o.get("parcel"), "egrid": o.get("egrid"), "commune": commune, "zone": zone_label},
                required_check=required_check,
            )
        )

    oereb_ref = [_source_ref("VD-OEREB", f"EGRID {o.get('egrid')}", "high", o.get("valid_as_of", "live"))]
    rpga_ref = [_source_ref("COMMUNE-RPGA", zname or "communal zone unresolved", "medium", o.get("valid_as_of", "live"))]

    zl = zone_label.lower()
    themes = " ".join(t or "" for t in o.get("concerned_themes", [])).lower()
    if "centr" in zl or "histor" in zl or "isos" in themes or "site construit" in themes:
        add("OPP-HERITAGE", "Patrimoine / intégration", "élevé",
            "Centre historique / site protégé — gabarit, matériaux et intégration très scrutés",
            "Étude d'intégration soignée; concertation préalable; calage sur le gabarit du bâti contigu",
            source_refs=oereb_ref + rpga_ref,
            confidence="high")

    ds = o.get("noise_ds") or ""
    if ds and "III" not in ds and "IV" not in ds:
        add("OPP-NOISE", "Bruit (degré de sensibilité)", "modéré",
            f"{ds} — zone calme protégée; installations/usages bruyants contestables",
            "Limiter les sources de bruit; étude acoustique SIA 181; horaires d'exploitation",
            source_refs=oereb_ref,
            confidence="medium")

    if o.get("alignments"):
        add("OPP-ALIGNMENTS", "Alignements / limites des constructions", "modéré",
            "; ".join(o["alignments"])[:110],
            "Respecter strictement la limite des constructions; faire confirmer par le service",
            source_refs=oereb_ref,
            confidence="high")

    nb_count = len(nb)
    if not e:
        add(
            "OPP-NEIGHBOURS-UNKNOWN",
            "Voisinage",
            "modéré",
            "La géométrie précise des parcelles voisines n'est pas disponible dans ce contexte offline.",
            "Lancer l'identification géographique ou joindre un plan de voisinage avant mise à l'enquête.",
            evidence_state="unknown",
            source_refs=[],
            confidence="low",
            required_check="Identifier les parcelles voisines dans un rayon pertinent depuis la géométrie cadastrale.",
        )
    elif nb_count >= 8:
        add("OPP-NEIGHBOURS-DENSE", "Densité de voisinage", "élevé",
            f"{nb_count} parcelles voisines (≤40 m) — nombreux opposants potentiels",
            "Information/consultation des voisins en amont de l'enquête",
            evidence_state="computed",
            source_refs=[_source_ref("SWISSTOPO-CADASTRE", "identify around parcel", "medium")],
            confidence="medium")
    elif nb_count >= 3:
        add("OPP-NEIGHBOURS", "Voisinage", "modéré", f"{nb_count} parcelles voisines (≤40 m)",
            "Anticiper vues, ombres et distances vis-à-vis des voisins directs",
            evidence_state="computed",
            source_refs=[_source_ref("SWISSTOPO-CADASTRE", "identify around parcel", "medium")],
            confidence="medium")

    h = project_height_m or zp.get("height_faite_m") or zp.get("height_corniche_m")
    if h:
        shadow = winter_shadow_len(h)
        setback = zp.get("setback_min_m")
        ref = max(setback, 6) if setback is not None else 6
        if shadow > ref:
            add("OPP-SHADOW", "Ombres portées / ensoleillement", "élevé",
                f"Hauteur ~{h:g} m → ombre hivernale ~{shadow:.0f} m (> recul {ref:g} m) sur le voisinage nord",
                "Réduire la hauteur/retrait côté nord; joindre une étude d'ombres portées",
                evidence_state="computed",
                source_refs=rpga_ref + [_source_ref("AEDIFICA-CALC", "winter solstice shadow heuristic", "medium")],
                confidence="medium",
                required_check="Verifier l'ombre avec la volumetrie reelle et la topographie.")
        else:
            add("OPP-SHADOW", "Ombres portées", "faible", f"Hauteur ~{h:g} m → ombre hivernale ~{shadow:.0f} m",
                "Joindre une étude d'ombres portées au dossier",
                evidence_state="computed",
                source_refs=rpga_ref + [_source_ref("AEDIFICA-CALC", "winter solstice shadow heuristic", "medium")],
                confidence="medium",
                required_check="Verifier l'ombre avec la volumetrie reelle et la topographie.")
    else:
        add(
            "OPP-SHADOW-UNKNOWN",
            "Ombres portées / ensoleillement",
            "modéré",
            "Aucune hauteur de projet ou hauteur réglementaire numérique n'est disponible.",
            "Conserver le risque comme inconnu jusqu'à la volumétrie ou une règle de hauteur vérifiée.",
            evidence_state="unknown",
            confidence="low",
            required_check="Fournir une hauteur de projet ou une règle communale vérifiée pour calculer l'ombre.",
        )

    other = (zp.get("other") or "").lower()
    if "contigu" in other and "non contigu" not in other:
        add("OPP-MITOYENNETE", "Mitoyenneté / jours et vues", "modéré",
            "Ordre contigu — murs mitoyens, jours et vues droites (art. 684 CC + droit cantonal)",
            "Accord de voisinage sur jours/vues; respect des distances de vues droites",
            source_refs=rpga_ref,
            confidence="medium",
            required_check="Verifier jours, vues et mitoyennete sur le projet reel.")

    grounds = [
        {"ground": s["ground"], "level": s["level"], "basis": s["basis"], "mitigation": s["mitigation"]}
        for s in signals
    ]
    total = sum(_LEVEL[g["level"]] for g in grounds)
    overall = "élevé" if total >= 6 else "modéré" if total >= 3 else "faible"
    return {"parcel": o.get("parcel"), "egrid": o.get("egrid"), "commune": commune, "zone": zone_label,
            "area": o.get("area_m2") or area, "neighbours": nb_count, "zone_rpga": zname,
            "height_used": h, "grounds": grounds, "signals": signals, "score": total, "overall": overall,
            "required_checks": [s["required_check"] for s in signals if s.get("required_check")]}


def report(r):
    return {
        "report_id": f"OPPOSITION-{r.get('egrid') or r.get('parcel')}",
        "parcel": {"parcel": r.get("parcel"), "egrid": r.get("egrid"), "commune": r.get("commune"), "zone": r.get("zone")},
        "summary": {"overall": r.get("overall"), "score": r.get("score"), "signal_count": len(r.get("signals", []))},
        "signals": r.get("signals", []),
        "evidence_model": evidence_model(r),
        "claims_prediction": False,
        "disclaimer": NON_PREDICTION_DISCLAIMER,
        "required_checks": r.get("required_checks", []),
        "trust_footer": trust.render_footer("fr"),
    }


def render_report_html(report_obj):
    import html

    def esc(value):
        return html.escape("" if value is None else str(value))

    rows = "".join(
        f"<li class='{esc(signal.get('evidence_state'))}'><b>{esc(signal.get('level'))}</b> "
        f"{esc(signal.get('ground'))}<br><small>{esc(signal.get('basis'))}</small>"
        f"<br><small>confiance: {esc(signal.get('confidence'))} · état: {esc(signal.get('evidence_state'))}</small></li>"
        for signal in report_obj.get("signals", [])
    )
    checks = "".join(f"<li>{esc(check)}</li>" for check in report_obj.get("required_checks", []))
    body = f"""
  <h1>Rapport indicatif opposition / recours</h1>
  <p><span class="chip {esc(report_obj['summary']['overall'])}">Risque global</span> {esc(report_obj['summary']['overall'])} ({esc(report_obj['summary']['score'])})</p>
  <section><h2>Signaux</h2><ul>{rows}</ul></section>
  <section><h2>Contrôles requis</h2><ul>{checks}</ul></section>
"""
    return datum_html.shell(esc(report_obj["report_id"]), "Opposition / recours", body, esc(report_obj.get("trust_footer")))


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
    if not r["signals"]:
        print("  Aucun facteur de risque saillant détecté à ce stade.")
    for s in sorted(r["signals"], key=lambda x: -_LEVEL[x["level"]]):
        print(f"  {_ICON[s['level']]} [{s['level'].upper():7}] {s['ground']} ({s['evidence_state']}, confiance {s['confidence']})")
        print(f"        motif    : {s['basis']}")
        print(f"        mitigation: {s['mitigation']}")
        if s.get("required_check"):
            print(f"        vérif.   : {s['required_check']}")
    print("-" * 72)
    print("Indicatif — fondé sur parcelle/zone/voisinage; le résultat réel dépend du projet et d'un")
    print("examen juridique.")
    trust.print_footer("fr")
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
