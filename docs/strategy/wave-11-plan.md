# Wave 11 — plan consolidé d'exécution

> Document vivant. Consolide **tous** les retours du propriétaire (session du
> 2026-06-06 sur la démo Etienne + audit visuel Playwright) et impose une
> exécution **par tranches courtes et shippables**, chaque tranche aboutissant
> à un PR + déploiement Fly + vérification visuelle. Plus de polish-sans-câblage.

## 0 · Garde-fous

- **Plus aucun bouton sans handler vérifié end-to-end.**
- **Plus aucun gabarit statique passé pour du dynamique** — les compteurs / les
  *prochain pas* / les chips doivent refléter l'état réel du projet.
- **Tout PR a un audit visuel** (Playwright traverse les 18 surfaces et
  commit les captures dans `docs/audit/<wave>/`).
- **L'identité Datum est la loi** : sprite officiel, fontes officielles,
  composants Wordmark/Monogram. Plus de SVG inline maison ni de classe `.wm`.

## 1 · Inventaire complet à traiter

### A — Cohérence des données affichées **(quick wins, P0)**
- `phase_code = 0` provoque un `indexOf(...) = 0` → la rail allume *11
  OBJECTIFS* et la carte projet titre *« Phase 11 »*. Faux.
- *« Prochain pas »* renvoie systématiquement des actions phase 33 (4 docs
  permis) même quand le projet est à phase 0/11/21. Algo backend
  `/next-step` indépendant de `phase_code` réel.
- Caractères parasites `�` dans les seeds Etienne (apostrophes
  Unicode mal encodées) qui apparaissent dans Mémoire et Captures.
- Page d'accueil affiche un dossier *« 8 pièces manquantes »* pour des
  projets vides (compteur du gabarit, pas l'état réel).
- `À valider` affiche *« 50 step(s) à faire · 5 rétroactif »* sur un
  projet à phase 0 — chiffres réels mais formulation qui paraît figée.

### B — Pièces jointes partout **(structurel, P1)**
- Aucun endroit dans l'app pour **uploader** un document ou **pointer
  vers un lien externe** (Drive, OneDrive, Dropbox, intranet atelier).
- Doctrine confirmée : Aedifica = index + droits + traçabilité, **pas
  un Dropbox bis**.
- Cibles : Documents · BRS · Permis · Mémoire · Checklist · Tâches.
- Plans architecturaux = gros fichiers ⇒ mode *« lien »* par défaut,
  upload local optionnel plafonné à 25 Mo.

### C — Vraie gestion de projet **(structurel, P2)**
- Tâches/priorités P0/P1/P2 + dépendances : OK pour la navigation par
  bloquant. Manque : **Gantt** + **Kanban** + vue calendrier.
- **Ne pas réinventer la roue** : intégrer `frappe-gantt` (MIT, ~50 ko,
  vanilla JS, drag des barres natif). Kanban : composant maison
  (< 200 lignes, 4 colonnes todo/doing/done/blocked, drag minimal).

### D — Surfaces ambiguës à clarifier **(P3)**
- **Mémoire** doit être un journal automatique (ledger + unknowns +
  captures système), pas une zone de saisie manuelle. Repositionner la
  capture rapide en onglet secondaire.
- **Copilote IA** : opération `AC-SPACE-101 → "bureau"` hardcodée
  (audit confirme). Soit (a) brancher l'Archicad live + sélecteur d'opérations
  (b) cacher derrière un flag `LIVE_ARCHICAD_OK` avec un état vide
  honnête.
- **Coordination** : presentation pass — micro-icônes par acteur,
  bouton vers la surface concernée sur chaque cadran.
- **Tableau de bord — Prochain pas** : ré-aligner l'algo backend
  `/next-step` sur `project.phase_code`.

### E — Identité jusqu'au bout **(P0 + complément)**
- Wordmark officielle, polices Space Grotesk + IBM Plex Mono, tailles
  correctes — **fait** dans la dernière PR.
- Sprite Datum mappé à NAV — **fait** en W11 P0.
- À faire : utilisation des **datum-marks** (`ic-datum-target`,
  `ic-datum-dimension`, `ic-datum-north`) dans des contextes
  pertinents (orientation, mesures, intake) — pas seulement le menu.
- Auditer chaque libellé / chip pour s'assurer qu'on n'utilise pas
  d'emoji.

### F — AAA **(P4)**
- Audit log des accès et mutations sensibles (ledger existe, à
  étendre aux invitations + révocations + scope d'accès).
- Rotation des tokens API + révocation des invitations.
- Scoping fin par rôle (external = vue scopée uniquement à son
  intervenant).

## 2 · Ordre d'exécution (1 tranche = 1 PR = 1 déploiement)

| PR / Tranche | Thème | Durée | Pré-requis |
|---|---|---|---|
| **W11.A** (cette PR) | **Cohérence** des données (phase_code, prochain pas, encoding) | 1-2 h | aucun |
| **W11.B** | **Attachments** : modèle + upload + lien externe + UI partout | 4-6 h | W11.A |
| **W11.C** | **Gantt + Kanban** (frappe-gantt + composant maison) | 3-4 h | W11.B (les tâches portent les attachments) |
| **W11.D** | **Mémoire / Copilote / Coordination** — refonte clarification | 2-3 h | W11.A |
| **W11.E** | **Identité fin** — datum-marks + audit libellés + datum-stamps cohérents | 1-2 h | W11.A |
| **W11.F** | **AAA** — audit log + rotation + scoping | 2-3 h | W11.B |

## 3 · Méthode par tranche

Chaque tranche suit le même pipeline (pas de raccourci) :

1. **Implémentation** (backend + frontend) avec tests product.
2. **Build + tests locaux verts** (68+ tests product).
3. **Audit visuel Playwright** (les captures avant/après dans
   `docs/audit/wave-11-X/`) pour confirmer que ce que je dis correspond
   à ce qu'on voit à l'écran.
4. **PR** avec description complète, captures comparatives.
5. **CI 5/5 verte**.
6. **Merge** + **déploiement Fly**.
7. **Re-audit visuel sur prod** pour confirmation finale.
8. **Tâche TaskList marquée done** + état du plan mis à jour ici.

## 4 · Tranche A — cohérence des données *(exécution maintenant)*

### A.1 — Phase rail / project card / dashboard cohérents avec `phase_code`
- Backend : si `phase_code = "0"` (jamais initialisé), renvoyer un
  marqueur clair côté API (`phase_label = "Pas démarré"`) ; les routes
  `/coordination`, `/checklist`, `/next-step` doivent ignorer la phase
  par défaut.
- Frontend : ne plus retomber sur `PHASES[0]` quand `phase_code` est
  `"0"` ou inconnu. Afficher *« Phase de cadrage à définir »*.
- Phase rail : pas d'item highlighté si non démarré, **bouton dédié
  *« Démarrer · phase 1 »***.

### A.2 — Algo `/next-step` ré-aligné sur `phase_code`
- Backend : `next-step` retourne les bons items selon la phase
  courante (phase 0/11 → setup objectifs ; 21 → faisabilité ; 32 →
  développement projet…).
- Test : changer la phase via la rail → `next-step` change.

### A.3 — Encoding seed
- Re-encoder le seed Etienne en ASCII pur (apostrophes ASCII, pas
  Unicode dangereux). Wipe + re-seed sur Fly.

### A.4 — Carte projet du Home
- N'affiche la phase que si réellement définie. Sinon : *« À cadrer »*.

### A.5 — Compteur *« À valider »*
- Si checklist non seedée → masquer le bloc ou afficher *« Initialiser
  la checklist »* avec un CTA.

## 5 · Suivi des PRs

| PR | Tranche | État | Lien |
|---|---|---|---|
| #239 | W11 P0 (W11 historique) | ✅ mergé | … |
| #240 | wordmark + fontes + tailles | ✅ mergé | … |
| (next) | **W11.A — cohérence** | 🔄 en cours | — |
| — | W11.B — attachments | planifié | — |
| — | W11.C — Gantt + Kanban | planifié | — |
| — | W11.D — refontes Mémoire/Copilote/Coordination | planifié | — |
| — | W11.E — identité fin | planifié | — |
| — | W11.F — AAA | planifié | — |
