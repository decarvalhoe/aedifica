#!/usr/bin/env python3
"""HTML fiche generator (piste 4) — one printable A4 sheet per parcel.

Combines, all provenance-tagged: the sourced constraints (OEREB), the buildable envelope (commune RPGA),
and the opposition-risk radar (MVP2). Output: pilot/out/fiche_<parcel>.html (print to PDF to attach to the
one-pager). Honest by design — values are sourced or flagged; never an authority.

Usage:  python pilot/fiche.py ["address or EGRID"] [hypothetical_height_m]
"""
import datetime
import html
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oereb              # noqa: E402
import domain             # noqa: E402
import mvp1_demo as demo  # noqa: E402
import opposition_radar as radar  # noqa: E402
import trust              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
_RISK_COLOR = {"élevé": "var(--ts-conflict)", "modéré": "var(--ts-assume)", "faible": "var(--ts-sourced)"}


def esc(x):
    return html.escape(str(x)) if x not in (None, "") else "—"


def fmt(x, unit=""):
    return f"{x:g}{unit}" if isinstance(x, (int, float)) else "—"


def collect(query, height=None):
    o, e, n, area = radar.resolve(query)
    area = o.get("area_m2") or area
    try:
        area = float(area)
    except (TypeError, ValueError):
        area = None
    rpga = domain.load_commune_ruleset(o.get("commune"))
    zname, zp, how = domain.match_communal_zone(rpga, {"zone": o.get("zone"), "parcel": o.get("parcel")})
    rad = radar.score(o, e, n, area, height)
    return {"o": o, "area": area, "zname": zname, "zp": zp or {}, "how": how, "rad": rad}


def _chips(items, limit=None, kind="law"):
    items = [i for i in items if i]
    extra = ""
    if limit and len(items) > limit:
        extra = f'<span class="chip more">+{len(items)-limit}</span>'
        items = items[:limit]
    return "".join(f'<span class="chip {kind}">{esc(i)}</span>' for i in items) + extra or "—"


def envelope_rows(zp, area, how):
    ibus, ius, ios = zp.get("ibus"), zp.get("ius"), zp.get("ios")
    idx, idx_name = (ibus, "IBUS") if ibus is not None else (ius, "IUS")
    out = []
    if idx is not None:
        out.append(("Indice", f"{idx_name} {fmt(idx)}", "RPGA"))
        if area:
            out.append(("SBP max", f"{area*idx:,.0f} m² <small>= {area:g} × {idx_name} {idx:g}</small>".replace(",", "'"), "calc"))
    elif ios is not None:
        out.append(("Indice", f"IOS {fmt(ios)} (emprise au sol)", "RPGA"))
        if area:
            out.append(("Emprise sol max", f"{area*ios:,.0f} m² <small>= {area:g} × IOS {ios:g}</small>".replace(",", "'"), "calc"))
    else:
        out.append(("Indice", "non fixé — densité géométrique (gabarit)", "RPGA"))
    hc, hf = zp.get("height_corniche_m"), zp.get("height_faite_m")
    if hc is not None:
        out.append(("Hauteur corniche", f"{fmt(hc)} m", "RPGA"))
    if hf is not None:
        out.append(("Hauteur faîte", f"{fmt(hf)} m", "RPGA"))
    if hc is None and hf is None:
        out.append(("Hauteur", "non métrique (gabarit / contiguïté)", "RPGA"))
    if zp.get("levels_max") is not None:
        out.append(("Niveaux max", fmt(zp.get("levels_max")), "RPGA"))
    if zp.get("setback_min_m") is not None:
        out.append(("Distance aux limites", f"{fmt(zp.get('setback_min_m'))} m (min.)", "RPGA"))
    return out


def render(query, height=None):
    d = collect(query, height)
    o, zp, rad = d["o"], d["zp"], d["rad"]
    today = datetime.date.today().isoformat()
    prov = zp.get("provenance") or {}

    env = "".join(
        f'<tr><td>{esc(k)}</td><td>{v}<span class="tag {t}">{t}</span></td></tr>'
        for k, v, t in envelope_rows(zp, d["area"], d["how"])
    )
    grounds = "".join(
        f'<div class="ground"><div class="gl" style="color:{_RISK_COLOR[g["level"]]}">{esc(g["level"]).upper()}</div>'
        f'<div class="gb"><b>{esc(g["ground"])}</b><br><span class="mut">{esc(g["basis"])}</span>'
        f'<br><span class="mit">→ {esc(g["mitigation"])}</span></div></div>'
        for g in sorted(rad["grounds"], key=lambda x: -{"faible": 1, "modéré": 2, "élevé": 3}[x["level"]])
    ) or '<div class="mut">Aucun facteur saillant détecté.</div>'

    rc = _RISK_COLOR[rad["overall"]]
    zone_line = esc(d["zname"]) + (f' &nbsp;<span class="mut">(art. {esc(prov.get("article"))} · conf. {esc(prov.get("confidence"))})</span>' if d["zname"] else "")
    if d["zname"] and d["how"] == "keyword":
        zone_line += ' <span class="warn">(appariement approximatif)</span>'
    trust_footer = "<br>".join(esc(line) for line in trust.render_footer("fr").splitlines())
    html_doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AEDIFICA — Fiche parcelle {esc(o.get('parcel'))} ({esc(o.get('commune'))})</title>
<link rel="icon" href="../../docs/design-system/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="../../docs/design-system/colors_and_type.css">
<link rel="stylesheet" href="../../docs/design-system/aedifica-datum-ui.css">
</head><body class="report-body"><div class="report-sheet">
 <header>
   <div class="slide__topline" style="padding-bottom:14px">
     <span>Fiche parcelle</span><span>Préparation sourcée</span><span>{esc(o.get('commune'))} · {today}</span>
   </div>
   <div style="display:flex;justify-content:space-between;gap:24px;align-items:flex-end;padding:22px 0;border-bottom:1px solid var(--ink)">
     <div>
       <span class="ds-wordmark" style="font-size:42px"><span class="ae">Æ</span>DIFICA</span>
       <span class="mini-datum" aria-hidden="true"></span>
       <h1 class="d-title" style="font-size:30px;margin-top:16px">Préparation — Parcelle {esc(o.get('parcel'))}</h1>
     </div>
     <p class="mono" style="text-align:right;color:var(--fg-3);font-size:10px;line-height:1.7">
       {esc(o.get('commune'))}<br>EGRID {esc(o.get('egrid'))}<br>DATUM +13.50
     </p>
   </div>
 </header>

 <div class="report-grid">
  <div class="report-section"><h2>Contraintes · sources officielles <span class="tag api">api</span></h2>
   <table class="dt">
    <tr><td>Surface (registre foncier)</td><td><b>{fmt(d['area'])} m²</b></td></tr>
    <tr><td>Zone d'affectation</td><td><b>{esc(o.get('zone'))}</b></td></tr>
    <tr><td>Sensibilité au bruit</td><td>{esc(o.get('noise_ds'))}</td></tr>
    <tr><td>Alignements</td><td>{esc('; '.join(o.get('alignments') or []))}</td></tr>
    <tr><td>Plans légalisés</td><td>{len(o.get('plans') or [])} document(s)</td></tr>
   </table>
   <h2>Lois applicables</h2>{_chips([l['number'] for l in o.get('laws', [])], kind='law')}
   <h2>Non concerné par</h2>{_chips(o.get('not_concerned', []), limit=6, kind='law')}
  </div>
  <div class="report-section"><h2>Enveloppe · règlement communal <span class="tag RPGA">RPGA</span></h2>
   <table class="dt"><tr><td>Zone (règlement)</td><td><b>{zone_line}</b></td></tr>{env}</table>
   <h2 style="color:{rc}">Radar d'opposition / recours</h2>
   <p>Risque global : <span class="badge" style="color:{rc}">{esc(rad['overall']).upper()}</span>
      <span class="mut">&nbsp;score {rad['score']} · {rad['neighbours']} voisins ≤40 m</span></p>
   {grounds}
  </div>
 </div>

 <footer class="a4__foot"><b>{trust_footer}</b><br>
  Contraintes via swisstopo + cadastre RDPPF VD (live) ; enveloppe via le règlement communal ingéré
  ({esc((zp.get('provenance') or {}).get('url',''))[:70]}…) ; radar indicatif (heuristique).
  AEDIFICA · pilote Lausanne/VD · {today}.</footer>
</div></body></html>"""

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"fiche_{o.get('commune','x')}_{o.get('parcel','x')}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    return path


def main():
    args = sys.argv[1:]
    height = None
    if args:
        try:
            height = float(args[-1]); args = args[:-1]
        except ValueError:
            pass
    query = " ".join(args).strip() or demo.DEMO_ADDR
    path = render(query, height)
    print(f"Fiche générée : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
