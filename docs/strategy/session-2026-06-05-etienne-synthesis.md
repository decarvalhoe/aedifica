# Séance Etienne Piergiovanni — synthèse & plan d'intégration

> **Statut : synthèse de la séance de travail du 2026-06-05** avec l'architecte
> partenaire **Etienne Piergiovanni**, premier retour terrain sur l'app redressée.
> **Sources :** 4 pages de notes manuscrites + la feuille de route SIA (section Vaud)
> + l'enregistrement audio de la séance (47 min, transcrit **en local sur GPU**,
> faster-whisper large-v3-turbo).
> **Confidentialité :** l'audio et le transcript brut contiennent des propos privés
> → **non versionnés** (gardés hors du repo, cf. principe LPD ci-dessous). Ce
> document ne retient que la matière produit.

---

## 1 · L'insight central

La séance ne porte presque pas sur de **nouvelles capacités par phase** — celles-ci
sont déjà cataloguées dans [`phase-value-catalog.md`](phase-value-catalog.md). Elle
décrit la **couche d'exploitation / de gouvernance** qui rend ces capacités
utilisables dans un vrai atelier. C'est **le « OS » d'ArchiOS**, au-dessus de
l'intelligence par phase.

Les mots d'Etienne (le cœur de la valeur, verbatim) :

> « le réel intérêt… c'est cette **centralisation**, cette interface qui te permet
> d'accéder, de **trier les choses, les retrouver, les transmettre**. Avec quelque
> chose d'ultra carré. […] on est complètement en dehors de tout ce qui serait
> création, dessin — **mais c'est tout autant important. C'est là où je suis le plus
> mauvais.** »

→ **trier · retrouver · transmettre** (= la note « trier / trouver / transmettre »)
est la colonne vertébrale. Le dessin n'est pas le sujet ; l'**organisation, la
coordination et la traçabilité** le sont — exactement ce que `architect-reality.md`
§6 identifie comme la valeur défendable (« decisional/contractual traceability »).

Deux couches complémentaires :

| Couche | Ce que c'est | Où c'est documenté |
|---|---|---|
| **Intelligence par phase** | *Ce que* fait Aedifica à chaque étape SIA (parcelle→contraintes, opposition, permis, coûts…) | `phase-value-catalog.md` (déjà livré en grande partie) |
| **Couche d'exploitation** ← *cette séance* | *Comment* le projet et l'atelier sont gouvernés à travers les phases (intervenants, accès, checklist, validation, calendrier multi-projet) | ce document |

---

## 2 · Décodage thématique (notes ⨯ audio)

Chaque thème : la **note**, ce qu'**a dit Etienne**, le **sens produit**.

### A · Intervenants & gestion d'accès documentaire  *(le 1er sujet de la séance)*
- **Notes :** « Intervenant (groupe / personne) avec gestion d'accès documentaire » ;
  « Mandataire / Document à jour / Plan etc » ; « Procès-Verbaux ».
- **Audio :** on saisit les intervenants au fur et à mesure ; chaque intervenant
  ajouté **crée sa "case"**. Chaque document posé reçoit **un niveau d'accès**.
  Danger explicite : *ne pas* donner accès à trop de documents à des gens qui n'en
  ont pas besoin (ils se perdent, ou c'est confidentiel). **Arborescence des acteurs** :
  groupes ⊃ sous-groupes (ex. « groupe ingénieur » → civil / électrique ; base
  commune + documents spécifiques par sous-groupe) jusqu'à **la personne seule**
  (le mail du contremaître vs « Manolo » qui ne lit pas ses mails). En créant la
  liste, **sourcer directement les contacts** (référence, responsable).
- **Sens produit :** un **registre d'intervenants** (groupes/personnes, contacts,
  responsables) + un **contrôle d'accès par document/dossier** par intervenant. Relie
  `architect-reality.md` §2 : l'architecte coordonne **6–10 disciplines responsables**,
  et « le produit, c'est de cadrer les interfaces de responsabilité — qui doit quoi,
  quand, sur quelle base ».

### B · Annuaire réutilisable
- **Notes :** « annuaire ».
- **Audio :** « ça pourrait alimenter une forme d'**annuaire** que tu récupères d'un
  projet à l'autre — on bosse souvent avec le même genre ».
- **Sens produit :** un **annuaire au niveau atelier** (les intervenants saisis dans un
  projet deviennent réutilisables) — niveau organisation, pas seulement projet.

### C · Embarquement à n'importe quelle phase + checklist rétroactive
- **Notes :** « Par module · Projet doit être rejoint à n'importe quelle phase · avec
  checklist rétroactive ».
- **Audio :** « la réalité du terrain a ce côté chaotique, tu ne fais pas selon le
  manuel → **un projet doit pouvoir être rejoint à n'importe quelle phase**. » Si tu
  rejoins à la phase permis, il faut **une checklist rétroactive du passé**. Si tu
  démarres à un point ≠ zéro, tu as déjà la documentation pour **renseigner les points
  précédents**.
- **Sens produit :** la phase d'entrée d'un projet est **paramétrable** ; l'app
  **reconstruit une checklist rétroactive** des livrables des phases antérieures.

### D · La checklist SIA « déjà écrite » + validation des steps réels
- **Notes :** « Step de base cohérent · Phase prochaine avec validation » ;
  « Gestion checklist ».
- **Audio :** la liste de tâches « est **quasi écrite ici** — la SIA décrit tout, tu as
  des coches à mettre ; **déjà classée dans l'ordre**, structure cohérente, excellente
  base ». Mais **à la création du projet tu fais une phase de validation** : « cette
  phase on la fait / cette phase on ne la fait pas (pas de sens) » ; chaque item peut
  être *à faire plus tard*, *inutile / non nécessaire dans ce projet*. **Pas de message
  d'erreur** si un step non pertinent n'est pas fait.
- **Sens produit :** un **gabarit de checklist dérivé de la SIA**, par phase, que
  l'atelier **active/désactive/diffère** à l'ouverture → la liste des *steps réels* du
  projet. (La feuille SIA Vaud fournie = la source de ce gabarit, cf. §5.)

### E · Sourçage canonique manuel + 3 niveaux de validation
- **Notes :** « Sourçage canonique manuel par l'atelier » ; « Source importée en local
  + versioning → la réf du doc, nom du doc officiel » ; « Validation des documents
  retenus par l'archi maître » ; « **3 niv : Canonique / Indicatif / Refusé** ».
- **Audio :** l'IA propose des sources (tu valides), **mais** tu dois aussi pouvoir
  **lui injecter une source manuellement** : ex. un permis reçu (fait par d'autres,
  que tu as modifié) — *introuvable sur le net, « c'est moi qui l'ai »*. Dans Terrain &
  Zonage, les documents collectés doivent être triables : **canonique / indicatif /
  refusé**. Au-delà des docs officiels : **documents clients, confidentiels**.
- **Sens produit :** un **module Documents/Sources** : import local + versioning + nom
  officiel ; **workflow de validation à 3 niveaux** (canonique/indicatif/refusé) **par
  l'architecte maître**. Étend le modèle de confiance existant
  (`sourced/computed/assumption/unknown/conflict/decision`) d'une **couche de curation
  humaine**.

### F · Documents confidentiels — LPD
- **Notes :** « document confidentiel à traiter avec la **LPD** » *(noté « LAPD » → 
  confirmé à l'audio : « selon la loi… la LPD »)*.
- **Audio :** « assurer que les documents confidentiels soient **traités comme
  confidentiels selon la loi** ».
- **Sens produit :** marquage **confidentiel** d'un document + traçabilité d'accès
  conforme **LPD** (Loi fédérale sur la Protection des Données). C'est une **exigence**,
  pas une option.

### G · Base vivante de référence (« verrou / source », PV + appels)
- **Notes :** « Verrou de **BRS** / Source de **BRS** · **PV + coup de tél** · **Base
  vivante de référence** versionnée · Responsable · contact · annuaire ».
- **Audio :** centralisation des **plans à jour**, **procès-verbaux de séance**, tout
  document officiel, accessible par le maître d'ouvrage / les mandataires ; une base
  **versionnée** avec **responsable** et **contacts**.
- **Sens produit :** une **base de référence vivante, versionnée, verrouillable**
  (source figée = « canonique »), avec un **responsable** par entrée, qui capte aussi
  l'**informel** (PV de séance, décisions prises par téléphone). Étend la **Mémoire**
  actuelle (inconnues + journal).
  > ⚠️ **À confirmer avec Etienne : le sigle « BRS ».** Le concept est clair (base de
  > référence sourcée, verrouillée/versionnée) ; l'acronyme exact n'est pas prononcé à
  > l'audio. → question ouverte §9.

### H · Calendrier multi-projet, prédictif & collisions  *(le besoin n°1 d'Etienne)*
- **Notes :** « Calendrier / Gantt / agile · **niveau Atelier multiprojet** ·
  **predictive** · **Collision Interprojet (IA)** · **Gestion de Coût Prédictif** ».
- **Audio (longuement, c'est SON point) :** « c'est un métier d'être chef de projet
  d'utiliser ses outils Gantt… **mais c'est totalement automatisable. J'ai essayé sur
  Excel, jamais réussi.** » Le problème **n'est pas un projet, c'est le calendrier de
  TOUS les projets**. « Je me plante à chaque fois sur le temps, ça me prend toujours 3×
  plus » → un facteur de **pondération** appris. L'app doit **alerter** : « fais
  attention, tu t'es engagé à 2 semaines… **tu vas rendre en avance alors que tu es en
  retard** » → **collision inter-projets**. Sur le tableau de bord : une case **verte→
  rouge** « ton planning est bon / tu n'as plus le temps », et **« qu'est-ce qui se
  collisionne »**. Prédictif **basé sur l'historique** : « Etienne, atelier Carré Neuf,
  a déjà fait cette tâche, ça lui a pris tant de temps ». **Clé d'adoption** : « j'ai
  fini ma tâche, **j'appuie sur un point et c'est fini** — si c'est comme ça tu utilises
  vraiment le truc ». Les **coches sont liées à des tâches**.
- **Sens produit :** un **plan atelier multi-projet** (Gantt/agile) + **estimation de
  durée prédictive** (depuis l'historique de l'atelier) + **détection de collisions
  inter-projets** + alertes vert/rouge sur le tableau de bord. Tâches **liées aux
  coches** de checklist. **Frontière IA : §4.**

### I · Honoraires prédictifs (formule SIA)
- **Notes :** « Gestion de Coût Prédictif ».
- **Audio :** pour un indépendant : « combien vaut mon temps ? » Lier **honoraires ↔
  temps réel ↔ argent engagé**. Après 1–2 projets : « **avant de commencer**, voici
  l'honoraire qu'il te faut pour ce type de projet » (temps prédit). Il existe une
  **formule SIA** basée sur le **prix de l'ouvrage / l'appel d'offres** → honoraire
  estimé (« je l'ai déjà, le mécanisme est ok, curseur ajustable »).
- **Sens produit :** un **estimateur d'honoraires prédictif** couplant la **formule SIA
  102** (cf. `architect-reality.md` §6, *H = T × h*) et l'historique de temps. Différencie
  pour les indépendants (les grosses boîtes « padent » leurs marges).

### J · Tâches collaborateurs, priorités P0/P1/P2, quick wins
- **Notes :** « Tâches Collaborateur gestion checklist » ; « Gestion Priorité **P0/P1/
  P2** + **quick win** ».
- **Audio :** assigner une tâche à un employé (dans le calendrier) ; voir si on le
  **surcharge** (« dans le rouge total ») ; le collaborateur la reçoit **sur SA
  checklist** (« le lundi, dans son app : qu'est-ce que tu fais cette semaine »). L'app
  conseille : « vu ton planning, fais ça, ça, ça ». **Quick wins** = tâches rapides,
  peu critiques, vite « débarrassées ». **Méthode réelle d'Etienne** : il **navigue en
  priorités, pas en agenda** (« l'agenda est inutile, trop élastique ») — « je dois
  savoir **ce qui me bloque sur tous mes projets en même temps**, et ce que je peux
  faire en parallèle ». Ses tâches ont des **icônes** (référence, priorité, où ça
  s'inscrit, incidences, liens) et des **dépendances** (tâches bloquantes pour des
  sous-tâches). + Pareto (les derniers 20 % prennent 80 % du temps) & Murphy.
- **Sens produit :** un **graphe de tâches priorisé & à dépendances** (P0/P1/P2 +
  bloquant/bloqué + quick-win), assignable aux collaborateurs, **navigable par « qu'est-
  ce qui me bloque »** — *pas* un agenda. Vue de charge par collaborateur. (NB : on
  priorise déjà le dev exactement ainsi — P0/P1/P2 + quick wins.)

### K · Opposition : la critique d'Etienne (à rendre crédible)
- **Audio :** il trouve l'app « jolie », « ça claque » — **mais l'onglet *Risque
  d'opposition* est son moins crédible.** « C'est **toujours élevé**… ça ne m'apprend
  rien, ça fait appel au flair ; je sais déjà qu'un projet non réglementaire = risque
  élevé. » **Comment le rendre utile :** le **calculer sur la documentation canonique**
  fournie ; aller plus loin — analyser **les bâtiments voisins**, l'**historique
  d'opposition du voisin**, les **jurisprudences** ; au lieu de « élevé/modéré », dire
  **« attention précisément à CE point »**. Les **décisions communales sont publiques**
  (« si c'est public, c'est analysable ») → une IA qui **scanne la doc publique de la
  zone** (ce qui a été refusé et pourquoi) et rend un **feedback ciblé**. « Si je devais
  mettre un effort, je le mettrais **ailleurs** d'abord. »
- **Sens produit :** refondre l'opposition d'un **score générique** vers une **analyse
  sourcée & ciblée** (doc canonique du dossier + scan des décisions publiques +
  jurisprudence) avec des **alertes précises**. **Priorité : P2** (approfondir, pas
  vitrine) — Etienne le juge le moins crédible aujourd'hui.

### L · Règlement à l'étude — alerte prédictive
- **Notes :** « Règlement à l'étude — prédiction / alerte ».
- **Audio :** savoir si le **règlement est à jour** ; les règlements **changent à
  certaines dates**. Pas seulement « valable encore 1–2 ans » mais **« un autre est à
  l'étude »** qui donnera d'autres hauteurs/densités — risque d'être **sur de mauvaises
  bases** en cours de projet. Alerte : « attention, règlement en cours d'étude/ré-étude ».
- **Sens produit :** suivi de **versions/validité des règlements communaux** + **alerte
  « règlement à l'étude »** sur un projet impacté. Étend l'ingestion de communes
  (versionner + dater + signaler les révisions en cours).

### M · Capture de friction & preuves (photos)
- **Audio :** une **mini-CLI** attachée à un projet : « ajoute une issue », formatée
  « ça vient d'Etienne, constatation…, aurait préféré ceci » → ticket auto. Et : « il
  veut faire des trucs avec **les photos** — un truc qui ne reste pas dans la tête,
  **des preuves à futur** ».
- **Sens produit :** (a) **capture de friction** (voix/texte → issue structurée, taguée
  auteur/observation) ; (b) **photos = preuves horodatées** rattachées au projet/PV.
  Relie l'agent site-report du `phase-value-catalog` (photos → PV) §52.

---

## 3 · Le verdict d'Etienne (priorités validées)

> Ce sont SES priorités, dites en séance — elles pilotent la roadmap §6.

1. **Ce qu'il trouve « le plus intéressant » :** « ce côté **multi-entrée, gestion de
   projet, lien avec calendrier, points de PV et points de décision** ».
2. **Ce qu'on construit d'abord (accord explicite) :** la **phase préliminaire + la mise
   en place d'un projet** — la couche d'exploitation (A–G) — « que ça **fonctionne pour
   de vrai**, qu'on puisse **tester** cette partie ». Puis **phase par phase, module par
   module, petit à petit**.
3. **Ce qu'il testera :** il **utilise l'app sur un vrai projet** (ou un existant), et
   remonte les **frictions** (« j'aurais préféré cette action-là »).
4. **Sa réserve :** l'opposition (K) est son onglet le moins crédible → **à
   approfondir, pas à mettre en vitrine**. La gestion d'accès **par donnée** (très fine)
   ajoute de la complexité → **différer** la granularité extrême.
5. **Son exigence d'adoption :** **facile à utiliser** (un clic = tâche finie) + **« ça
   claque »** (il a aimé le redesign : « j'ai pensé à Etienne à qui je vais le montrer en
   premier, il faut que ça claque salement »).

---

## 4 · La frontière IA (cadrage d'Etienne — important)

Etienne est explicite : **ne pas mettre de l'IA partout** (« les informaticiens veulent
mettre IA partout, c'est très bête »). La majorité de la couche d'exploitation est **du
« pur soft »** — de la **gestion de projet normée** (annuaire, checklists, accès,
calendrier) qu'**il ne faut pas réinventer** (« des mécanismes qui existent déjà,
récupérables »).

| L'IA sert vraiment ici | C'est du « pur soft » (ne pas sur-IA-iser) |
|---|---|
| **Prédictif** : durée de tâche / honoraires depuis l'historique de l'atelier | Annuaire, registre d'intervenants, gestion d'accès |
| **Collision inter-projets** (analyse de charge & deadlines) | Checklists SIA, cases liées aux tâches, statuts |
| **Scan/analyse** de la doc publique (opposition ciblée, jurisprudence) | Import/versioning de documents, niveaux de validation |
| **Veille réglementaire** (règlement à l'étude, impact) | Calendrier / Gantt / vue de charge |
| **Proposition** de sources (toujours validées par l'architecte) | Capture de PV/photos, tickets de friction |

> **Garde-fou produit (déjà notre principe) :** « **l'architecte EST la référence
> finale de validation systématique. Il n'y a pas un truc qui valide à sa place.** »
> = exactement « l'IA propose, l'architecte décide » + « sourcé ou inconnu ».

---

## 5 · Réconciliation du modèle de phases SIA

Etienne a apporté la **feuille SIA section Vaud** comme référence du parcours. Elle doit
devenir la **source du gabarit de checklist** (§2-D) et aligner la frise de l'app.

| Feuille SIA Vaud (Etienne) | Code SIA officiel (`architect-reality.md` §3) | Frise actuelle de l'app | Action |
|---|---|---|---|
| Phase 1 — Définition des objectifs | **11** | `0 Intake` | renommer/aligner sur **11** |
| Phase 2 — Études préliminaires | **21** faisabilité · **22** choix mandataires (concours) | `11 Faisab.` | ajouter **22** (concours SIA 142/143) |
| Phase 3.31 — Avant-projet | **31** | `31 Avant-pr.` | ok |
| Phase 3.32 — Projet de l'ouvrage | **32** | `32 Projet/BIM` | ok |
| Phase 3.33 — Demandes d'autorisation | **33** | `33 Permis` | ok |
| Phase 4.41 — Appels d'offres | **41** | `41 Appel d'offres` | ok |
| Phase 5.51 — Projet d'exécution | **51** | `5x Exécution` | scinder 51/52/53 |
| Phase 5.52 — Exécution de l'ouvrage | **52** | `52 Chantier` | ok |
| Phase 5.53 — Mise en service | **53** | `6 Exploit.` | distinguer **53** vs **6** |
| (—) Exploitation | **61 / 62 / 63** | `6 Exploit.` | sous-phases 61/62/63 |

**Deux exigences supplémentaires (cf. `architect-reality.md` §3) :**
- La feuille porte aussi **précision du coût** (±15 % en 31 → ±10 % en 33), **durée de
  phase**, **intervenants par phase** → colonnes à **surfacer par phase** (jauge de
  précision de coût, qui est impliqué, durée attendue).
- **Modéliser les DEUX référentiels** : SIA 112:2014/102:2020 (contrats en cours) **et**
  SIA 102:2024 (Phase 0 « Initialisation » + scission 41/42). L'app doit porter les deux.

---

## 6 · Roadmap d'intégration (priorisée)

Principe : on suit l'accord d'Etienne — **la couche d'exploitation d'abord**, testée sur
un vrai projet, puis phase par phase. Priorités **P0/P1/P2 + quick win** (sa propre
grille).

### 🟥 P0 — « Mise en place d'un projet » (l'essentiel, à tester en premier)
*La phase préliminaire opérationnelle qu'Etienne veut éprouver.*
1. **Registre d'intervenants** par projet (groupes ⊃ sous-groupes ⊃ personnes) +
   **contacts/responsables sourcés** → alimente un **annuaire atelier** réutilisable. *(A,B)*
2. **Module Documents/Sources** : import local + **versioning** + nom officiel ;
   **validation 3 niveaux** (canonique/indicatif/refusé) par l'architecte ; **injection
   manuelle** d'une source canonique. *(E)*
3. **Gestion d'accès par document/dossier × intervenant** (groupe/personne) + **flag
   confidentiel LPD**. *(A,F)* — granularité **moyenne** d'abord (par groupe/dossier),
   pas par donnée.
4. **Checklist SIA paramétrable** (gabarit depuis la feuille SIA) : à l'ouverture,
   **activer/différer/désactiver** les steps → steps réels ; **embarquement à n'importe
   quelle phase + checklist rétroactive**. *(C,D)*
5. **Tableau de bord « à valider »** : file des items rouges (documents/steps à valider).
   *(E,H)*
6. **Base vivante de référence** : PV de séance + décisions (y c. « coup de tél »),
   versionnée, responsable par entrée — extension de la **Mémoire**. *(G)*

### 🟧 P1 — Pilotage multi-projet (le différenciateur le plus désiré)
7. **Plan atelier multi-projet** (liste de projets + tâches) avec **tâches liées aux
   coches** de checklist ; **complétion en 1 clic**. *(H,J)*
8. **Graphe de tâches priorisé & à dépendances** (P0/P1/P2, bloquant/bloqué, quick-win,
   icônes), **navigable par « ce qui me bloque »** (pas un agenda). *(J)*
9. **Estimation de durée prédictive** (historique atelier + pondération apprise) +
   **détection de collisions inter-projets** + **alertes vert/rouge** au tableau de bord. *(H)* — **IA**
10. **Assignation aux collaborateurs** + **vue de charge** (sur-charge = rouge) +
    **checklist par collaborateur** + suggestions « quick wins de la semaine ». *(J)*
11. **Honoraires prédictifs** : formule **SIA 102** (prix de l'ouvrage / appel d'offres)
    × temps historique → honoraire conseillé. *(I)* — **IA**

### 🟨 P2 — Approfondissements (après validation terrain)
12. **Opposition crédible** : recalculer **sur la doc canonique du dossier** + **scan des
    décisions publiques de la zone** + jurisprudence → **alertes ciblées** (« attention
    à CE point »), pas un score générique. *(K)* — **IA**
13. **Veille réglementaire** : versions/validité des règlements + **alerte « règlement à
    l'étude »** sur projets impactés. *(L)* — **IA**
14. **Capture de friction** (voix/texte → issue taguée) + **photos = preuves horodatées**
    rattachées au projet/PV. *(M)*
15. **Granularité d'accès fine** (par donnée) — différée (complexité, réserve d'Etienne).

### ⚡ Quick wins (faisables vite, fort signal)
- Renommer/aligner la **frise SIA** sur les codes officiels + ajouter **22 (concours)**
  et scinder **51/52/53**. *(§5)*
- Surfacer la **précision de coût par phase** (±15 %→±10 %) et **les intervenants par
  phase** sur le tableau de bord (déjà dans la feuille SIA). *(§5)*
- **Flag confidentiel** + mention LPD sur un document (socle de P0-3). *(F)*

---

## 7 · Cartographie dans l'app (existant à étendre vs nouveau)

| Besoin séance | Surface/feature existante | Nature |
|---|---|---|
| Registre intervenants + annuaire | Équipe (rôles owner/member/viewer) | **étendre** (intervenants ≠ users ; groupes/sous-groupes) |
| Accès par document × intervenant | capacités (`org.manage`, etc.) | **nouveau** (ACL documentaire) |
| Documents/sources + 3 niveaux validation | trust states + ledger | **nouveau module** sur le socle de confiance |
| Checklist SIA paramétrable + rétroactive | next-step (par phase) | **étendre** (gabarit, activation, rétroactif) |
| Base vivante (PV, décisions) | Mémoire (inconnues + journal) | **étendre** |
| Tableau de bord « à valider » | Dashboard (phase-aware) | **étendre** (file de validation) |
| Multi-projet Gantt/collision/prédictif | Accueil (liste projets + avancement) | **nouveau** (niveau atelier) |
| Tâches priorisées/dépendances/collaborateurs | next-step | **nouveau** (graphe de tâches) |
| Honoraires prédictifs | Coûts & soumissions (cockpit honoraires) | **étendre** (prédictif + formule SIA) |
| Opposition ciblée + scan public | Risque d'opposition | **refondre** (sourcé/ciblé) |
| Veille règlement | ingestion de communes | **étendre** (versions + alerte) |
| Photos/preuves + friction | Copilote / Chantier | **nouveau** (capture) |

---

## 8 · Checklist actionnable (pour ouvrir le chantier)

**Préparation**
- [ ] Confirmer le sigle **« BRS »** avec Etienne (§9) et la granularité d'accès visée.
- [ ] Récupérer la **formule SIA 102** d'Etienne (honoraires ← prix de l'ouvrage). *(I)*
- [ ] Récupérer **un vrai projet** (ou existant) d'Etienne pour le test terrain.
- [ ] Numériser/joindre la **feuille SIA Vaud** comme source du gabarit de checklist.

**P0 — mise en place d'un projet (à construire & faire tester)**
- [ ] Modèle de données : `Intervenant` (groupe/sous-groupe/personne, contact,
      responsable) + `Document` (version, nom officiel, niveau de validation, confidentiel)
      + `AccessGrant` (document/dossier × intervenant).
- [ ] UI **Intervenants** : ajout progressif, arborescence, contacts sourcés, annuaire.
- [ ] UI **Documents** : import + versioning + validation **canonique/indicatif/refusé**
      (gate architecte) + injection manuelle + flag **confidentiel (LPD)**.
- [ ] **Gabarit checklist SIA** par phase + activation/diffère/désactive à l'ouverture +
      **phase d'entrée paramétrable** + **checklist rétroactive**.
- [ ] **File « à valider »** sur le tableau de bord.
- [ ] **Base vivante** : entrées PV/décision versionnées, responsable.
- [ ] Faire **tester par Etienne** sur un projet réel → journal de frictions.

**P1 — pilotage multi-projet**
- [ ] Vue **atelier multi-projet** + tâches liées aux coches + complétion 1 clic.
- [ ] **Graphe de tâches** (priorité/bloquant/dépendances) navigable par « ce qui bloque ».
- [ ] **Prédictif durée** + **collision inter-projets** + alertes vert/rouge.
- [ ] **Collaborateurs** : assignation, charge, checklist perso, quick wins.
- [ ] **Honoraires prédictifs** (formule SIA × historique).

**P2 — approfondir**
- [ ] **Opposition** sourcée/ciblée (doc canonique + scan décisions publiques + jurisprudence).
- [ ] **Veille réglementaire** (versions + « règlement à l'étude »).
- [ ] **Capture friction + photos preuves**.

**Quick wins**
- [ ] Aligner la **frise SIA** (codes officiels, +22, 51/52/53, 61/62/63).
- [ ] Surfacer **précision de coût** + **intervenants par phase**.

---

## 9 · Questions ouvertes (à valider avec Etienne)

1. **« BRS »** : sens exact du sigle (note p.3 « Verrou de BRS / Source de BRS »). Le
   concept (base de référence sourcée, verrouillée/versionnée) est clair, l'acronyme non.
2. **Granularité d'accès** cible pour la v1 : par **groupe/dossier** (proposé) vs par
   donnée (différé) — il a lui-même signalé la complexité.
3. **Formule d'honoraires** SIA précise + variables (prix de l'ouvrage, coefficients).
4. **Annuaire** : partagé au niveau atelier dès la v1, ou par projet d'abord ?
5. **Prédictif** : démarrer sur des **estimations manuelles + pondération** (sans IA)
   puis brancher l'historique, ou viser l'IA d'emblée ?

---

## 10 · Prochaine étape concrète

Conforme à l'accord de séance :

1. **Construire le P0** (mise en place d'un projet : intervenants + accès + documents/
   validation + checklist SIA paramétrable + base vivante), sur la DA Datum, avec le
   même soin UX.
2. **Le faire tester par Etienne** sur un vrai projet → recueillir les frictions.
3. **Itérer phase par phase / module par module**, en branchant l'IA **là où elle sert
   vraiment** (§4) : prédictif, collision, scan public, veille.

> Cadre business : Etienne évoque un **mandat** (« ça serait un mandat à ce moment-là »).
> Le partenariat pilote est donc en bonne voie — l'app redressée « claque », et la
> direction (couche d'exploitation d'abord) est **validée par l'architecte terrain**.
