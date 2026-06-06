# Wave 15 — Épuisement des issues restantes

## Reliquats du retour W13 non traités explicitement

- **Foresight** : le user a dit « il y a un truc que je n'aime pas dans cette page » sans préciser. Probablement la densité verticale + la carte des propositions trop bruyante.
- **Kanban** : « pareil, ça ne va pas du tout ». Aucun travail dessus jusqu'ici (Gantt a été refait W14.C.3, pas le Kanban).

## Endpoints sans UI

- `POST /api/auth/me/rotate-token` (W11.F) — pas de bouton dans l'app
- `POST /api/auth/me/revoke-token` (W11.F) — pas de bouton dans l'app
- `PATCH /api/projects/{pid}/llm-mode` (W12.C) — pas de switch
- `POST /api/orgs/benchmark/snapshot` (W12.E) — pas de bouton
- `GET /api/orgs/benchmark` (W12.E) — pas de surface de visualisation
- `GET /api/orgs/audit` (W11.F) — pas de surface

## Reste à faire

### W15.A — Kanban scalable + Foresight UX polish
- Kanban : recherche/filtre, project chip inline, density toggle, empty-states par colonne, KPI strip
- Foresight : layout de carte plus calme, regroupement par type, confidence inline pas en pastille à part

### W15.B — Surface « Compte & atelier »
- Nouveau groupe nav « Réglages » avec :
  - Compte (rotate-token, revoke-token, change-password)
  - LLM par projet (toggle off/local/cloud)
  - Benchmark atelier (liste snapshots + bouton « Geler maintenant »)
  - Journal de sécurité (audit log)

### W15.C — Visual audit Playwright
- Capture des 20 surfaces + screenshots commit dans `docs/audit/wave-15/`
- Fix tout bug de layout repéré

### W15.D — Mobile responsive
- Sidebar drawer < 900px
- Phase rail scroll horizontal
- Tableaux empilent en cards

### W15.E — Documentation Archicad bridge
- `docs/integrations/archicad-bridge.md` avec installation + endpoints

## Doctrine maintenue

Tout reste pur soft. Aucun nouvel engine. Just câbler ce qui existe + corriger ce qui frotte.
