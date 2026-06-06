#!/bin/bash
# Seed an Aedifica workspace for Etienne Piergiovanni (Atelier Carré-Neuf) on the
# given base URL. Stand-alone from seed-demo.sh --different org, different login,
# realistic content based on the 2026-06-05 session (Pareto/Murphy P0/P1/P2 nav,
# BRS via PV + téléphone, captures friction/photo, multi-actor invites ready).
#
# Usage: scripts/seed-etienne.sh https://aedifica-demo.fly.dev
set -e
BASE="${1:?usage: $0 <base-url>}"
API="${BASE%/}/api"

post() { curl -fsS -X POST "$1" -H 'Content-Type: application/json' --data-binary "$2"; }
post_auth() { curl -fsS -X POST "$1" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" --data-binary "$2"; }

# 1) Atelier + owner
R=$(post "$API/orgs" '{"org_name":"Atelier Carre-Neuf","user_email":"etienne@carre-neuf.ch","user_name":"Etienne Piergiovanni","password":"carre-neuf-2026"}')
TOK=$(echo "$R" | python -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# 2) Project: a realistic small-scale Vaud renovation/upgrade (sub-phase 32 --projet de l'ouvrage)
post_auth "$API/projects" '{"project_id":"CN-LUTRY-2026","name":"Rehabilitation Bourg-Dessus, Lutry","commune":"Lutry"}' > /dev/null
# Seeded at phase 21 (faisabilite done) so phase 11 is retroactive --surfaces external blockers immediately
post_auth "$API/projects/CN-LUTRY-2026/checklist/seed" '{"entry_phase":"21"}' > /dev/null

# 3) Documents --one canonical (the cadastral plan) + two pending (the to-validate queue)
DOC1=$(post_auth "$API/projects/CN-LUTRY-2026/documents" '{"official_name":"Plan cadastral 904, Lutry","category":"plan"}' | python -c 'import sys,json;print(json.load(sys.stdin)["document"]["id"])')
curl -fsS -X POST "$API/projects/CN-LUTRY-2026/documents/$DOC1/validate" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" --data-binary '{"level":"canonical"}' > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/documents" '{"official_name":"Reglement communal Lutry (extrait 2025)","category":"regulation"}' > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/documents" '{"official_name":"Permis de construire CAMAC 2026-0214","category":"permit","confidential":true}' > /dev/null

# 4) Intervenants --owner side + civil engineer + geometer + thermicien
G_ENG=$(post_auth "$API/projects/CN-LUTRY-2026/intervenant-groups" '{"name":"Ingenieurs","kind":"discipline"}' | python -c 'import sys,json;print(json.load(sys.stdin)["group"]["id"])')
G_MAND=$(post_auth "$API/projects/CN-LUTRY-2026/intervenant-groups" '{"name":"Mandataires","kind":"discipline"}' | python -c 'import sys,json;print(json.load(sys.stdin)["group"]["id"])')

IV_MO=$(post_auth "$API/projects/CN-LUTRY-2026/intervenants" '{"name":"M. & Mme Bourg-Pellet","role":"maitre de louvrage","email":"famille.bourg@example.org","is_responsible":true}' | python -c 'import sys,json;print(json.load(sys.stdin)["intervenant"]["id"])')
IV_CIV=$(post_auth "$API/projects/CN-LUTRY-2026/intervenants" "{\"name\":\"Anne Civilis\",\"role\":\"ingenieure civile\",\"organization\":\"Civilis Ingenierie SA\",\"email\":\"a.civilis@civilis.ch\",\"group_id\":$G_ENG,\"is_responsible\":true}" | python -c 'import sys,json;print(json.load(sys.stdin)["intervenant"]["id"])')
IV_GEO=$(post_auth "$API/projects/CN-LUTRY-2026/intervenants" "{\"name\":\"Jean-Luc Mesure\",\"role\":\"geometre officiel\",\"organization\":\"Geometres Vaud SA\",\"email\":\"jl.mesure@geo-vd.ch\",\"group_id\":$G_MAND}" | python -c 'import sys,json;print(json.load(sys.stdin)["intervenant"]["id"])')
IV_THE=$(post_auth "$API/projects/CN-LUTRY-2026/intervenants" "{\"name\":\"Sabine Thermique\",\"role\":\"ingenieure thermicienne\",\"organization\":\"Thermo+Bois SA\",\"email\":\"s.thermique@thermo-bois.ch\",\"group_id\":$G_ENG}" | python -c 'import sys,json;print(json.load(sys.stdin)["intervenant"]["id"])')

# Plan cadastral → access for the engineers group
post_auth "$API/projects/CN-LUTRY-2026/documents/$DOC1/grants" "{\"group_id\":$G_ENG,\"level\":\"read\"}" > /dev/null

# 5) BRS --"PV + coup de telephone" --Etienne's verbatim from [02:35] et [27:50]
post_auth "$API/projects/CN-LUTRY-2026/brs" "{\"content\":\"Le client demande l-augmentation de la hauteur du salon de 30cm.\",\"kind\":\"change\",\"channel\":\"phone\",\"emitter_intervenant_id\":$IV_MO}" > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/brs" "{\"content\":\"Decision actee : materialisation principale en bois (validee en seance).\",\"kind\":\"decision\",\"channel\":\"pv\",\"emitter_intervenant_id\":$IV_MO,\"source_ref\":\"PV seance 2026-05-12\"}" > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/brs" "{\"content\":\"Budget cadre reaffirme : 950'000 CHF (CFC2).\",\"kind\":\"requirement\",\"channel\":\"email\",\"emitter_intervenant_id\":$IV_MO}" > /dev/null

# 6) Tasks --realistic priority navigation (P0 = concours/rendu, P1 = bloquant, P2 = quick win)
T1=$(post_auth "$API/projects/CN-LUTRY-2026/tasks" '{"title":"Rendu permis CAMAC","priority":"p0","estimate_hours":24,"due_date":"2026-07-15","phase_code":"33"}' | python -c 'import sys,json;print(json.load(sys.stdin)["task"]["id"])')
T2=$(post_auth "$API/projects/CN-LUTRY-2026/tasks" '{"title":"Coordination structure (Civilis)","priority":"p1","estimate_hours":8,"phase_code":"32"}' | python -c 'import sys,json;print(json.load(sys.stdin)["task"]["id"])')
T3=$(post_auth "$API/projects/CN-LUTRY-2026/tasks" '{"title":"Plans facades + coupes echelle 1/100","priority":"p1","estimate_hours":16,"phase_code":"32"}' | python -c 'import sys,json;print(json.load(sys.stdin)["task"]["id"])')
T4=$(post_auth "$API/projects/CN-LUTRY-2026/tasks" '{"title":"Recolte donnees thermicienne","priority":"p2","estimate_hours":2,"is_quick_win":true,"phase_code":"32"}' | python -c 'import sys,json;print(json.load(sys.stdin)["task"]["id"])')
T5=$(post_auth "$API/projects/CN-LUTRY-2026/tasks" '{"title":"Releve geometre (validations alignements)","priority":"p1","estimate_hours":6,"phase_code":"32"}' | python -c 'import sys,json;print(json.load(sys.stdin)["task"]["id"])')
# Permis depends on plans + structure --illustrates "bloquants" navigation
post_auth "$API/projects/CN-LUTRY-2026/tasks/$T1/deps" "{\"blocked_by_id\":$T2}" > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/tasks/$T1/deps" "{\"blocked_by_id\":$T3}" > /dev/null
# One completed task with actual_hours = 3x estimate (Pareto/Murphy)
T_DONE=$(post_auth "$API/projects/CN-LUTRY-2026/tasks" '{"title":"Faisabilite + cahier des charges","priority":"p1","estimate_hours":12,"phase_code":"21"}' | python -c 'import sys,json;print(json.load(sys.stdin)["task"]["id"])')
curl -fsS -X PATCH "$API/projects/CN-LUTRY-2026/tasks/$T_DONE" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" --data-binary '{"status":"done","actual_hours":34}' > /dev/null

# 7) Captures --friction + photo with measurements + regulation alert (Etienne's words [42:42])
post_auth "$API/projects/CN-LUTRY-2026/captures" '{"kind":"friction","content":"Le client a change davis sur la cuisine (3eme version) --risque de derive budget."}' > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/captures" '{"kind":"photo","content":"Fissure mur nord --longueur 15cm, largeur 2mm. Suivi mensuel.","source_ref":"photo_2026-06-01.jpg"}' > /dev/null
post_auth "$API/projects/CN-LUTRY-2026/captures" '{"kind":"regulation","content":"Reglement communal Lutry --revision PGA en cours, decision attendue Q3 2026. Hauteurs corniche susceptibles dabaissement de 1m."}' > /dev/null

# 8) Pre-generate the invites for the MO + the engineer (codes to print and hand to Etienne)
INV_MO=$(post_auth "$API/projects/CN-LUTRY-2026/intervenants/$IV_MO/invite" '{"email":"famille.bourg@example.org","name":"M. & Mme Bourg-Pellet"}' | python -c 'import sys,json;print(json.load(sys.stdin)["invite_token"])')
INV_CIV=$(post_auth "$API/projects/CN-LUTRY-2026/intervenants/$IV_CIV/invite" '{"email":"a.civilis@civilis.ch","name":"Anne Civilis"}' | python -c 'import sys,json;print(json.load(sys.stdin)["invite_token"])')

# 9) Print credentials (these end up in the printed manual addendum)
cat <<TXT
=================== ATELIER CARRE-NEUF · AEDIFICA ===================
URL              : $BASE/workspace
Architect login  : etienne@carre-neuf.ch / carre-neuf-2026
Project          : Rehabilitation Bourg-Dessus, Lutry  (id: CN-LUTRY-2026)
Owner API token  : $TOK
Client invite    : $INV_MO    (M. & Mme Bourg-Pellet)
Engineer invite  : $INV_CIV    (Anne Civilis, ingenieure civile)
====================================================================
TXT
