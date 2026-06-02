#!/usr/bin/env python3
"""Aedifica demo cockpit — an interactive local web app for partner presentations.

One command launches a Datum-branded, clickable cockpit:

    python pilot/demo_cockpit.py            # -> http://127.0.0.1:8090

- LIVE: type a Vaud address or EGRID and pull sourced constraints + buildable
  envelope + opposition risk in seconds (swisstopo + RDPPF/OEREB), with a frozen
  Lausanne/Pully fallback if the network is unavailable.
- WORKFLOW: permit-readiness (ACTIS-CAMAC) and the Archicad agent loop
  (dry-run -> approval -> ledger) run from fixtures.

Every value keeps its trust state (sourced / computed / unknown) and the output
is never presented as an authority decision.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import domain  # noqa: E402
import model_bridge_demo  # noqa: E402
import opposition_radar as radar  # noqa: E402
import permit_readiness  # noqa: E402
import trust  # noqa: E402
import workspace  # noqa: E402

DEMO_PROJECT = os.path.join(HERE, "projects", "demo_lausanne_palud")
PRESETS = {
    "lausanne": "Place de la Palud 2, 1003 Lausanne",
    "pully": "Avenue du Prieuré 1, 1009 Pully",
}


# --------------------------------------------------------------------------- #
# Data builders
# --------------------------------------------------------------------------- #
def _claim_view(claim: dict) -> dict:
    return {
        "title": claim.get("title"),
        "state": claim.get("state"),
        "value": claim.get("value"),
        "confidence": claim.get("confidence"),
        "sources": [ref.get("source_id") for ref in claim.get("source_refs", []) if ref.get("source_id")],
        "next_action": claim.get("next_action") or claim.get("required_human_check"),
        "formula": claim.get("formula"),
    }


def _opposition_view(risks: dict) -> dict:
    signals = []
    for signal in risks.get("signals", []):
        signals.append(
            {
                "ground": signal.get("ground"),
                "category": signal.get("evidence_category"),
                "level": signal.get("level"),
                "basis": signal.get("basis"),
                "mitigation": signal.get("mitigation"),
                "evidence_state": signal.get("evidence_state"),
                "confidence": signal.get("confidence"),
            }
        )
    return {
        "overall": risks.get("overall"),
        "score": risks.get("score"),
        "signals": signals,
        "disclaimer": radar.NON_PREDICTION_DISCLAIMER,
    }


def _frozen_lausanne(reason: str | None = None) -> dict:
    brief = workspace.generate_offline_parcel_brief(DEMO_PROJECT)
    parcel = brief["parcel"]
    return {
        "mode": "fixture",
        "reason": reason,
        "query": "Place de la Palud, Lausanne (fixture)",
        "parcel": {
            "egrid": parcel.get("egrid"),
            "number": parcel.get("number"),
            "commune": parcel.get("commune"),
            "zone": brief["constraints"][0].get("value") if brief.get("constraints") else None,
            "area_m2": parcel.get("area_m2"),
            "zone_communal": brief.get("communal_zone", {}).get("name"),
        },
        "constraints": [_claim_view(c) for c in brief.get("constraints", [])],
        "envelope": [_claim_view(c) for c in brief.get("envelope_claims", [])],
        "opposition": _opposition_view(brief.get("risks", {})),
        "sources": brief.get("source_refs", []),
        "trust_footer": brief.get("trust_footer"),
    }


def build_lookup(query: str, live: bool = True) -> dict:
    if not query:
        return _frozen_lausanne("empty query")
    try:
        if not live:
            raise RuntimeError("offline mode requested")
        oereb_record, e, n, area = radar.resolve(query)
        if not oereb_record or not oereb_record.get("egrid"):
            raise RuntimeError("no parcel resolved")
    except (Exception, SystemExit) as exc:  # network/geocode/parcel failure -> fixture
        return _frozen_lausanne(f"live lookup unavailable ({exc}); showing fixture")

    commune = oereb_record.get("commune")
    rpga = domain.load_commune_ruleset(commune)
    zone_name, zone_params, _ = domain.match_communal_zone(
        rpga, {"zone": oereb_record.get("zone"), "parcel": oereb_record.get("parcel")}
    )
    zone_params = zone_params or {}
    area_value = oereb_record.get("area_m2") or area
    envelope = domain.calculate_envelope(area_value, zone_params)
    source_ref = {
        "source_id": "VD-OEREB",
        "locator": f"EGRID {oereb_record.get('egrid')}",
        "valid_as_of": oereb_record.get("valid_as_of", "live"),
        "confidence": "high",
    }
    constraint_claims = workspace._constraint_claims(oereb_record, source_ref)
    envelope_claims = workspace._envelope_claims(envelope, [source_ref])
    try:
        risks = radar.score(oereb_record, e, n, area_value)
    except (Exception, SystemExit):
        risks = {"overall": "inconnu", "score": 0, "signals": []}

    return {
        "mode": "live",
        "reason": None,
        "query": query,
        "parcel": {
            "egrid": oereb_record.get("egrid"),
            "number": oereb_record.get("parcel"),
            "commune": commune,
            "zone": oereb_record.get("zone"),
            "area_m2": area_value,
            "zone_communal": zone_name,
        },
        "constraints": [_claim_view(c) for c in constraint_claims],
        "envelope": [_claim_view(c) for c in envelope_claims],
        "opposition": _opposition_view(risks),
        "sources": [source_ref],
        "trust_footer": trust.render_footer("fr"),
    }


def build_permit() -> dict:
    checklist = workspace._load_json(os.path.join(HERE, "permit", "vd_camac_checklist.json"))
    dossier = workspace._load_json(os.path.join(HERE, "permit", "demo_missing_dossier.json"))
    readiness = permit_readiness.build_readiness(checklist, dossier)
    return {
        "dossier_id": readiness["dossier_id"],
        "state": readiness["state"],
        "ready_for_review": readiness["ready_for_review"],
        "summary": readiness["summary"],
        "groups": [
            {
                "actor": group["actor"],
                "category": group["category"],
                "items": [
                    {
                        "title": item["title"],
                        "status": item["status"],
                        "missing_message": item.get("missing_message"),
                        "provenance": item.get("checklist_provenance", []),
                    }
                    for item in group["items"]
                ],
            }
            for group in readiness["groups"]
        ],
        "disclaimers": readiness["disclaimers"],
    }


def build_model() -> dict:
    selection = model_bridge_demo.inspect_selected_elements()
    audit = model_bridge_demo.missing_metadata_audit(selection)
    ledger_data = workspace._load_json(os.path.join(HERE, "memory", "demo_project_ledger.json"))
    blocked = model_bridge_demo.dry_run_property_update("AC-SPACE-101", "RoomUsage", "office")
    approved = model_bridge_demo.dry_run_property_update("AC-SPACE-101", "RoomUsage", "office", ledger_data)
    return {
        "fixture_mode": True,
        "model_version": selection.get("source_model_version"),
        "selected_count": len(selection.get("selected_elements", [])),
        "audit": {
            "missing_count": audit.get("missing_count"),
            "missing": [
                {
                    "element_id": item.get("element_id"),
                    "property": item.get("property") or item.get("missing_property") or item.get("field"),
                    "proposed_fix": item.get("proposed_fix"),
                }
                for item in audit.get("missing", [])[:6]
            ],
        },
        "blocked_without_approval": bool(blocked.get("blocked")),
        "allowed_with_approval": not bool(approved.get("blocked")),
        "required_approval": blocked.get("required_approval"),
    }


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #
COCKPIT_HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AEDIFICA — Cockpit démo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<style>
:root{
  --paper:#F3F1EC;--sheet:#FFFFFF;--ink:#16171A;--accent:#C0392B;--mut:#87867D;
  --line:rgba(22,23,26,.12);--line2:rgba(22,23,26,.22);
  --sourced:#1F7A44;--computed:#475569;--assume:#9A6A10;--unknown:#84847A;--conflict:#C1122C;
  --ui:"Space Grotesk","Helvetica Neue",sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--ui);line-height:1.45}
header{position:sticky;top:0;z-index:10;background:var(--paper);border-bottom:1px solid var(--ink);padding:14px 28px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:-.02em;font-size:20px}.brand .ae{color:var(--accent)}
.kicker{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--mut)}
.search{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.search input{font-family:var(--mono);font-size:13px;padding:9px 12px;border:1px solid var(--ink);background:var(--sheet);min-width:300px}
button{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:9px 12px;border:1px solid var(--ink);background:var(--ink);color:#fff;cursor:pointer}
button.ghost{background:transparent;color:var(--ink)}
button:hover{opacity:.86}
.badge{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;padding:4px 8px;border:1px solid currentColor}
.badge.live{color:var(--sourced)}.badge.fixture{color:var(--assume)}
main{width:min(1180px,calc(100vw - 40px));margin:22px auto}
.hero{display:grid;grid-template-columns:1.4fr 1fr;gap:22px;border:1px solid var(--ink);background:var(--sheet);padding:26px;margin-bottom:18px}
.hero h1{font-size:34px;font-weight:300;letter-spacing:-.025em;margin:.1em 0 .3em}
.hero p{max-width:60ch;color:#333}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.kpi{border:1px solid var(--line2);padding:12px}
.kpi b{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
.kpi .n{font-size:30px;font-weight:300}
.tabs{display:flex;gap:0;border:1px solid var(--ink);border-bottom:0;overflow:hidden}
.tab{flex:1;text-align:center;border-right:1px solid var(--ink);background:var(--sheet);color:var(--ink)}
.tab:last-child{border-right:0}
.tab.active{background:var(--ink);color:#fff}
.panelwrap{border:1px solid var(--ink);background:var(--sheet);padding:24px;min-height:340px}
.panel{display:none}.panel.active{display:block}
h2{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--mut);font-weight:500;margin:0 0 14px}
.claim{border:1px solid var(--line2);padding:12px 14px;margin:9px 0;display:flex;gap:12px;align-items:flex-start}
.pill{font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;border:1px solid currentColor;padding:3px 6px;white-space:nowrap;display:inline-flex;align-items:center;gap:5px}
.pill::before{content:"";width:6px;height:6px;background:currentColor}
.sourced{color:var(--sourced)}.computed{color:var(--computed)}.assumption{color:var(--assume)}
.unknown{color:var(--unknown)}.conflict{color:var(--conflict)}
.faible{color:var(--sourced)}.modéré,.modere{color:var(--assume)}.élevé,.eleve{color:var(--conflict)}
.claim .body{flex:1}.claim .ttl{font-weight:600}
.claim .val{font-family:var(--mono);font-size:13px;margin-top:2px}
.claim small{color:var(--mut);font-family:var(--mono);font-size:10px;display:block;margin-top:3px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.note{font-family:var(--mono);font-size:11px;color:var(--mut);margin-top:10px}
.disc{border-left:3px solid var(--accent);padding:8px 12px;margin:8px 0;font-size:13px;background:rgba(192,57,43,.04)}
footer{width:min(1180px,calc(100vw - 40px));margin:14px auto 40px;font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);border-top:1px solid var(--ink);padding-top:12px}
.spin{color:var(--mut);font-family:var(--mono);font-size:12px}
@media(max-width:820px){.hero,.grid2{grid-template-columns:1fr}.search input{min-width:0;flex:1}}
</style>
</head>
<body>
<header>
  <span class="brand"><span class="ae">Æ</span>DIFICA</span>
  <span class="kicker">Cockpit démo · ArchiOS Suisse</span>
  <span id="mode" class="badge fixture">—</span>
  <div class="search">
    <input id="q" placeholder="Adresse ou EGRID (VD)…" value="Place de la Palud 2, 1003 Lausanne">
    <button onclick="lookup()">Analyser</button>
    <button class="ghost" onclick="preset('lausanne')">Lausanne</button>
    <button class="ghost" onclick="preset('pully')">Pully</button>
  </div>
</header>

<main>
  <section class="hero">
    <div>
      <span class="kicker">Parcelle → savoir de projet sourcé</span>
      <h1 id="heroTitle">Une parcelle. Des contraintes sourcées. En quelques secondes.</h1>
      <p id="heroSub">Tapez une adresse vaudoise : Aedifica récupère la zone, le degré de sensibilité au bruit, les alignements et l'enveloppe constructible — chaque valeur tracée à sa source, sans maquette BIM.</p>
      <div class="kpis">
        <div class="kpi"><b>Zone</b><div class="n" id="kZone">—</div></div>
        <div class="kpi"><b>Surface RF</b><div class="n" id="kArea">—</div></div>
        <div class="kpi"><b>Risque opposition</b><div class="n" id="kRisk">—</div></div>
      </div>
    </div>
    <div>
      <h2>Contrat de lecture</h2>
      <p style="font-size:14px">Chaque affirmation porte son <b>état de preuve</b> : <span class="pill sourced">sourced</span> avec sa source, <span class="pill computed">computed</span>, ou <span class="pill unknown">unknown</span> — jamais une valeur inventée.</p>
      <p class="note" id="footerNote">Préparation sourcée par AEDIFICA. Pas une autorité.</p>
    </div>
  </section>

  <div class="tabs">
    <button class="tab active" data-t="parcelle">Parcelle &amp; contraintes</button>
    <button class="tab" data-t="enveloppe">Enveloppe</button>
    <button class="tab" data-t="opposition">Opposition</button>
    <button class="tab" data-t="permis">Permis</button>
    <button class="tab" data-t="modele">Modèle Archicad</button>
  </div>
  <div class="panelwrap">
    <div class="panel active" id="p-parcelle"><div class="spin">Lancez une analyse…</div></div>
    <div class="panel" id="p-enveloppe"></div>
    <div class="panel" id="p-opposition"></div>
    <div class="panel" id="p-permis"><div class="spin">Chargement…</div></div>
    <div class="panel" id="p-modele"><div class="spin">Chargement…</div></div>
  </div>
</main>
<footer id="footer">AEDIFICA · Datum +13.50 · démo locale — pas une autorité.</footer>

<script>
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cls = s => (s||'unknown').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');
function pill(state){ return `<span class="pill ${cls(state)}">${esc(state)}</span>`; }
function claimCard(c){
  const v = c.value==null ? 'Inconnu' : esc(c.value);
  const meta = [];
  if(c.sources && c.sources.length) meta.push('source: '+esc(c.sources.join(', ')));
  if(c.formula) meta.push('formule: '+esc(c.formula));
  if(c.next_action) meta.push('action: '+esc(c.next_action));
  return `<div class="claim">${pill(c.state)}<div class="body"><div class="ttl">${esc(c.title)}</div><div class="val">${v}</div>${meta.length?`<small>${meta.join(' · ')}</small>`:''}</div></div>`;
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');
  document.getElementById('p-'+t.dataset.t).classList.add('active');
});
async function lookup(){
  const q = document.getElementById('q').value.trim();
  setMode('…','fixture');
  document.getElementById('p-parcelle').innerHTML = '<div class="spin">Interrogation des registres suisses…</div>';
  try{
    const r = await fetch('/api/lookup?live=1&q='+encodeURIComponent(q));
    const d = await r.json();
    renderLookup(d);
  }catch(e){ document.getElementById('p-parcelle').innerHTML = '<div class="spin">Erreur: '+esc(e)+'</div>'; }
}
function preset(name){ const v={lausanne:'Place de la Palud 2, 1003 Lausanne',pully:'Avenue du Prieuré 1, 1009 Pully'}[name]; document.getElementById('q').value=v; lookup(); }
function setMode(txt,kind){ const m=document.getElementById('mode'); m.textContent=txt; m.className='badge '+kind; }
function renderLookup(d){
  setMode(d.mode==='live'?'● LIVE':'fixture', d.mode==='live'?'live':'fixture');
  const p=d.parcel||{};
  document.getElementById('kZone').textContent = p.zone_communal || (p.zone? String(p.zone).slice(0,18):'—');
  document.getElementById('kArea').textContent = p.area_m2? Math.round(p.area_m2)+' m²':'—';
  document.getElementById('kRisk').textContent = (d.opposition&&d.opposition.overall)||'—';
  document.getElementById('kRisk').className = 'n '+cls((d.opposition&&d.opposition.overall)||'');
  document.getElementById('heroTitle').textContent = p.commune? `${p.number||''} · ${p.commune}` : 'Parcelle analysée';
  document.getElementById('heroSub').textContent = `EGRID ${p.egrid||'—'} · zone OEREB « ${p.zone||'—'} »`+(p.zone_communal?` → pack communal « ${p.zone_communal} »`:'')+(d.reason?` · ${d.reason}`:'');
  document.getElementById('footerNote').textContent = d.trust_footer||'';
  // parcelle
  document.getElementById('p-parcelle').innerHTML =
    `<h2>Contraintes parcelle ${d.mode==='live'?'(données live)':'(fixture)'}</h2>`+
    (d.constraints||[]).map(claimCard).join('')+
    `<div class="note">Sources : ${esc((d.sources||[]).map(s=>s.source_id+' ('+(s.valid_as_of||'')+')').join(' · '))}</div>`;
  // enveloppe
  document.getElementById('p-enveloppe').innerHTML =
    `<h2>Enveloppe constructible</h2>`+
    `<p class="note">Limite assumée : l'enveloppe numérique (indices/hauteurs) n'est pas en open data — elle vient du règlement communal ingéré. Les inconnues restent visibles, jamais à zéro.</p>`+
    (d.envelope||[]).map(claimCard).join('');
  // opposition
  const o=d.opposition||{};
  document.getElementById('p-opposition').innerHTML =
    `<h2>Radar de risque d'opposition — ${esc(o.overall)} (score ${esc(o.score)})</h2>`+
    `<p class="note">${esc(o.disclaimer||'')}</p>`+
    (o.signals||[]).map(s=>`<div class="claim">${pill(s.level)}<div class="body"><div class="ttl">${esc(s.ground)} <small style="display:inline">· ${esc(s.category)} · ${esc(s.evidence_state)} · confiance ${esc(s.confidence)}</small></div><div class="val" style="font-family:var(--ui);font-weight:400">${esc(s.basis)}</div><small>mitigation: ${esc(s.mitigation)}</small></div></div>`).join('') ||
    '<div class="spin">Aucun signal saillant.</div>';
}
async function loadPermit(){ try{ renderPermit(await (await fetch('/api/permit')).json()); }catch(e){ document.getElementById('p-permis').innerHTML='<div class="spin">Erreur permis: '+esc(e)+'</div>'; } }
function renderPermit(d){
    const s=d.summary||{};
    document.getElementById('p-permis').innerHTML =
      `<h2>Complétude permis · ${esc(d.dossier_id)}</h2>`+
      `<div class="claim">${pill(d.ready_for_review?'sourced':'assumption')}<div class="body"><div class="ttl">${d.ready_for_review?'Dossier prêt pour revue':'Dossier NON prêt — '+esc(s.required_blockers)+' blocker(s) requis'}</div><small>état: ${esc(d.state)} · present ${esc(s.present||0)} · missing ${esc(s.required_blockers||0)} · assumption ${esc(s.assumptions?s.assumptions.length:0)}</small></div></div>`+
      (d.disclaimers||[]).map(x=>`<div class="disc">${esc(x)}</div>`).join('')+
      (d.groups||[]).map(g=>`<h2 style="margin-top:18px">${esc(g.actor)} · ${esc(g.category)}</h2>`+
        g.items.map(i=>`<div class="claim">${pill(i.status)}<div class="body"><div class="ttl">${esc(i.title)}</div>${(i.status==='missing'||i.status==='assumption')&&i.missing_message?`<small>action: ${esc(i.missing_message)}</small>`:''}<small>provenance: ${esc((i.provenance||[]).join(', ')||'—')}</small></div></div>`).join('')).join('');
}
async function loadModel(){ try{ renderModel(await (await fetch('/api/model')).json()); }catch(e){ document.getElementById('p-modele').innerHTML='<div class="spin">Erreur modèle: '+esc(e)+'</div>'; } }
function renderModel(d){
    document.getElementById('p-modele').innerHTML =
      `<h2>Boucle agent → Archicad (dry-run, fixture)</h2>`+
      `<p class="note">Modèle ${esc(d.model_version)} · ${esc(d.selected_count)} éléments sélectionnés · ${esc(d.audit.missing_count)} métadonnées manquantes détectées.</p>`+
      `<div class="grid2"><div>`+
        `<h2>Métadonnées à compléter</h2>`+
        (d.audit.missing||[]).map(m=>`<div class="claim">${pill('assumption')}<div class="body"><div class="ttl">${esc(m.element_id)}</div><small>${esc(m.proposed_fix||m.property||'')}</small></div></div>`).join('')+
      `</div><div>`+
        `<h2>Garde-fou mutation</h2>`+
        `<div class="claim">${pill(d.blocked_without_approval?'conflict':'sourced')}<div class="body"><div class="ttl">Sans approbation</div><div class="val">${d.blocked_without_approval?'BLOQUÉ':'autorisé'}</div><small>scope requis: ${esc(d.required_approval||'adapter_execution')}</small></div></div>`+
        `<div class="claim">${pill(d.allowed_with_approval?'sourced':'conflict')}<div class="body"><div class="ttl">Avec approbation tracée (ledger)</div><div class="val">${d.allowed_with_approval?'dry-run autorisé':'bloqué'}</div><small>dry-run → approbation → ledger</small></div></div>`+
      `</div></div>`;
}
if(window.__DEMO__){ renderLookup(__DEMO__.lookup); renderPermit(__DEMO__.permit); renderModel(__DEMO__.model); }
else { lookup(); loadPermit(); loadModel(); }
</script>
</body>
</html>
"""


def build_static_html(query: str = PRESETS["lausanne"], live: bool = False) -> str:
    """A self-contained single-file export: data pre-injected, no server needed."""
    payload = {"lookup": build_lookup(query, live), "permit": build_permit(), "model": build_model()}
    inject = "<script>window.__DEMO__=" + json.dumps(payload, ensure_ascii=False) + ";</script>\n</head>"
    return COCKPIT_HTML.replace("</head>", inject)


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
def make_handler():
    class CockpitHandler(BaseHTTPRequestHandler):
        def _send(self, status, body, content_type="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if path in ("/", "/cockpit", "/index.html"):
                return self._send(200, COCKPIT_HTML, "text/html; charset=utf-8")
            if path == "/api/health":
                return self._send(200, json.dumps({"status": "ok"}))
            if path == "/api/lookup":
                params = parse_qs(parsed.query)
                query = (params.get("q", [""])[0]).strip()
                live = params.get("live", ["1"])[0] != "0"
                return self._send(200, json.dumps(build_lookup(query, live), ensure_ascii=False))
            if path == "/api/permit":
                return self._send(200, json.dumps(build_permit(), ensure_ascii=False))
            if path == "/api/model":
                return self._send(200, json.dumps(build_model(), ensure_ascii=False))
            return self._send(404, json.dumps({"error": "not found"}))

        def log_message(self, *_args):
            return

    return CockpitHandler


def serve(host: str = "127.0.0.1", port: int = 8090) -> HTTPServer:
    return HTTPServer((host, port), make_handler())


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Run the Aedifica demo cockpit.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--export", default=None, help="Write a self-contained single-file HTML and exit.")
    parser.add_argument("--query", default=PRESETS["lausanne"], help="Parcel query for --export.")
    parser.add_argument("--live", action="store_true", help="Use a live lookup for --export (else fixture).")
    args = parser.parse_args(argv)

    if args.export:
        with open(args.export, "w", encoding="utf-8") as f:
            f.write(build_static_html(args.query, args.live))
        print(f"Wrote self-contained cockpit to {args.export}")
        return 0

    httpd = serve(args.host, args.port)
    print(f"Aedifica demo cockpit → http://{args.host}:{args.port}  (Ctrl+C to stop)")
    print("Live address lookup with frozen Lausanne/Pully fallback. Local only, no auth.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
