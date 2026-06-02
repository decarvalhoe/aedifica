#!/usr/bin/env python3
"""Render the minimal Datum workspace surfaces from a real fixture project.

Three surfaces, all data-driven (no marketing page, no fabricated claims):
- workspace shell: project state, route, source/report status, next actions;
- parcel intake: address / EGRID / parcel intake state from the manifest;
- claim review: claims grouped by trust state, unknowns show the next action,
  assumptions carry an explicit human-review status.

Deterministic output (no timestamps) so the committed ``pilot/ui/*.html`` stay
stable. Uses the validated design system in ``docs/design-system``.

Usage:
    python pilot/workspace_ui.py --write          # regenerate pilot/ui/*.html
    python pilot/workspace_ui.py --out pilot/out   # write elsewhere
"""
from __future__ import annotations

import argparse
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import workspace  # noqa: E402

DEMO_PROJECT = os.path.join(HERE, "projects", "demo_lausanne_palud")
FOOTER = "Préparation sourcée par AEDIFICA. Pas une autorité."

# Map product trust states to the design-system pill classes.
_PILL = {
    "sourced": "is-sourced",
    "computed": "is-computed",
    "assumption": "is-assume",
    "unknown": "is-unknown",
    "conflict": "is-unknown",
    "decision": "is-computed",
}


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _doc(title: str, label: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AEDIFICA — {_esc(title)}</title>
  <link rel="icon" href="../../docs/design-system/assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../../docs/design-system/colors_and_type.css">
  <link rel="stylesheet" href="../../docs/design-system/aedifica-datum-ui.css">
  <style>
    .ds-ts.is-unknown {{ color: var(--st-unknown, #84847A); }}
    .ds-ts {{ white-space: nowrap; }}
    .wsr-actions li {{ margin: 6px 0; }}
    .wsr-val {{ font-family: var(--font-mono, monospace); }}
    td, th {{ word-break: break-word; }}
    .dt th:first-child, .dt td:first-child {{ width: 132px; white-space: nowrap; }}
  </style>
</head>
<body class="datum-viewport datum-surface">
  <main class="slide" aria-label="AEDIFICA {_esc(label)}">
{body}
    <footer class="slide__foot">
      <span><b>{_esc(FOOTER)}</b></span>
      <span>§ {_esc(label)}</span>
    </footer>
  </main>
</body>
</html>
"""


def _pill(state: str) -> str:
    cls = _PILL.get(state, "is-unknown")
    return f"<span class='ds-ts {cls}'><span class='dot'></span>{_esc(state)}</span>"


def _state_counts(claims: list) -> dict:
    counts = {}
    for claim in claims:
        counts[claim.get("state")] = counts.get(claim.get("state"), 0) + 1
    return counts


def render_workspace_shell(project_dir: str = DEMO_PROJECT) -> str:
    manifest = workspace._load_json(workspace.project_manifest_path(project_dir))
    brief = workspace.generate_offline_parcel_brief(project_dir)
    route = brief.get("regulatory_route", {})
    counts = _state_counts(brief.get("claims", []))
    active_layers = route.get("active_layers", [])
    warnings = brief.get("freshness_warnings", [])
    jur = manifest.get("jurisdiction", {})

    next_actions = "".join(
        f"<li>{_esc(item.get('topic'))} — {_esc(item.get('next_action'))}</li>"
        for item in brief.get("residual_unknowns", [])[:6]
    )
    layer_rows = "".join(
        f"<tr><td>{_esc(layer.get('layer_id'))}</td>"
        f"<td><span class='ds-ts is-sourced'><span class='dot'></span>{_esc(layer.get('source_version_id') or 'active')}</span></td></tr>"
        for layer in active_layers
    )
    body = f"""    <div class="slide__topline">
      <span>Workspace</span>
      <span>{_esc(manifest.get('project_id'))}</span>
      <span><a href="project_intake.html">Intake</a> · <a href="claim_review.html">Claims</a></span>
    </div>
    <section class="slide__head">
      <div class="slide__kicker">
        <span class="snum">§ R1B</span>
        <span class="ds-eyebrow">Projet · route · sources · inconnues</span>
      </div>
      <h1 class="d-title">{_esc(manifest.get('name'))}</h1>
      <p class="d-lead">Surface de travail du projet {_esc(jur.get('country'))} · {_esc(jur.get('canton'))} · {_esc(jur.get('commune'))} — route réglementaire, état des contraintes et prochaines vérifications. Chaque sortie garde son état de preuve.</p>
    </section>
    <section class="slide__body">
      <div class="g2" style="height:100%; align-items:stretch">
        <article class="dash">
          <div class="dash__bar">
            <span class="ds-wordmark"><span class="ae">Æ</span>DIFICA</span>
            <span class="sub">{_esc(manifest.get('project_id'))}</span>
            <span class="sp mono">{_esc(jur.get('country'))} · {_esc(jur.get('canton'))} · {_esc(jur.get('commune'))}</span>
          </div>
          <div class="dash__body">
            <div class="g3 gap-tight mobile-g2" style="margin-bottom:14px">
              <div class="kpi"><div class="kpi__label">Route</div><div class="kpi__num">{len(active_layers)}</div><div class="kpi__foot">couches actives</div></div>
              <div class="kpi"><div class="kpi__label">Sourcé</div><div class="kpi__num">{counts.get('sourced', 0)}</div><div class="kpi__foot">contraintes sourcées</div></div>
              <div class="kpi"><div class="kpi__label">Unknowns</div><div class="kpi__num">{counts.get('unknown', 0)}</div><div class="kpi__foot"><span class="state-sq" style="color:var(--st-unknown);border-style:dashed;background:transparent"></span>à sourcer</div></div>
            </div>
            <table class="dt"><tbody>{layer_rows}</tbody></table>
          </div>
        </article>
        <aside class="panel panel--ink">
          <h2>Prochaines vérifications.</h2>
          <ul class="wsr-actions">{next_actions or '<li>Aucune inconnue résiduelle.</li>'}</ul>
          {'<p class="wsr-val">' + str(len(warnings)) + ' avertissement(s) de fraîcheur de pack.</p>' if warnings else ''}
        </aside>
      </div>
    </section>"""
    return _doc("Workspace", "workspace", body)


def render_parcel_intake(project_dir: str = DEMO_PROJECT) -> str:
    manifest = workspace._load_json(workspace.project_manifest_path(project_dir))
    jur = manifest.get("jurisdiction", {})
    parcel = manifest.get("parcel", {})
    body = f"""    <div class="slide__topline">
      <span><a href="app_shell.html">Workspace</a></span>
      <span>Project intake</span>
      <span><a href="claim_review.html">Claims</a></span>
    </div>
    <section class="slide__head">
      <div class="slide__kicker">
        <span class="snum">§ 01</span>
        <span class="ds-eyebrow">Créer le contexte projet</span>
      </div>
      <h1 class="d-title">Adresse, EGRID ou parcelle — le contexte d'abord.</h1>
      <p class="d-lead">L'intake fixe le périmètre, active les packs juridictionnels et prépare la mémoire sourcée. Aucune valeur d'enveloppe n'est inventée : les inconnues restent visibles.</p>
    </section>
    <section class="slide__body">
      <div class="g2" style="height:100%; align-items:start">
        <form class="panel" aria-label="Project intake form">
          <div class="g2 gap-tight mobile-g2">
            <div class="field"><label>Project ID</label><input name="project_id" value="{_esc(manifest.get('project_id'))}"></div>
            <div class="field"><label>Phase (SIA)</label><input name="phase" value="{_esc(manifest.get('phase_code'))}"></div>
            <div class="field"><label>Country</label><input name="country" value="{_esc(jur.get('country'))}"></div>
            <div class="field"><label>Canton</label><input name="canton" value="{_esc(jur.get('canton'))}"></div>
            <div class="field"><label>Commune</label><input name="commune" value="{_esc(jur.get('commune'))}"></div>
            <div class="field"><label>EGRID</label><input name="egrid" value="{_esc(parcel.get('egrid'))}"></div>
            <div class="field"><label>Parcelle</label><input name="parcel" value="{_esc(parcel.get('number'))}"></div>
            <div class="field"><label>Adresse</label><input name="address" placeholder="ou rechercher par adresse"></div>
          </div>
          <div style="display:flex;gap:12px;margin-top:18px;flex-wrap:wrap">
            <button class="ds-btn ds-btn--accent" type="button">Créer le workspace</button>
            <button class="ds-btn ds-btn--ghost" type="button">Voir la source</button>
          </div>
        </form>
        <aside class="panel panel--accent">
          <h2>Ce que l'intake produit.</h2>
          <ul>
            <li>Route {_esc(jur.get('country'))} / {_esc(jur.get('canton'))} / {_esc(jur.get('commune'))} avec fraîcheur des packs.</li>
            <li>Registre de sources et premiers unknowns.</li>
            <li>Contrat de preuve avant tout rapport ou adapter.</li>
            <li>Surface suivante : workspace, pas écran marketing.</li>
          </ul>
        </aside>
      </div>
    </section>"""
    return _doc("Project Intake", "intake", body)


def render_claim_review(brief: dict | None = None, project_dir: str = DEMO_PROJECT) -> str:
    if brief is None:
        brief = workspace.generate_offline_parcel_brief(project_dir)
    claims_list = brief.get("claims", [])
    counts = _state_counts(claims_list)
    pills = "".join(
        f"<span class='ds-ts {_PILL.get(state, 'is-unknown')}' style='margin-right:8px'><span class='dot'></span>{_esc(state)} · {counts.get(state, 0)}</span>"
        for state in ("sourced", "computed", "assumption", "unknown", "conflict")
    )

    def human_check(claim):
        if claim.get("state") in {"assumption", "unknown", "conflict"}:
            return claim.get("required_human_check") or claim.get("next_action") or "Revue humaine requise"
        return claim.get("required_human_check") or "—"

    def evidence(claim):
        refs = [ref.get("source_id") for ref in claim.get("source_refs", []) if ref.get("source_id")]
        return ", ".join(refs) if refs else "—"

    rows = "".join(
        f"<tr><td>{_pill(claim.get('state'))}</td>"
        f"<td>{_esc(claim.get('title'))}</td>"
        f"<td class='wsr-val'>{'Inconnu' if claim.get('value') is None else _esc(claim.get('value'))}</td>"
        f"<td>{_esc(evidence(claim))}</td>"
        f"<td>{_esc(human_check(claim))}</td></tr>"
        for claim in claims_list
    )
    body = f"""    <div class="slide__topline">
      <span><a href="app_shell.html">Workspace</a></span>
      <span>Claim review</span>
      <span><a href="project_intake.html">Intake</a></span>
    </div>
    <section class="slide__head">
      <div class="slide__kicker">
        <span class="snum">§ 09.3</span>
        <span class="ds-eyebrow">Claim card · evidence · ledger</span>
      </div>
      <h1 class="d-title">Chaque affirmation porte son état.</h1>
      <p class="d-lead">Sourced, computed, assumption, unknown — une seule grammaire. Les inconnues affichent l'action suivante ; les hypothèses exigent un statut de revue humaine explicite.</p>
      <p style="margin-top:10px">{pills}</p>
    </section>
    <section class="slide__body">
      <table class="dt">
        <thead><tr><th>State</th><th>Claim</th><th>Value</th><th>Evidence</th><th>Human check</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>"""
    return _doc("Claim Review", "claims", body)


SURFACES = {
    "app_shell.html": render_workspace_shell,
    "project_intake.html": render_parcel_intake,
    "claim_review.html": render_claim_review,
}


def write_surfaces(out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for filename, renderer in SURFACES.items():
        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
            f.write(renderer())
        written.append(filename)
    return written


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Render the Datum workspace surfaces from the fixture project.")
    parser.add_argument("--out", default=None, help="Output directory (default: pilot/ui when --write).")
    parser.add_argument("--write", action="store_true", help="Write into pilot/ui/.")
    args = parser.parse_args(argv)
    out_dir = args.out or (os.path.join(HERE, "ui") if args.write else os.path.join(HERE, "out", "ui"))
    written = write_surfaces(out_dir)
    print(f"Wrote {len(written)} surfaces to {out_dir}: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
