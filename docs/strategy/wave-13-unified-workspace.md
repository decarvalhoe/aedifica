# Wave 13 — Workspace unifié (no more intermediate page after login)

## Problème observé

Après login, l'utilisateur tombe sur une **page intermédiaire bloquante** disconnectée du reste :
- un grand bloc « Un appui concret… » avec recherche de parcelle (doublon de Terrain & zonage)
- un encart « Présentation faisabilité » qui ressemble à une page marketing
- la liste des projets en cards
- l'équipe en lecture seule
- l'AtelierPilotage (Gantt/Kanban multi-projet) caché en bas

Quand on clique sur un projet, on entre dans une **autre** vue (sidebar + main) avec navigation par fonctionnalité. Le contraste UX est brutal : deux applications cousues ensemble.

## Doctrine

- **Une seule surface après login.** Le workspace est l'application ; la « page projets » n'existe pas.
- **Sélecteur de projet intégré au workspace.** Dans la sidebar, là où se trouve déjà la carte du projet courant, un popover s'ouvre avec la liste + création.
- **Multi-projet accessible depuis n'importe où.** L'AtelierPilotage (Gantt/Kanban multi-projet) + Équipe vivent dans un groupe « Atelier · global » du nav, toujours visible.
- **Empty-state inline.** Aucun écran d'accueil ; si zéro projet, le main affiche un formulaire de création directement.

## État de l'art (UX pattern)

Référents étudiés : **Notion** (workspace switcher coin haut-gauche → popover), **Linear** (project picker dans la nav → search + create), **Figma** (file switcher inline), **Jira** (project dropdown avec recherche), **Slack** (workspace rail).

**Pattern retenu** :
1. Top de la sidebar : un **bouton-carte** affichant le projet courant (nom gras + chip phase + commune en gris). Caret à droite.
2. Click → **popover** descend, contenant :
   - Projet courant en haut avec ✓
   - Liste des autres projets (nom + phase + commune)
   - Search field si > 5 projets
   - Séparateur
   - **+ Nouveau projet** : ouvre un formulaire inline (nom + commune) dans le popover
3. Esc / click outside → fermeture.
4. Clavier : ↑↓ pour naviguer, Enter pour sélectionner, `/` ou typing pour focus search.

## Reorg du NAV

Aujourd'hui :
```
Pilotage          dashboard, foresight, taches, checklist, terrain, copilote, memoire
Coordination      coordination, intervenants, documents, brs
Dossier régl.     permis, opposition, conformite
Économie & chantier  couts, chantier
Atelier           equipe
```

W13 :
```
Pilotage             [inchangé — per-project]
Coordination         [inchangé — per-project]
Dossier régl.        [inchangé — per-project]
Économie & chantier  [inchangé — per-project]
Atelier · global     atelier (Gantt/Kanban multi-projet), equipe
```

Le groupe « Atelier · global » est **toujours actif** indépendamment du projet courant. Cliquer dessus ne change pas `active`, mais montre la vue agrégée.

## Empty-state (0 projet)

- Sidebar : project switcher en mode « Aucun projet » + groupe Atelier · global accessible
- Main : carte centrée avec
  - Titre : « Créer votre premier projet »
  - Form inline (nom + commune)
  - Bouton primaire
- Pas de redirection, pas d'écran d'accueil

## Auto-sélection au load

- Si `localStorage.lastProjectId` existe et le projet est dans la liste → l'activer
- Sinon, sélectionner le projet le plus récemment créé (ou modifié)
- Persiste `localStorage.lastProjectId` à chaque changement de projet

## Tranches

- [ ] **W13.A** — ProjectSwitcher (popover + search + inline create) + reorg NAV (Atelier · global)
- [ ] **W13.B** — Routing : skip Home, auto-select project, empty-state inline
- [ ] **W13.C** — Extraction d'AtelierPilotage en vue indépendante (`view === "atelier"`)
- [ ] **W13.D** — CSS Datum-cohérent pour le popover switcher
- [ ] **W13.E** — Tests E2E mis à jour + visual audit + deploy

Doctrine garde-fou : pour ne pas casser la démo seedée d'Etienne, le projet « Place de la Palud » reste auto-sélectionné par défaut. La création de projet reste accessible via le switcher en un clic.
