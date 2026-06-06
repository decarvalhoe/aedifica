# Wave 11 — Audit critique & plan d'exécution

> Source : retours du propriétaire (2026-06-06, après livraison W10 sur Fly + manuel
> Etienne). Audit code conduit en parallèle pour confirmer/élargir chaque point.
> Cadre : **ne plus livrer de surface visuellement polie mais câblée à rien**.

## 1 · Tout ce qui a été remonté

### A · Identité graphique — assets officiels inutilisés
- Aucun **favicon** officiel — l'app sert le favicon Next.js par défaut.
- **Monogramme** Aedifica (`logo-aedifica-monogram.svg`) jamais rendu.
- **Sprite officiel** des 22 icônes (`functional-icons.svg`) ignoré : l'app utilise 8 SVG
  custom inline qui ne respectent ni la grille 24 px, ni l'épaisseur 1.5 px, ni les caps
  carrés du design system.
- **Datum-marks** (`ic-datum-target`, `ic-datum-dimension`, `ic-datum-north`) — jamais
  utilisés alors qu'ils portent la *langue de dessin* architecturale.
- Glyphes utilisés **ne sont pas issus du sprite officiel**.

### B · Bugs visibles confirmés par l'audit
- **Phase rail SIA** (barre du haut) : pas cliquable, pas câblée. Aucun handler. C'est
  pourtant le premier endroit où on s'attend à pouvoir naviguer par phase et voir *« ce
  qui s'y passe »*.
- **Checklist** : boutons de tri par acteur = row de 5 toggles (peu élégant), à remplacer
  par un dropdown. Les statuts *« Plus tard »* / *« Inutile »* PATCH bien (vérifié), mais
  le feedback visuel est minimal — la pastille change discrètement et le step reste à la
  même place ; perception = *« ça ne fait rien »*.
- **Tableau de bord — Prochain pas** : la liste vient bien de `/projects/{id}/next-step`,
  mais l'algorithme renvoie des steps **non-corrélés à la phase réelle du projet**.
  Au mieux, c'est mal pondéré ; à vérifier surface par surface.

### C · Surfaces partiellement câblées / floues
- **Copilote IA** : opération hardcodée `AC-SPACE-101 → "bureau"` (ligne 696). UX zéro
  indication d'usage, ressenti = surface fake. À refondre ou cacher derrière un flag.
- **Mémoire** : conçue comme journal automatique (ledger + unknowns + captures), mais
  perçue comme zone de saisie manuelle car la capture utilisateur prend toute la place.
  Le purpose initial doit être réaffirmé OU la surface revue.
- **Terrain & zonage — *« Demander l'ingestion »*** : POST `/communes` réussit mais aucun
  retour utilisateur visible (le bouton ne tigge pas de banner, et l'utilisateur reste
  sur la même page sans signal). Le mécanisme existe mais le feedback est cassé.
- **Coordination** : 4 cadrans fonctionnels mais présentation à reprendre — sensation de
  *« bâclé »*.

### D · Manque structurel — gestion documentaire
- **Aucun mécanisme d'upload** dans toute l'app. La création de document accepte un
  `file_ref` (string) mais pas de fichier réel — aucun stockage.
- **Aucun lien externe** non plus (Drive, OneDrive, Dropbox, intranet atelier…).
- Présent dans : Checklist · BRS · Documents & sources · Permis · Mémoire · Tâches.
  Tous les domaines fonctionnels demandent à pointer vers des documents — actuellement
  impossible.
- **Doctrine validée par l'utilisateur** : ne PAS proposer un hébergement Aedifica.
  Intégrer les hébergements des ateliers **flexiblement** — soit upload local, soit lien
  externe avec gestion des permissions à l'extérieur.
- Documents architecturaux = **plans lourds** : il faut un mode *« lien vers la source »*
  par défaut, upload pour les petits volumes seulement.

### E · Manque structurel — gestion de projet (Gantt + Agile)
- Tâches + priorités P0/P1/P2 + dépendances : OK pour la navigation par bloquant.
- **Manque** : vue *Gantt* (timeline + barres + dépendances), vue *Kanban* (tableau
  agile par statut), vue *Calendrier* (gros plan sur la semaine/mois).
- **Doctrine validée par l'utilisateur** : **ne pas réinventer la roue** — intégrer une
  librairie OSS reconnue.
- Candidats : **frappe-gantt** (MIT, vanilla JS, léger, ~50 ko), **dhtmlx-gantt** (GPL),
  ou un composant React minimal au-dessus de SVG.
- Recommandation : **frappe-gantt** + un composant Kanban maison (simple, < 200 lignes).

### F · Authentification / autorisation
- Intervenants : registre fonctionnel ; on peut inviter en `external`.
- Manque (suggestion du propriétaire) : usage *AAA* (Authentication, Authorization,
  Accounting). En pratique pour Aedifica : audit log des accès, rotation token, scoping
  plus fin. À cadrer.

---

## 2 · Roadmap exécutable

### W11 · P0 — Identité + wirings critiques *(cette PR)*
1. **Sprite officiel + assets identité** dans `web/public/assets/`.
2. **Favicon** Aedifica (le svg du DS) + métadonnées dans `layout.tsx`.
3. **Monogramme** sur le header workspace + login.
4. **Refonte du composant `Icon`** : référence au sprite via `<use>`. Mapping NAV → IDs
   officiels (`ic-portfolio`, `ic-parcel`, `ic-permit`, `ic-opposition`, etc.).
5. **Phase rail cliquable** : PATCH `/projects/{id}` ajout `phase_code` (si manquant)
   + handler `onClick` sur chaque phase pour basculer le projet.
6. **Checklist : filtres acteur → dropdown** unique au lieu de la row de toggles.
7. **Feedback PATCH visible** sur les actions checklist : la ligne disparaît si statut
   ≠ "todo" et est filtrée par défaut sur "à faire", avec un toggle *« voir tout »*.
8. **Terrain — ingestion demandée** : banner success/error explicit + redirection sur
   *Atelier* quand la commune est en attente.

### W11 · P1 — Pièces jointes partout *(PR séparée)*
9. **Modèle `Attachment`** : `(project, owner_kind, owner_id, kind: upload|link,
   url|file_ref, provider: local|gdrive|onedrive|dropbox|other, sha256, size)`.
10. **Endpoint `POST /api/projects/{id}/attachments`** (multipart pour upload, JSON pour
    lien). **Endpoint `DELETE`**. **Endpoint `GET`** scoped au owner.
11. **UI** : composant `AttachField` réutilisable. Intégré dans Documents, BRS, Permis,
    Mémoire, Checklist, Tâches. Mode par défaut = *lien*, upload en option (cap 25 Mo).
12. **Stockage** : sur Fly, FS éphémère par défaut + recommandation de déléguer au
    cloud du client (Drive/OneDrive). Pas d'objet store au début.

### W11 · P2 — Vues projet (Gantt + Kanban) *(PR séparée)*
13. **Intégration frappe-gantt** sous une nouvelle nav *Pilotage → Planning*. Tasks
    déjà persistées → barres Gantt. Drag pour déplacer.
14. **Kanban** : composant maison, colonnes todo/doing/done/blocked, drag minimal.
15. **Bascule de vue** dans *Tâches & priorités* : liste · Kanban · Gantt.

### W11 · P3 — Clarification surfaces ambiguës *(PR séparée)*
16. **Copilote IA** : soit (a) finir le câblage live Archicad + ajouter un sélecteur
    d'opération (b) cacher la surface derrière un flag `LIVE_ARCHICAD_OK`.
17. **Mémoire** : repositionner comme *journal* (ledger + unknowns + captures) avec un
    onglet *Auto* / *Manuel* distinct.
18. **Coordination** : refonte présentation (grouping plus net, micro-icônes de bloquant,
    bouton vers la surface correspondante).
19. **Dashboard — Prochain pas** : auditer l'algo backend et ré-aligner avec
    `project.phase_code`.

### W11 · P4 — AAA *(PR séparée)*
20. **Audit log** des accès / mutations sensibles (ledger existe déjà, à étendre).
21. **Rotation token** + révocation invitations.

---

## 3 · Garde-fous renouvelés

- **Plus aucune surface poussée en prod sans câblage end-to-end vérifié**.
- **Aucun nouveau bouton sans handler câblé**.
- **Identité = Datum DS, point**. Plus de SVG custom inline ; tout passe par le sprite
  officiel.
- **Feedback utilisateur explicite** sur chaque action mutative (banner / toast / ligne
  qui change).
- **Documents** : reconnaître que l'atelier a déjà son stockage. Aedifica est l'index +
  les droits d'accès + la traçabilité, pas un Dropbox bis.
- **Project management** : ne pas réinventer. Intégrer.

---

## 4 · Suivi PR

| PR | Wave | Contenu | Statut |
|---|---|---|---|
| #239 | W11 P0 | Identité + phase rail + filtre dropdown + feedback | en cours |
| à venir | W11 P1 | Pièces jointes (upload + lien) partout | planifié |
| à venir | W11 P2 | Gantt frappe + Kanban | planifié |
| à venir | W11 P3 | Mémoire / Copilote / Coordination / Prochain pas | planifié |
| à venir | W11 P4 | AAA | planifié |
