#!/usr/bin/env python3
"""Aedifica demo cockpit — an interactive local web app for partner presentations.

One command launches a Datum-branded, clickable cockpit, styled with the VALIDATED
design system (docs/design-system: Space Grotesk + IBM Plex Mono, self-hosted) so
it is pixel-consistent with the brand book — premium even offline.

    python pilot/demo_cockpit.py            # -> http://127.0.0.1:8090
    python pilot/demo_cockpit.py --export demo.html   # self-contained single file

- LIVE: type a Vaud address or EGRID -> sourced constraints + buildable envelope
  + opposition risk in seconds (swisstopo + RDPPF/OEREB), with a verifiable link
  to the official source, and a frozen Lausanne/Pully fallback if offline.
- WORKFLOW: permit readiness (ACTIS-CAMAC) and the Archicad agent loop
  (dry-run -> approval -> ledger) from fixtures.

Every value keeps its trust state (sourced / computed / unknown); never an
authority decision.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESIGN_DIR = os.path.join(ROOT, "docs", "design-system")
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
RDPPF_PDF = "https://www.rdppf.vd.ch/ws/RdppfSVC.svc/extract/pdf/?EGRID={egrid}&LANG=fr"
GAINS = {
    "parcelle": "Aujourd'hui : géoportail + extrait RDPPF + registre foncier, ~30–60 min. Ici : quelques secondes, chaque valeur tracée à sa source.",
    "enveloppe": "Le potentiel constructible d'un coup d'œil — et les inconnues restent visibles, jamais bricolées en faux chiffres (votre responsabilité est protégée).",
    "opposition": "Anticipez les leviers de recours AVANT la mise à l'enquête, au lieu de les découvrir en opposition.",
    "permis": "Ne plus jamais déposer un dossier incomplet : les manquants ACTIS-CAMAC sont listés, sourcés, avant dépôt.",
    "modele": "Une IA qui agit dans Archicad — mais aucune mutation sans votre approbation explicite, tracée au ledger.",
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
    return {
        "overall": risks.get("overall"),
        "score": risks.get("score"),
        "signals": [
            {
                "ground": s.get("ground"),
                "category": s.get("evidence_category"),
                "level": s.get("level"),
                "basis": s.get("basis"),
                "mitigation": s.get("mitigation"),
                "evidence_state": s.get("evidence_state"),
                "confidence": s.get("confidence"),
            }
            for s in risks.get("signals", [])
        ],
        "disclaimer": radar.NON_PREDICTION_DISCLAIMER,
    }


def _verify_url(egrid: str | None) -> str | None:
    return RDPPF_PDF.format(egrid=egrid) if egrid else None


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
        "laws": [],
        "verify_url": _verify_url(parcel.get("egrid")),
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
    except (Exception, SystemExit) as exc:
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
        "laws": [{"title": law.get("title"), "number": law.get("number"), "url": law.get("url")} for law in oereb_record.get("laws", []) if law.get("url")],
        "verify_url": _verify_url(oereb_record.get("egrid")),
        "sources": [source_ref],
        "trust_footer": trust.render_footer("fr"),
    }


def build_permit() -> dict:
    checklist = workspace._load_json(os.path.join(HERE, "permit", "vd_camac_checklist.json"))
    dossier = workspace._load_json(os.path.join(HERE, "permit", "demo_missing_dossier.json"))
    r = permit_readiness.build_readiness(checklist, dossier)
    return {
        "dossier_id": r["dossier_id"],
        "state": r["state"],
        "ready_for_review": r["ready_for_review"],
        "summary": r["summary"],
        "groups": [
            {
                "actor": g["actor"],
                "category": g["category"],
                "items": [
                    {"title": i["title"], "status": i["status"], "missing_message": i.get("missing_message"), "provenance": i.get("checklist_provenance", [])}
                    for i in g["items"]
                ],
            }
            for g in r["groups"]
        ],
        "disclaimers": r["disclaimers"],
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
                {"element_id": i.get("element_id"), "property": i.get("property") or i.get("missing_property") or i.get("field"), "proposed_fix": i.get("proposed_fix")}
                for i in audit.get("missing", [])[:6]
            ],
        },
        "blocked_without_approval": bool(blocked.get("blocked")),
        "allowed_with_approval": not bool(approved.get("blocked")),
        "required_approval": blocked.get("required_approval"),
    }


# --------------------------------------------------------------------------- #
# HTML (styled with the validated Datum design system at /ds/)
# --------------------------------------------------------------------------- #
COCKPIT_HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AEDIFICA — Cockpit démo</title>
<link rel="icon" href="/ds/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/ds/colors_and_type.css">
<style>
*{box-sizing:border-box}
body{margin:0;background:var(--surface);color:var(--ink);font-family:var(--font-ui);line-height:1.5}
.hdr{position:sticky;top:0;z-index:10;background:var(--surface);border-bottom:1px solid var(--ink);padding:13px 26px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.hdr .ds-wordmark{font-size:21px}
.search{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.search input{font-family:var(--font-mono);font-size:13px;padding:11px 13px;border:1px solid var(--ink);background:var(--surface-2);min-width:300px;border-radius:var(--r-1)}
.search .ds-btn{padding:11px 16px}
.modechip{font-family:var(--font-mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;padding:4px 8px;border:1px solid currentColor;color:var(--mut)}
.modechip.live{color:var(--ts-sourced)}.modechip.fixture{color:var(--ts-assume)}
main{width:min(1180px,calc(100vw - 40px));margin:22px auto}
.hero{display:grid;grid-template-columns:1.5fr 1fr;gap:24px;border:1px solid var(--ink);background:var(--surface-2);padding:28px;margin-bottom:18px}
.hero h1{margin:.14em 0 .34em}
.hero aside .ds-body{font-size:14px;margin-top:8px}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}
.kpi{border:1px solid var(--line-2);padding:13px}
.kpi b{display:block;font-family:var(--font-mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-bottom:5px}
.kpi .n{font-family:var(--font-display);font-weight:300;font-size:30px;line-height:1.05;letter-spacing:-.02em}
.tabs{display:flex;border:1px solid var(--ink);border-bottom:0}
.tab{flex:1;text-align:center;padding:13px 8px;border-right:1px solid var(--ink);background:var(--surface-2);color:var(--ink);font-family:var(--font-mono);font-size:11px;letter-spacing:.07em;text-transform:uppercase;cursor:pointer}
.tab:last-child{border-right:0}
.tab.active{background:var(--ink);color:var(--surface)}
.panelwrap{border:1px solid var(--ink);background:var(--surface-2);padding:24px;min-height:360px}
.panel{display:none}.panel.active{display:block}
.sec{font-family:var(--font-mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--mut);margin:0 0 14px}
.gain{border:1px solid var(--line-2);background:var(--paper-2);padding:11px 14px;margin:0 0 18px;font-size:13.5px}
.gain b{font-family:var(--font-mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);display:block;margin-bottom:3px}
.claim{border:1px solid var(--line-2);padding:12px 14px;margin:9px 0;display:flex;gap:13px;align-items:flex-start}
.claim .body{flex:1;min-width:0}.claim .ttl{font-weight:500}
.claim .val{font-family:var(--font-mono);font-size:13px;margin-top:3px;color:var(--ink-90)}
.claim small{color:var(--mut);font-family:var(--font-mono);font-size:10px;display:block;margin-top:4px;word-break:break-word}
a.src{color:var(--accent);text-decoration:none;border-bottom:1px solid currentColor;font-family:var(--font-mono);font-size:11px}
.verify{margin:14px 0 4px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.note{font-family:var(--font-mono);font-size:11px;color:var(--mut);margin-top:10px}
.disc{border-left:3px solid var(--accent);padding:8px 12px;margin:8px 0;font-size:13px;background:var(--trust-bg)}
.lvl{display:inline-flex;align-items:center;gap:6px;font-family:var(--font-mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;padding:3px 7px;border:1px solid currentColor;line-height:1;white-space:nowrap}
.lvl::before{content:"";width:7px;height:7px;background:currentColor}
.lvl.faible{color:var(--ts-sourced)}.lvl.modere{color:var(--ts-assume)}.lvl.eleve{color:var(--ts-conflict)}.lvl.inconnu{color:var(--ts-unknown)}
.spin{color:var(--mut);font-family:var(--font-mono);font-size:12px}
footer{width:min(1180px,calc(100vw - 40px));margin:14px auto 44px;font-family:var(--font-mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut);border-top:1px solid var(--ink);padding-top:12px}
@media(max-width:820px){.hero,.grid2{grid-template-columns:1fr}.search input{min-width:0;flex:1}}
</style>
</head>
<body>
<header class="hdr">
  <span class="ds-wordmark"><span class="ae">Æ</span>DIFICA</span>
  <span class="ds-eyebrow">Cockpit démo · ArchiOS Suisse</span>
  <span id="mode" class="modechip">—</span>
  <div class="search">
    <input id="q" placeholder="Adresse ou EGRID (VD)…" value="Place de la Palud 2, 1003 Lausanne">
    <button class="ds-btn" onclick="lookup()">Analyser</button>
    <button class="ds-btn ds-btn--ghost" onclick="preset('lausanne')">Lausanne</button>
    <button class="ds-btn ds-btn--ghost" onclick="preset('pully')">Pully</button>
  </div>
</header>

<main>
  <section class="hero">
    <div>
      <p class="ds-eyebrow">Parcelle → savoir de projet sourcé</p>
      <h1 class="ds-display-2" id="heroTitle">Une parcelle. Des contraintes sourcées. En quelques secondes.</h1>
      <p class="ds-lead" id="heroSub">Tapez une adresse vaudoise : zone, degré de sensibilité au bruit, alignements et enveloppe constructible — chaque valeur tracée à sa source officielle, sans maquette BIM.</p>
      <div class="kpis">
        <div class="kpi"><b>Zone</b><div class="n" id="kZone">—</div></div>
        <div class="kpi"><b>Surface RF</b><div class="n" id="kArea">—</div></div>
        <div class="kpi"><b>Risque opposition</b><div class="n" id="kRisk">—</div></div>
      </div>
    </div>
    <aside>
      <p class="ds-eyebrow">Contrat de lecture</p>
      <p class="ds-body">Chaque affirmation porte son <b>état de preuve</b> : <span class="ds-ts is-sourced"><span class="dot"></span>sourced</span> avec sa source, <span class="ds-ts is-computed"><span class="dot"></span>computed</span>, ou <span class="ds-ts is-unknown"><span class="dot"></span>unknown</span> — jamais une valeur inventée.</p>
      <p class="note" id="footerNote">Préparation sourcée par AEDIFICA. Pas une autorité.</p>
    </aside>
  </section>

  <nav class="tabs">
    <button class="tab active" data-t="parcelle">Parcelle &amp; contraintes</button>
    <button class="tab" data-t="enveloppe">Enveloppe</button>
    <button class="tab" data-t="opposition">Opposition</button>
    <button class="tab" data-t="permis">Permis</button>
    <button class="tab" data-t="modele">Modèle Archicad</button>
  </nav>
  <div class="panelwrap">
    <div class="panel active" id="p-parcelle"><div class="spin">Lancez une analyse…</div></div>
    <div class="panel" id="p-enveloppe"></div>
    <div class="panel" id="p-opposition"></div>
    <div class="panel" id="p-permis"><div class="spin">Chargement…</div></div>
    <div class="panel" id="p-modele"><div class="spin">Chargement…</div></div>
  </div>
</main>
<footer>AEDIFICA · Datum +13.50 · démo locale — pas une autorité.</footer>

<script>
const G = __GAINS__;
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cls = s => (s||'unknown').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');
const TS = {sourced:'is-sourced',computed:'is-computed',assumption:'is-assume',unknown:'is-unknown',conflict:'is-conflict',decision:'is-decision'};
function pill(state){ return `<span class="ds-ts ${TS[state]||'is-unknown'}"><span class="dot"></span>${esc(state)}</span>`; }
function gain(t){ return `<div class="gain"><b>Le gain pour vous</b>${esc(G[t]||'')}</div>`; }
function claimCard(c){
  const v = c.value==null ? 'Inconnu' : esc(c.value);
  const meta=[];
  if(c.sources&&c.sources.length) meta.push('source: '+esc(c.sources.join(', ')));
  if(c.formula) meta.push('formule: '+esc(c.formula));
  if(c.next_action) meta.push('action: '+esc(c.next_action));
  return `<div class="claim">${pill(c.state)}<div class="body"><div class="ttl">${esc(c.title)}</div><div class="val">${v}</div>${meta.length?`<small>${meta.join(' · ')}</small>`:''}</div></div>`;
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active'); document.getElementById('p-'+t.dataset.t).classList.add('active');
});
function setMode(txt,kind){ const m=document.getElementById('mode'); m.textContent=txt; m.className='modechip '+kind; }
async function lookup(){
  const q=document.getElementById('q').value.trim(); setMode('…','fixture');
  document.getElementById('p-parcelle').innerHTML='<div class="spin">Interrogation des registres suisses…</div>';
  try{ renderLookup(await (await fetch('/api/lookup?live=1&q='+encodeURIComponent(q))).json()); }
  catch(e){ document.getElementById('p-parcelle').innerHTML='<div class="spin">Erreur: '+esc(e)+'</div>'; }
}
function preset(n){ document.getElementById('q').value=({lausanne:'Place de la Palud 2, 1003 Lausanne',pully:'Avenue du Prieuré 1, 1009 Pully'})[n]; lookup(); }
function renderLookup(d){
  setMode(d.mode==='live'?'● LIVE':'fixture', d.mode==='live'?'live':'fixture');
  const p=d.parcel||{};
  document.getElementById('kZone').textContent=p.zone_communal||(p.zone?String(p.zone).slice(0,18):'—');
  document.getElementById('kArea').textContent=p.area_m2?Math.round(p.area_m2)+' m²':'—';
  const k=document.getElementById('kRisk'); const ov=(d.opposition&&d.opposition.overall)||'—'; k.textContent=ov; k.style.color=({faible:'var(--ts-sourced)','modéré':'var(--ts-assume)','élevé':'var(--ts-conflict)'})[ov]||'var(--ink)';
  document.getElementById('heroTitle').textContent=p.commune?`${p.number||''} · ${p.commune}`:'Parcelle analysée';
  document.getElementById('heroSub').textContent=`EGRID ${p.egrid||'—'} · zone OEREB « ${p.zone||'—'} »`+(p.zone_communal?` → pack communal « ${p.zone_communal} »`:'')+(d.reason?` · ${d.reason}`:'');
  document.getElementById('footerNote').textContent=d.trust_footer||'';
  const laws=(d.laws||[]).map(l=>`<a class="src" href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.number||l.title)}</a>`).join(' · ');
  document.getElementById('p-parcelle').innerHTML=gain('parcelle')+
    `<p class="sec">Contraintes parcelle ${d.mode==='live'?'(données live)':'(fixture)'}</p>`+
    (d.constraints||[]).map(claimCard).join('')+
    (d.verify_url?`<p class="verify"><a class="src" href="${esc(d.verify_url)}" target="_blank" rel="noopener">↗ Vérifier à la source officielle (extrait RDPPF/OEREB)</a></p>`:'')+
    (laws?`<div class="note">Actes applicables : ${laws}</div>`:'')+
    `<div class="note">Sources : ${esc((d.sources||[]).map(s=>s.source_id+' ('+(s.valid_as_of||'')+')').join(' · '))}</div>`;
  document.getElementById('p-enveloppe').innerHTML=gain('enveloppe')+
    `<p class="sec">Enveloppe constructible</p>`+
    `<p class="note">L'enveloppe numérique (indices/hauteurs) n'est pas en open data — elle vient du règlement communal ingéré. Les inconnues restent visibles, jamais à zéro.</p>`+
    (d.envelope||[]).map(claimCard).join('');
  const o=d.opposition||{};
  document.getElementById('p-opposition').innerHTML=gain('opposition')+
    `<p class="sec">Radar de risque d'opposition — ${esc(o.overall)} (score ${esc(o.score)})</p>`+
    `<p class="note">${esc(o.disclaimer||'')}</p>`+
    ((o.signals||[]).map(s=>`<div class="claim"><span class="lvl ${cls(s.level)}">${esc(s.level)}</span><div class="body"><div class="ttl">${esc(s.ground)} <small style="display:inline">· ${esc(s.category)} · ${esc(s.evidence_state)} · confiance ${esc(s.confidence)}</small></div><div class="val" style="font-family:var(--font-ui);font-weight:400">${esc(s.basis)}</div><small>mitigation: ${esc(s.mitigation)}</small></div></div>`).join('')||'<div class="spin">Aucun signal saillant.</div>');
}
async function loadPermit(){ try{ renderPermit(await (await fetch('/api/permit')).json()); }catch(e){ document.getElementById('p-permis').innerHTML='<div class="spin">Erreur permis: '+esc(e)+'</div>'; } }
function renderPermit(d){
  const s=d.summary||{};
  document.getElementById('p-permis').innerHTML=gain('permis')+
    `<p class="sec">Complétude permis · ${esc(d.dossier_id)}</p>`+
    `<div class="claim">${pill(d.ready_for_review?'sourced':'assumption')}<div class="body"><div class="ttl">${d.ready_for_review?'Dossier prêt pour revue':'Dossier NON prêt — '+esc(s.required_blockers)+' blocker(s) requis'}</div><small>état: ${esc(d.state)} · present ${esc(s.present||0)} · missing ${esc(s.required_blockers||0)}</small></div></div>`+
    (d.disclaimers||[]).map(x=>`<div class="disc">${esc(x)}</div>`).join('')+
    (d.groups||[]).map(g=>`<p class="sec" style="margin-top:18px">${esc(g.actor)} · ${esc(g.category)}</p>`+
      g.items.map(i=>`<div class="claim">${pill(i.status)}<div class="body"><div class="ttl">${esc(i.title)}</div>${(i.status==='missing'||i.status==='assumption')&&i.missing_message?`<small>action: ${esc(i.missing_message)}</small>`:''}<small>provenance: ${esc((i.provenance||[]).join(', ')||'—')}</small></div></div>`).join('')).join('');
}
async function loadModel(){ try{ renderModel(await (await fetch('/api/model')).json()); }catch(e){ document.getElementById('p-modele').innerHTML='<div class="spin">Erreur modèle: '+esc(e)+'</div>'; } }
function renderModel(d){
  document.getElementById('p-modele').innerHTML=gain('modele')+
    `<p class="sec">Boucle agent → Archicad (dry-run, fixture)</p>`+
    `<p class="note">Modèle ${esc(d.model_version)} · ${esc(d.selected_count)} éléments · ${esc(d.audit.missing_count)} métadonnées manquantes détectées.</p>`+
    `<div class="grid2"><div><p class="sec">Métadonnées à compléter</p>`+
      (d.audit.missing||[]).map(m=>`<div class="claim">${pill('assumption')}<div class="body"><div class="ttl">${esc(m.element_id)}</div><small>${esc(m.proposed_fix||m.property||'')}</small></div></div>`).join('')+
    `</div><div><p class="sec">Garde-fou mutation</p>`+
      `<div class="claim">${pill(d.blocked_without_approval?'conflict':'sourced')}<div class="body"><div class="ttl">Sans approbation</div><div class="val">${d.blocked_without_approval?'BLOQUÉ':'autorisé'}</div><small>scope requis: ${esc(d.required_approval||'adapter_execution')}</small></div></div>`+
      `<div class="claim">${pill(d.allowed_with_approval?'sourced':'conflict')}<div class="body"><div class="ttl">Avec approbation tracée (ledger)</div><div class="val">${d.allowed_with_approval?'dry-run autorisé':'bloqué'}</div><small>dry-run → approbation → ledger</small></div></div>`+
    `</div></div>`;
}
if(window.__DEMO__){ renderLookup(__DEMO__.lookup); renderPermit(__DEMO__.permit); renderModel(__DEMO__.model); }
else { lookup(); loadPermit(); loadModel(); }
</script>
</body>
</html>
""".replace("__GAINS__", json.dumps(GAINS, ensure_ascii=False))


# --------------------------------------------------------------------------- #
# Static export (self-contained single file: inline CSS + base64 fonts)
# --------------------------------------------------------------------------- #
def _inline_design_css() -> str:
    with open(os.path.join(DESIGN_DIR, "colors_and_type.css"), encoding="utf-8") as f:
        css = f.read()
    for font_name in ("SpaceGrotesk-Variable.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
        path = os.path.join(DESIGN_DIR, "fonts", font_name)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
        css = css.replace(f'url("fonts/{font_name}")', f"url(data:font/ttf;base64,{b64})")
    return css


def build_static_html(query: str = PRESETS["lausanne"], live: bool = False) -> str:
    payload = {"lookup": build_lookup(query, live), "permit": build_permit(), "model": build_model()}
    html = COCKPIT_HTML.replace('<link rel="stylesheet" href="/ds/colors_and_type.css">', f"<style>{_inline_design_css()}</style>")
    html = html.replace('<link rel="icon" href="/ds/assets/favicon.svg" type="image/svg+xml">', "")
    inject = "<script>window.__DEMO__=" + json.dumps(payload, ensure_ascii=False) + ";</script>\n</head>"
    return html.replace("</head>", inject)


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
_CTYPE = {".css": "text/css; charset=utf-8", ".ttf": "font/ttf", ".woff": "font/woff", ".woff2": "font/woff2", ".svg": "image/svg+xml", ".png": "image/png"}


def make_handler():
    class CockpitHandler(BaseHTTPRequestHandler):
        def _send(self, status, body, content_type="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _serve_design(self, rel):
            safe = os.path.normpath(unquote(rel)).lstrip("\\/")
            full = os.path.normpath(os.path.join(DESIGN_DIR, safe))
            if not full.startswith(DESIGN_DIR) or not os.path.isfile(full):
                return self._send(404, json.dumps({"error": "not found"}))
            ext = os.path.splitext(full)[1].lower()
            with open(full, "rb") as fh:
                self._send(200, fh.read(), _CTYPE.get(ext, "application/octet-stream"))

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if path in ("/", "/cockpit", "/index.html"):
                return self._send(200, COCKPIT_HTML, "text/html; charset=utf-8")
            if path.startswith("/ds/"):
                return self._serve_design(path[len("/ds/"):])
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
    print("Datum-branded · live address lookup + frozen fallback · local only, no auth.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
