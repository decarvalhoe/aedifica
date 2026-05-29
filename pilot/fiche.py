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
import mvp1_demo as demo  # noqa: E402
import opposition_radar as radar  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
_RISK_COLOR = {"élevé": "#b60205", "modéré": "#d9822b", "faible": "#1f6f6b"}


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
    rpga = demo.load_rpga(o.get("commune"))
    zname, zp, how = demo.match_zone(rpga, {"zone": o.get("zone"), "parcel": o.get("parcel")})
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
        f'<div class="ground"><div class="gl" style="background:{_RISK_COLOR[g["level"]]}">{esc(g["level"]).upper()}</div>'
        f'<div class="gb"><b>{esc(g["ground"])}</b><br><span class="mut">{esc(g["basis"])}</span>'
        f'<br><span class="mit">→ {esc(g["mitigation"])}</span></div></div>'
        for g in sorted(rad["grounds"], key=lambda x: -{"faible": 1, "modéré": 2, "élevé": 3}[x["level"]])
    ) or '<div class="mut">Aucun facteur saillant détecté.</div>'

    rc = _RISK_COLOR[rad["overall"]]
    zone_line = esc(d["zname"]) + (f' &nbsp;<span class="mut">(art. {esc(prov.get("article"))} · conf. {esc(prov.get("confidence"))})</span>' if d["zname"] else "")
    if d["zname"] and d["how"] == "keyword":
        zone_line += ' <span class="warn">(appariement approximatif)</span>'
    html_doc = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>Aedifica — Fiche parcelle {esc(o.get('parcel'))} ({esc(o.get('commune'))})</title>
<style>
 :root{{--ink:#16202b;--mut:#6b7886;--line:#e2e6ea;--api:#1f6f6b;--rpga:#b5673f;--calc:#2f6f8f}}
 *{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--ink);margin:0;background:#eceef1;font-size:12px}}
 .pg{{width:210mm;min-height:297mm;margin:10px auto;background:#fff;padding:14mm;box-shadow:0 2px 16px rgba(0,0,0,.12)}}
 h1{{font-size:20px;margin:0}} h1 b{{color:var(--rpga)}} .kick{{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--mut);margin:0 0 3px}}
 header{{border-bottom:2px solid var(--ink);padding-bottom:8px;display:flex;justify-content:space-between;align-items:flex-end}}
 header .r{{text-align:right;color:var(--mut);font-size:10px;line-height:1.5}}
 .lab{{font-size:9px;letter-spacing:1.5px;text-transform:uppercase;color:var(--api);font-weight:700;margin:14px 0 6px}}
 table{{width:100%;border-collapse:collapse}} td{{padding:3px 4px;border-bottom:1px solid var(--line);vertical-align:top}}
 td:first-child{{color:var(--mut);width:38%}} small{{color:var(--mut)}}
 .tag{{font-size:7.5px;font-weight:700;padding:1px 5px;border-radius:8px;margin-left:6px;color:#fff;vertical-align:middle}}
 .tag.api,.tag.API{{background:var(--api)}} .tag.RPGA{{background:var(--rpga)}} .tag.calc{{background:var(--calc)}}
 .chip{{display:inline-block;font-size:9px;background:#eef1f4;border:1px solid var(--line);border-radius:9px;padding:1px 7px;margin:2px 3px 0 0}}
 .chip.more{{background:var(--ink);color:#fff}} .warn{{color:var(--rpga);font-weight:700}}
 .badge{{display:inline-block;color:#fff;font-weight:800;padding:4px 12px;border-radius:5px;font-size:13px}}
 .ground{{display:flex;gap:9px;margin:6px 0;border:1px solid var(--line);border-radius:5px;padding:7px 8px}}
 .gl{{color:#fff;font-size:8px;font-weight:800;border-radius:3px;padding:3px 6px;height:fit-content;white-space:nowrap}}
 .mut{{color:var(--mut)}} .mit{{color:var(--calc)}}
 .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
 footer{{margin-top:16px;border-top:1px solid var(--line);padding-top:8px;color:var(--mut);font-size:9px}}
 @media print{{body{{background:#fff}}.pg{{box-shadow:none;margin:0;width:auto;min-height:auto;padding:0}}@page{{size:A4;margin:12mm}}}}
</style></head><body><div class="pg">
 <header><div><p class="kick">ArchiOS Suisse · Préparation sourcée</p>
   <h1>AEDIFICA — <b>Fiche parcelle</b></h1></div>
   <div class="r">{esc(o.get('commune'))} · parcelle {esc(o.get('parcel'))}<br>EGRID {esc(o.get('egrid'))}<br>{today}</div></header>

 <div class="grid">
  <div><p class="lab">Contraintes (sources officielles)<span class="tag api">api</span></p>
   <table>
    <tr><td>Surface (registre foncier)</td><td><b>{fmt(d['area'])} m²</b></td></tr>
    <tr><td>Zone d'affectation</td><td><b>{esc(o.get('zone'))}</b></td></tr>
    <tr><td>Sensibilité au bruit</td><td>{esc(o.get('noise_ds'))}</td></tr>
    <tr><td>Alignements</td><td>{esc('; '.join(o.get('alignments') or []))}</td></tr>
    <tr><td>Plans légalisés</td><td>{len(o.get('plans') or [])} document(s)</td></tr>
   </table>
   <p class="lab">Lois applicables</p>{_chips([l['number'] for l in o.get('laws', [])], kind='law')}
   <p class="lab">Non concerné par</p>{_chips(o.get('not_concerned', []), limit=6, kind='law')}
  </div>
  <div><p class="lab">Enveloppe constructible (règlement communal)<span class="tag RPGA">RPGA</span></p>
   <table><tr><td>Zone (règlement)</td><td><b>{zone_line}</b></td></tr>{env}</table>
   <p class="lab" style="color:{rc}">Radar d'opposition / recours</p>
   <p>Risque global : <span class="badge" style="background:{rc}">{esc(rad['overall']).upper()}</span>
      <span class="mut">&nbsp;score {rad['score']} · {rad['neighbours']} voisins ≤40 m</span></p>
   {grounds}
  </div>
 </div>

 <footer><b>Préparation sourcée, jamais une autorité — l'architecte décide.</b>
  Contraintes via swisstopo + cadastre RDPPF VD (live) ; enveloppe via le règlement communal ingéré
  ({esc((zp.get('provenance') or {}).get('url',''))[:70]}…) ; radar indicatif (heuristique).
  Aedifica · pilote Lausanne/VD · {today}.</footer>
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
