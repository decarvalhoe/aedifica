#!/bin/bash
# Seed an Aedifica demo on the given base URL (e.g. https://aedifica-demo.fly.dev).
# Idempotent-ish: returns the owner token + two invite tokens. Re-running creates
# duplicate intervenants — drop the volume to start over.
#
# Usage: scripts/seed-demo.sh https://aedifica-demo.fly.dev
set -e
BASE="${1:?usage: $0 <base-url>}"
API="${BASE%/}/api"

post() { curl -fsS -X POST "$1" -H 'Content-Type: application/json' --data-binary "$2" ; }
post_auth() { curl -fsS -X POST "$1" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" --data-binary "$2" ; }
patch_auth() { curl -fsS -X PATCH "$1" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" --data-binary "$2" ; }

# 1) Org + owner
R=$(post "$API/orgs" '{"org_name":"Atelier demo W10","user_email":"demo@aedifica.ch","password":"demo123"}')
TOK=$(echo "$R" | python -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# 2) Project, seeded at phase 21 (so phase 11 is retroactive — external blocker on the MO)
post_auth "$API/projects" '{"project_id":"DEMO-W10","name":"Maison Etienne - demo W10","commune":"Lausanne"}' > /dev/null
post_auth "$API/projects/DEMO-W10/checklist/seed" '{"entry_phase":"21"}' > /dev/null

# 3) A pending document to feed the validation queue
post_auth "$API/projects/DEMO-W10/documents" '{"official_name":"Permis CAMAC 2025-1234 (a valider)","category":"permit"}' > /dev/null

# 4) Client (MO) + invitation
IV=$(post_auth "$API/projects/DEMO-W10/intervenants" '{"name":"M. & Mme Client","role":"maitre de louvrage","email":"client@example.org"}' | python -c 'import sys,json;print(json.load(sys.stdin)["intervenant"]["id"])')
INV=$(post_auth "$API/projects/DEMO-W10/intervenants/$IV/invite" '{"email":"client@example.org","name":"M. & Mme Client"}')
CLIENT_TOKEN=$(echo "$INV" | python -c 'import sys,json;print(json.load(sys.stdin)["invite_token"])')

# 5) Engineer group + mandataire + access grant on a plan
G=$(post_auth "$API/projects/DEMO-W10/intervenant-groups" '{"name":"Ingenieurs","kind":"discipline"}' | python -c 'import sys,json;print(json.load(sys.stdin)["group"]["id"])')
IV2=$(post_auth "$API/projects/DEMO-W10/intervenants" "{\"name\":\"A. Civilis\",\"role\":\"ingenieur civil\",\"organization\":\"Civil SA\",\"email\":\"a@civilis.ch\",\"group_id\":$G}" | python -c 'import sys,json;print(json.load(sys.stdin)["intervenant"]["id"])')
D2=$(post_auth "$API/projects/DEMO-W10/documents" '{"official_name":"Plans structure v3 (a jour)","category":"plan"}' | python -c 'import sys,json;print(json.load(sys.stdin)["document"]["id"])')
post_auth "$API/projects/DEMO-W10/documents/$D2/grants" "{\"group_id\":$G,\"level\":\"read\"}" > /dev/null
INV2=$(post_auth "$API/projects/DEMO-W10/intervenants/$IV2/invite" '{"email":"a@civilis.ch","name":"A. Civilis"}')
MANDATAIRE_TOKEN=$(echo "$INV2" | python -c 'import sys,json;print(json.load(sys.stdin)["invite_token"])')

echo "=================== AEDIFICA DEMO ==================="
echo "URL              : $BASE/workspace"
echo "Architect login  : demo@aedifica.ch / demo123"
echo "Owner API token  : $TOK"
echo "Client invite    : $CLIENT_TOKEN"
echo "Engineer invite  : $MANDATAIRE_TOKEN"
echo "====================================================="
