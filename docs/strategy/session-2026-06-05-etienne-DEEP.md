# Séance Etienne — analyse profonde v3 (relecture exhaustive)

> **État de cette version.** v1 (`session-2026-06-05-etienne-synthesis.md`) survolait.
> v2 (la précédente version de ce document) avait identifié la couche multi-acteurs
> manquante mais restait globale. v3 (**ce document**) redéploie l'analyse à partir des
> matières brutes — **transcription audio ligne par ligne**, **4 notes manuscrites
> image par image**, **feuille SIA Vaud officielle retrouvée en source intégrale** — et
> rend explicites les implicites du dialogue. Source : Etienne Piergiovanni (architecte
> SIA-VD), session du 2026-06-05, 47 min utiles.
>
> Source retrouvée (j'ai pu télécharger la feuille originale d'Etienne) :
> SIA Vaud, *Construire dans les règles de l'art — suivez le guide*,
> <https://www.vd.sia.ch/sites/vd.sia.ch/files/181130_SIA-DEPLIANT-DOC_FINAL.pdf>.
> Référentiels cités : SIA 102/103/104/105/106/108 + norme SIA 112.

---

## 0 · Pourquoi une v3

L'utilisateur a explicitement reproché à v2 :
- la lecture du transcript est restée en surface, beaucoup de détails non extraits ;
- les notes manuscrites n'ont pas été toutes restituées (points importants oubliés) ;
- la checklist SIA implémentée n'est *pas exhaustive du tout* ;
- la dimension **multi-acteurs avec accès plateforme** (client + intervenants) n'est pas
  implémentée — alors qu'elle est dans le transcript ET dans les notes ;
- les **devoirs du client** ne sont pas modélisés ;
- la **double piste** (checklist côté client / suivi côté architecte) est manquante ;
- les **bloquants externes** doivent être visibles à part des bloquants atelier ;
- il faut un **point unique** pour : trouver les documents · voir ce qui est attendu de
  chacun · faire les validations.

v3 part de la matière brute et tient compte de tout cela.

---

## 1 · La feuille SIA Vaud d'Etienne, retranscrite intégralement

C'est le pivot. Etienne nous l'a tendue en disant *« cette liste, elle est quasi écrite
ici »* [04:42]. J'en restitue **l'intégralité** ci-dessous, du PDF officiel — c'est CETTE
liste qui doit nourrir l'outil. Légende : **MO** = maître de l'ouvrage, **A** =
architecte SIA, **I** = ingénieur·e·s/spécialistes (mandataires), **E** = entreprises,
**Aut** = autorité (commune, services techniques), **V** = voisinage.

### 1.1 · Acteurs reconnus par la feuille
La feuille pose **six** acteurs : MO · A · I · E · Aut · V. Les quatre premiers sont des
*utilisateurs* potentiels de la plateforme (ils interagissent, livrent, valident).
L'autorité et le voisinage sont des **destinataires/sources** (l'objet, pas l'utilisateur).
À retenir : la plateforme doit modéliser **MO, A, I, E** comme acteurs-utilisateurs ;
**Aut** comme destinataire de dossiers ; **V** comme objet d'analyse (oppositions).

### 1.2 · Colonnes de tracking de la feuille
Pour chaque phase, la feuille tient quatre colonnes :
1. **Précision du coût** (matérialisée par des cibles concentriques, du large au précis).
2. **Précision du projet** (cibles également — flou → net).
3. **Durée de la phase sur le projet** (barre temporelle ; révèle le poids relatif).
4. **Intervenant·e·s au sein du projet** (les icônes des acteurs présents).

C'est cette grille à **4 colonnes** qui doit constituer la lecture par phase dans l'app —
au-delà de la liste des steps. C'est ce qu'Etienne entend par *« je clique sur la phase,
je vois ce qui s'y passe »*.

### 1.3 · Contenu intégral, phase par phase (verbatim de la feuille)

**PHASE 1 · Définition des objectifs**
- Données du **MO** : rêves · budget · terrain · délais.
- Prestations **A** :
  - Échange avec le MO : traduction des rêves en besoins (nb de chambres, m²…).
  - Évaluation du budget : conseils et scénarios de financement.
  - Récolte des données de base du terrain : ensoleillement, cadre légal, affectation,
    règlements, capacité constructive, qualité du terrain, zones de protection des eaux,
    plan de quartier, exigences de la commune, etc.
  - Estimation des délais : évaluation du temps nécessaire de la planification à la
    réalisation.
- Précision coût / projet : **« À convenir spécifiquement »** *(non standardisée)*.
- Intervenants présents : MO, A.

**PHASE 2 · Études préliminaires**
- Acquis de la phase 1 *pour le MO* :
  - les besoins sont énoncés ;
  - le budget cadre est défini ;
  - le terrain a été analysé ;
  - les délais sont énoncés.
- Prestations **A** :
  - Étude de faisabilité.
  - Recommandation des différents types de mandataires (selon contraintes :
    ingénieur·e thermicien·ne, acousticien·ne, etc.).
  - Cahier des charges sommaire :
    - programme/concours (si MO public),
    - estimation des coûts et des honoraires (ordre de grandeur),
    - récolte des données légales, environnementales, etc.
- Précision coût / projet : **« À convenir spécifiquement »**.
- ⤷ **CONTRAT SIA** (signature) — la feuille place le contrat SIA en sortie de phase 2.
- Intervenants présents : MO, A.

**PHASE 3 · Étude du projet · 3.31 Avant-projet**
- Acquis de la phase 2 *les informations détaillées sont connues* :
  - l'étude de faisabilité a permis de choisir le projet le plus adapté ;
  - les différents types de mandataires sont identifiés : architecte + spécialistes ;
  - le cahier des charges est établi : programme + estimation des coûts/délais.
- Prestations **A + I** :
  - Choix des mandataires : choix de professionnel·le·s spécialisé·e·s et prise en
    compte de leurs contraintes.
  - Recherche d'implantation du bâtiment et de sa forme :
    - élaboration d'un concept architectural pour le parti retenu ;
    - forme du bâtiment ;
    - matérialisation (bois, béton, métal, verre, etc.) ;
    - définition de la structure porteuse ;
    - définition des objectifs énergétiques.
  - Estimation sommaire des coûts : **± 15 %** (sauf autre convention).
  - Établissement du calendrier général pour le projet de construction.
  - Établissement des contrats de mandataire.
- Précision coût : ± 15 %.
- Intervenants : MO, A, I.

**PHASE 3.32 · Projet de l'ouvrage  ·  3.33 · Demandes d'autorisation**
- Acquis de la phase 3.31 :
  - l'avant-projet est fait ;
  - les mandataires ont été choisis ;
  - le devis estimatif a été validé ;
  - le calendrier a été validé ;
  - les contrats sont signés.
- Prestations **A + I** :
  - Développement de projet : calcul et dimensionnement des éléments de construction et
    des techniques.
  - Direction de projet.
  - Organisation et coordination des mandataires.
  - Établissement de plans et documents : plans, coupes et façades à l'échelle prescrite
    pour la demande d'autorisation de construire ; étude de détails constructifs et
    choix des matériaux.
  - Établissement d'un devis général : **± 10 %**.
  - Élaboration du dossier d'enquête :
    - démarches auprès des pouvoirs publics et des services techniques, prise en compte
      de leurs exigences ;
    - suivi administratif du dossier.
- Précision coût : ± 10 %.
- ⤷ **MISE À L'ENQUÊTE**, puis **PERMIS DE CONSTRUIRE** (jalons publics).
- Intervenants : MO, A, I, Aut.

**PHASE 4.41 · Appels d'offres**
- Acquis des phases 3.32 & 3.33 (« le projet est connu ») :
  - le projet et les détails sont développés ;
  - le permis de construire est en cours ou est délivré ;
  - le planning est validé ;
  - le devis général est validé.
- Prestations **A + I** :
  - Plans d'appels d'offres : élaboration à une échelle appropriée de tous les plans et
    détails de principe nécessaires.
  - Appels d'offres :
    - intégration de toutes les propositions des professionnel·le·s spécialisé·e·s ;
    - rédaction d'un descriptif détaillé des matériaux et de la construction (**avec
      quantitatifs**) ;
    - lancement des appels d'offres.
  - **Adjudication** (attribution des mandats) :
    - contrôle des offres, comparaisons, analyse, proposition d'adjudication,
      négociations ;
    - adjudication des travaux et des fournitures.
  - **Révision des coûts et des délais** : après retour des offres, en collaboration
    avec les professionnel·le·s spécialisé·e·s.
- ⤷ **ADJUDICATION** (jalon).
- Intervenants : MO, A, I, E.

**PHASE 5.51 · Projet d'exécution**
- Acquis : « les entreprises sont connues » — entreprises adjugées, coût connu, dossier
  d'appels d'offres établi.
- Prestations **A + I** :
  - Contrats avec les entreprises.
  - Établissement des plans d'exécution après intégration des optimisations des
    entreprises (mise au point des détails : emplacement des prises, etc.).
  - Choix définitif des matériaux et des appareils **d'entente avec le MO**.
  - Établissement du calendrier définitif.
- Intervenants : MO, A, I, E.

**PHASE 5.52 · Exécution de l'ouvrage**
- Acquis : « les contrats d'entreprises sont signés » — plans d'exécution et détails
  définitifs, contrats signés, planning des travaux.
- Prestations **A + I** :
  - Coordination des mandataires, entreprises et fournisseurs.
  - Direction architecturale : vérification de la concordance exécution ↔ conception
    (plans).
  - Direction des travaux : surveillance + conduite générale du chantier, établissement
    des **métrés**.
  - Contrôle du coût et des délais.
- ⤷ **CHANTIER**.
- Intervenants : MO, A, I, E, Ouvriers.

**PHASE 5.53 · Mise en service**
- Acquis : *l'ouvrage est réalisé*.
- Prestations **A + I** :
  - **Mise en service** : vérification de l'ouvrage avec mandataires, entreprises et
    fournisseurs ; élimination des défauts constatés ; **réception des travaux (séances
    et PV)**.
  - **Documentation de l'ouvrage** : remise au MO du dossier conforme à l'exécution.
  - **Travaux de garantie** : élimination des défauts identifiés **dans un délai de
    2 ans**.
  - **Décompte final**.
- ⤷ **REMISE DES CLEFS**.
- Intervenants : MO, A, I, E.

> 💡 La feuille omet explicitement la **« phase 0 »** d'initialisation (SIA 112 dit
> qu'elle est *exclusivement* des prestations du mandant) — pour Aedifica, c'est le
> moment de l'**intake** : le MO contacte l'architecte. Notre app place sa première
> valeur ici.

### 1.4 · Le lexique de la feuille
La feuille embarque un lexique de 22 termes — c'est notre vocabulaire produit (à utiliser
tel quel dans l'UI) : Adjudication · Architecte SIA / Ingénieur·e SIA · Cahier des
charges · Concept · Contrainte · Contrat SIA · Coordination · Devis estimatif · Devis
général · Étude de faisabilité · Honoraires · Implantation · Maître de l'ouvrage ·
Mandataire · Métrés · Optimisation · Parcelle · Planification · Programme · Spécialiste.
À adopter dans la nomenclature de l'app (tooltips, libellés, glossaire).

---

## 2 · Les 4 notes manuscrites d'Etienne — image par image

### 2.1 · Note 1 (page de garde) — *« AEDIFICA — Vendredi 5 juillet KickOff »*

> Texte intégral : *« AEDIFICA / Vendredi 5 juillet KickOff / Présentation / Recherche →
> terrain / Source : Importe en local + versioning → la ref du doc | nom du doc officiel
> / Validation des document externes par l'archi ma / 3 niv : Canonique · Indicatif ·
> Refusé / Step de Base Cohérent / Pas prochain avec validation »*

Décortiqué :
- **Source : Importe en local** — Etienne demande explicitement que les sources soient
  *importées en local* (et non simplement référencées par lien externe) ; cohérent avec
  sa demande LPD et avec le sourçage manuel canonique (un permis modifié injecté).
- **+ versioning** — chaque source porte ses versions.
- **« la ref du doc | nom du doc officiel »** — chaque document a deux libellés :
  - une **référence** (interne au projet) ;
  - son **nom officiel** (tel qu'il est connu hors-projet, ex. *« Permis de construire
    n°CAMAC 2025-1234 »*).
- **Validation par l'archi = mandataire** — l'archi reste l'arbitre.
- **3 niveaux** : Canonique / Indicatif / Refusé (et pas davantage). C'est précisément
  ce que W9 a livré (`validation_level`) ✅.
- **« Step de Base Cohérent »** — l'app propose un *step suivant cohérent*, pas une
  liste exhaustive.
- **« Pas prochain avec validation »** — l'architecte valide le prochain pas (rien de
  poussé sans validation).

### 2.2 · Note 2 — *« par module · checklist rétroactive · coût prédictif · règlement à l'étude »*

> Texte intégral : *« → Par module / Projet doit être rejoint à n'importe quel Ø phase /
> avec checklist rétroactive / → Sourçage canonique manuel par l'atelier / → document
> confidentiel à traiter avec la LPD // Calendrier / gantt / agile / niveau Atelier
> prédictive / multiprojet / Collision Interprojet (AI) / Gestion de Coût Prédictif /
> Règlement à l'étude prédiction · alerte »*

Décortiqué :
- **« Par module »** — livraison par module, pas en bloc.
- **« Projet doit être rejoint à n'importe quel Ø phase »** — onboarding sans phase
  obligatoire (back-fill).
- **« avec checklist rétroactive »** — phases antérieures à l'entrée marquées
  rétroactives. ✅ W9.
- **« Sourçage canonique manuel par l'atelier »** — l'atelier peut FORCER une source
  canonique. ✅ W9.
- **« document confidentiel à traiter avec la LPD »** — bouton `confidential`. ✅ W9.
- **« Calendrier / gantt / agile »** — Etienne note TROIS approches, pas que gantt.
  Agile = navigation par priorité (P0/P1/P2). Base de notre tableau de tâches.
- **« niveau Atelier prédictive »** — la prédiction se nourrit du niveau de **l'atelier**
  (pas un benchmark global, l'atelier lui-même).
- **« multiprojet »** — vision cross-projet ✅ W9.
- **« Collision Interprojet (AI) »** — la seule case avec le tag « AI » écrit. Le reste
  est « pur soft ». La collision est calculée déterministe en W9 ; un raffinement IA
  (apprentissage de la pondération ×3 par tâche) est à venir.
- **« Gestion de Coût Prédictif »** — calculateur d'honoraires ✅ W9.
- **« Règlement à l'étude prédiction alerte »** — alerte sur réglementation en
  révision ✅ W9 (scaffold).

### 2.3 · Note 3 — *LE NŒUD MULTI-ACTEURS*

> Texte intégral : *« trier · trouver · transmettre / Phase SIA ≠ Phase Client /
> [encadré BRS] Version de BRS · Source de BRS · PV + Coup de tél · Base vivante de
> référence · version · Responsable · contacte · annuaire / Accès Client · Propre
> Checklist / Mandataire · Document à jour · Plans, etc / Procès Verbeau [Verbaux] /
> [encadré] Intervenant — groupe · personne — avec gestion d'accès documentaire »*

Décortiqué (chaque ligne) :

- **« trier · trouver · transmettre »** — le triptyque de la proposition de valeur,
  écrit en haut. Slogan produit.
- ⭐ **« Phase SIA ≠ Phase Client »** — **point critique non implémenté**. Le client ne
  pense pas en *phase 3.32* ; il pense en *« on a lancé la mise à l'enquête »*. La vue
  client doit projeter les phases SIA dans un **vocabulaire client** :
  - Définition des objectifs → *« On définit ensemble votre projet »*
  - Études préliminaires → *« On vérifie que c'est faisable »*
  - Avant-projet → *« On dessine le concept »*
  - Projet de l'ouvrage / autorisation → *« On prépare le permis de construire »*
  - Appels d'offres → *« On consulte les entreprises »*
  - Projet d'exécution → *« On finalise les plans pour le chantier »*
  - Exécution → *« Le chantier »*
  - Mise en service → *« On vous remet les clefs »*
- **[encadré BRS]** *« Version de BRS · Source de BRS · PV + Coup de tél · Base vivante
  de référence · version · Responsable · contacte · annuaire »* :
  - **Versioning** + **sourcing** du BRS. ✅ W9.
  - ⭐ **« PV + Coup de tél »** — Etienne précise *de quelles sources* viennent les
    entrées BRS : procès-verbaux **ET** coups de téléphone. Un canal *« téléphone »* est
    un type de source à part entière (W9 a `phone` ✅) ; les **PV** sont une source
    structurée (un PV peut générer plusieurs entrées BRS).
  - **« Base vivante de référence »** — label à utiliser dans l'UI pour le BRS (plus
    parlant).
  - **« version · Responsable · contacte · annuaire »** — chaque BRS porte un
    responsable et un contact, et ces contacts alimentent l'**annuaire** (récupérable
    entre projets, comme l'audio le dit aussi).
- ⭐ **« Accès Client · Propre Checklist »** — **point critique non implémenté**. Le
  client a un **accès** à la plateforme et **sa propre checklist** (ses devoirs).
- **« Mandataire · Document à jour · Plans, etc »** — le mandataire a un accès, et il
  **dépose ses documents** (pas seulement les consulte) — typiquement *les plans à
  jour*. → écriture autorisée pour les mandataires sur leur lot.
- ⭐ **« Procès Verbeau »** *(Procès Verbaux)* — entité de premier ordre. Pas juste un
  document parmi d'autres : un **PV** est un objet structuré avec *participants, points
  discutés, décisions, points à valider, points reportés*.
- **[encadré] Intervenant — groupe · personne — avec gestion d'accès documentaire** :
  groupe (entreprise/discipline) imbriquable ✅ W9 ; personne ✅ W9 ; **gestion d'accès
  documentaire** ✅ W9 (`AccessGrant`).

### 2.4 · Note 4 — *« Tâches Collaborateur gestion · checklist · Gestion Priorité P0/P1/P2 · + quick win »*

- **« Tâches Collaborateur gestion »** — chaque collaborateur a sa **propre vue tâches**.
- **« checklist »** — chaque collaborateur a aussi sa propre **checklist**.
- **« Gestion Priorité P0/P1/P2 »** — navigation par priorité, pas agenda. ✅ W9.
- **« + quick win »** — flag quick-win. ✅ W9.

→ La note 4 confirme que **le collaborateur est un acteur-utilisateur de la plateforme
avec sa propre vue scoping**. Généralisable : *tout acteur avec une responsabilité a sa
vue tâches/checklist*.

---

## 3 · Transcription audio — relecture ligne par ligne

Les segments importants, avec timecode, *plus* tout ce qui avait été manqué. (Le segment
> 42 min est hors-sujet et ignoré.)

### 3.1 · L'ouverture sur le multi-acteurs [00:00-03:35]
- **[00:11]** *« trouver les plans à jour, les procès-verbaux de séance ou tout document
  officiel… que ce soit par le maître d'ouvrage, que ce soit par les mandataires »*
  → trois utilisateurs explicitement nommés dès la première phrase.
- **[00:51-01:09]** *« je pose un document… il doit être accessible… rentrer les
  intervenants au fur et à mesure, qu'ils apparaissent. Une fois rentrés, ça crée la
  case correspondante »* → l'ajout d'un intervenant **crée son espace** (sa zone
  d'accès).
- **[01:16-02:35]** arborescence groupe ⊃ sous-groupe ⊃ personne ; jusqu'au canal
  (« mail du contremaître vs Manolo qui ne lit pas »).
- **[02:35-03:18]** *« sourcer directement leur contact »* + l'annuaire alimente d'un
  projet à l'autre.
- **[03:34]** *« cette interface qui te permet d'accéder, de trier, retrouver,
  transmettre »* — le triptyque (= la note 3).

### 3.2 · La checklist est la liste SIA [04:42-09:30]
- **[04:42]** *« cette liste des tâches, quand tu démarres un projet, elle est quasi
  écrite ici, en fait »* — pointant la feuille SIA Vaud (§1 ci-dessus).
- **[04:55]** *« toutes ces choses-là sont officielles, décrites par la SIA »*.
- **[05:00]** *« selon les projets, il y a des machins, tu vas simplifier… tu peux aussi
  mettre, ça, voilà, et pas besoin, ou alors c'est réglé »* → statuts à 4 :
  todo / done / deferred / skipped ✅ W9.
- **[05:20]** *« déjà classée dans l'ordre, structure cohérente, très bonne base »*.
- **[06:01]** *« on pourrait aussi s'imaginer que quand on est dans une phase, tac,
  prochain pas, qui pourrait être la liste complète… tu fasses aussi une phase de
  validation, … ok cette phase on va la faire, cette phase on la fera pas »*
  → **chaque phase est aussi validable** : on définit en amont les phases qui
  s'appliquent au projet.
- **[06:19]** *« peut-être même qu'on pourrait faire des groupes, ou pas, … des groupes
  de phase »* → groupement par grand bloc (1 / 2 / 3 / 4 / 5 / 6) déjà reflété par
  l'arbre SIA.
- **[06:45]** statuts proposés : *« premier à plus tard »* (= deferred) ; *« inutile,
  dans ce projet, concerné, non nécessaire »* (= skipped/N/A).
- **[07:39]** *« après le permis de construire, il n'y a pas de phase sur lesquelles tu
  n'es pas la main »* → après 3.33, l'architecte garde la main.
- **[07:43-08:08]** *« si tu le reprends à un point donné, tu peux renseigner les points
  précédents… si tu commences à un point qui n'est pas le point zéro, ça veut dire que tu
  as déjà la documentation nécessaire pour pouvoir renseigner jusqu'au point X »*
  → onboarding mid-process = **back-fill rétroactif** ✅ W9.
- **[08:34-09:00]** *« la réalité du terrain a ce côté un peu chaotique »*. *« un projet
  doit être rejoint à n'importe quelle phase »*.

### 3.3 · Documents : injection + canoniques + LPD [09:30-12:30]
- **[09:30]** *« il y a la gestion des documents… tu injectes »*.
- **[09:38]** *« si tu rejoins la phase au permis… il faudrait quand même une checklist
  rétroactive »*.
- **[10:18]** *« hyper bien que lui [l'app] puisse aller chercher des trucs et les
  proposer, tu valides »*. **[10:22]** *« mais il faudrait aussi un truc que tu peux lui
  balancer »* → **upload manuel canonique** existe à côté du fetch ✅ W9.
- **[10:27-10:49]** **canonique manuel** : *« on a reçu un permis qui n'a pas été demandé
  par moi, qui a ensuite été modifié, ce permis est une source que je lui mets dans le
  ventre — sourçage canonique manuel — sur laquelle il se base parce qu'il peut pas la
  trouver sur le net »*.
- **[10:49-11:06]** *« au-delà des documents officiels, tu as aussi tous les documents
  qui sont liés aux clients qui sont pas trouvables sur internet »*.
- **[11:11-11:45]** **LPD** : *« qui sont confidentielles… vraiment de pouvoir assurer
  que les documents confidentiels soient traités comme des documents confidentiels selon
  la loi… LPD »* ✅ W9 flag.
- **[11:45-12:22]** **dashboard à-valider** : *« un dashboard où tu vois hyper rapidement
  les trucs rouges en disant : j'ai X trucs à valider potentiellement, je clique, je
  tombe sur eux »* ✅ W9.

### 3.4 · Le bloc tâches / agenda / collision / honoraires [12:22-19:46]
- **[12:22]** *« il y a un truc le plus compliqué sur lequel j'ai vraiment pas du tout
  réussi à faire un truc sur mon fichier Excel »* → pierre d'achoppement personnelle ; on
  doit le résoudre.
- **[12:54-13:09]** *« travail au long cours… tu dois estimer combien de temps va prendre
  une tâche… pour toute tâche une forme de délai… je dois rendre ça à tel moment »*.
- **[13:21-13:38]** *« tâche à rendre dans trois mois mais qui me demande une semaine de
  travail entre-temps j'ai d'autres gens qui me demandent d'autres trucs »*.
- **[13:43]** *« ça concerne **même plus un projet mais ton calendrier de tous les
  projets** »*.
- **[13:53-13:57]** *« je me plante à chaque fois sur le combien de temps ça va me
  prendre, ça me prend toujours trois fois plus de temps »* → **pondération ×3 apprise**.
- **[14:03-14:09]** *« puisse me dire fais attention parce que tu t'es engagé »*.
- **[14:48-15:18]** *« une case qui passe du vert au rouge »* + **collision** : *« qu'est-
  ce qui se collisionne, parce que tu as trop de choses à faire encore sur ces deux
  prochaines semaines, dans deux semaines tu auras un gap parce que ton prochain rendu de
  SIA il est là »*.
- ⭐ **[15:32-15:53]** *« je suis en train aussi d'analyser qu'est-ce qui doit y avoir
  vraiment IA à l'intérieur… toute cette partie là c'est du pur soft, par contre cette
  partie là c'est intéressant d'avoir de l'IA dedans »*. **L'IA = uniquement la
  collision/prédiction.** Le reste = pur soft ✅ W9 déterministe.
- **[15:46-16:06]** *« la vision multiprojet et pouvoir faire du prédictif »*.
- **[16:06-16:20]** *« du prédictif avec : Etienne dans cet atelier carré-neuf
  précisément il a fait cette tâche déjà une autre fois ça lui a pris tant de temps,
  cette fois-ci tant de temps »* → la prédiction se nourrit du **journal de l'atelier**
  (pas un benchmark externe) ✅ W9.
- **[16:30-16:46]** *« j'ai fini ma tâche, j'appuie sur un point et c'est fini.
  Exactement »* → 1 clic = done. UX critique.
- ⭐ **[16:46-17:08]** *« c'est un des points les plus, parce que tout le reste c'est
  une forme de classement et c'est de l'aide bien menée, mais ce projet, je serais là »*
  → **pour Etienne, la gestion des tâches multi-projet est LA killer feature**.
- **[17:08-17:18]** *« voilà où tu vois si t'es dans le rouge ou dans le vert selon ton
  avancement, parce qu'effectivement ça veut dire que tu dois remplir des coches là-
  dedans, mais **ces coches sont liées à une tâche** »* → chaque coche checklist = une
  tâche. La fermeture d'une tâche ferme la coche correspondante.
- **[17:34-17:49]** *« pouvoir faire du prédictif à plusieurs niveaux… surtout pour un
  indépendant, c'est de se dire : c'est quoi l'argent que je reçois et combien vaut mon
  temps »*.
- **[17:57-18:04]** *« c'est ce que j'ai jamais fait, mais ça… »* — Etienne n'a JAMAIS
  rationalisé son tarif horaire ; pain point fort.
- **[18:04-18:21]** *« lien entre tes honoraires et le temps que tu mets vraiment… il
  pourrait te dire précisément en prédictif combien tu dois demander réellement à ton
  client »* → on dérive l'honoraire-cible de la prédiction temps × tarif horaire ✅ W9
  fee estimator a les deux méthodes ; rapprochement temps × rate à automatiser.
- **[18:35-18:53]** *« au bout d'un ou deux projets… c'est ça qu'il te faut comme
  honoraire »* → l'app conseille un honoraire dès projet #2 (boucle d'apprentissage).
- **[18:53-19:03]** *« les grosses boîtes s'en foutent, ils mettent des gros pavés »* →
  Aedifica **arme l'indépendant** face aux grandes structures.
- **[19:08-19:33]** *« il y a une formule faite par les SIA, à partir du prix de
  l'ouvrage »* + *« la formule existe déjà »* → la formule SIA est connue d'Etienne.
- **[19:33-19:46]** *« basé sur l'appel d'offres tu peux savoir quel est ton honoraire,
  et inversement »* → calcul bidirectionnel coût↔honoraire.

### 3.5 · Opposition : utile mais trop générique [20:45-25:36]
- **[20:45-21:32]** opposition systématiquement « élevée » → *« ne va pas m'apprendre
  grand chose »*.
- **[21:32-22:09]** *« cette donnée fait appel à du flair… je sais très bien si je suis
  dans un projet non réglementaire que le risque est extrêmement élevé »*.
- **[22:09-22:47]** *« calculé sur la documentation canonique »* + *« réfléchir par les
  bâtiments qui sont autour »*.
- **[22:47-22:56]** *« voisins est un gros fils de pute… s'il a déjà fait des oppositions,
  s'il a commandé des stations services… il a déjà fait des oppositions dans la
  commune »* → **profil des voisins** (oppositions passées, etc.).
- **[22:56-23:06]** *« faire attention précisément à ce point-ci »* → granularité fine,
  pas score global.
- **[23:06-23:14]** *« est-il capable d'aller consulter des jurisprudences »*.
- **[23:14-23:20]** *« dans cette commune et cet endroit ils se sont opposés où ils ont
  refusé un projet réglementaire pour telle raison »* → **jurisprudence locale**.
- **[23:20-24:34]** *« les oppositions… les décisions publiques »* + *« si c'est public,
  c'est réunissable, si c'est réunissable, c'est analysable »* + *« si tu mets une
  parcelle et une IA qui scanne toute la documentation publique possible de la zone… ça
  devient pertinent »*.
- **[24:48-25:00]** *« j'en mettrais d'abord ailleurs, un des onglets que j'utilise
  réellement qui me semblerait le moins crédible »* → **priorité basse** pour
  l'opposition tant que la scan-IA n'est pas branchée.
- **[25:23-25:36]** *« tu es à disposition des sources d'information : il n'y a pas de
  décision prise à la place… l'architecte est la référence finale de validation
  systématique »* → garde-fou.

### 3.6 · Règlement à l'étude — pain point majeur [26:16-27:41]
- **[26:16]** *« savoir si le règlement à jour »*.
- **[26:37-26:43]** *« règlements changent, ils changent à telle date »*.
- **[26:48-27:06]** *« règlement à l'étude… ils ont une date de péremption »* (en fait
  *« n'ont pas vraiment de péremption mais »* — les délais d'étude sont connus) → notion
  de **règlement valable** + **règlement en révision (study)**.
- **[27:06-27:12]** *« peut-être qui va te donner d'autres hauteurs à la corniche, autres
  densités »* → **paramètres affectés** : hauteur corniche, densité, etc.
- **[27:17-27:22]** *« pendant le cours de ton projet il arrive et tu n'es pas sur les
  bonnes bases »* → **risque critique** : projet basé sur des règles qui changent.
- **[27:33-27:41]** *« attention règlement en cours d'étude ou de ré-étude »* → l'alerte
  explicite.

### 3.7 · Bilan d'Etienne + roadmap [27:50-32:25]
- **[27:50-28:07]** *« ce que je trouve le plus pesé : ce côté multi-entrée gestion de
  projet, lien avec calendrier, et points de PV et points de décider »* → **PV + points
  de décision** : objet de premier ordre.
- **[28:11-28:22]** *« pour la gestion de projet, c'est de la pure gestion de projet »*
  → pas d'IA ici.
- **[28:22-28:32]** *« annuaire : ça existe déjà »* — patterns connus, ne pas réinventer.
- **[28:58-29:11]** *« la gestion d'accès spécifique de telle ou telle donnée à telle ou
  telle personne, ça commence à mettre des couches de complexité »* → justifie l'app vs
  Excel.
- **[30:01-30:42]** *« il faut vraiment partir sur l'essentiel »*.
- **[30:42-32:25]** *« si on met déjà ça en place, qu'on regarde que ça puisse fonctionner
  pour de vrai, qu'on puisse commencer à tester… puis on regardera ce qu'il y a ensuite,
  on rajoutera par phase par module petit à petit »* → roadmap explicite par module ;
  tester sur **un vrai projet d'Etienne**.

### 3.8 · Collaborateurs et propre checklist [32:38-34:13]
- **[32:38-32:54]** *« j'irais même plus loin… intégrer des collaborateurs »*.
- **[32:54-33:06]** *« je travaille sur un projet, tu dois une tâche à ton employé… il
  devrait y avoir, dans le calendrier, cette tâche : soit c'est moi, soit quelqu'un
  d'autre »*.
- **[33:06-33:23]** *« un emploi du temps pour me rendre compte si je surcharge mon
  collaborateur »*.
- ⭐ **[33:23-33:33]** *« avoir une idée et que **lui-même** ça lui sorte aussi, tout
  comme en fait c'est **d'abord sur sa checklist à lui** »* → **le collaborateur a sa
  propre vue et sa propre checklist**. Même mécanique que client/mandataire.
- **[33:40-33:50]** *« le lundi, tu mets dans son application : qu'est-ce que tu fais
  cette semaine »* → **brief hebdo** au collaborateur (interface dédiée).
- **[34:01-34:13]** *« quick wins que tu pourrais tacler rapidement »* ✅ W9.

### 3.9 · Navigation par priorité [34:43-37:46]
- **[34:43-35:01]** *« je navigue en points bloquants et P2, en priorité »*.
- **[35:01-35:09]** *« si je le rends en retard, c'est mort, j'aurai un concours »* → P0
  = couperet/concours/rendu officiel.
- **[35:14-35:24]** *« ça sert même à rien que j'ai un agenda, c'est tellement élastique,
  je dois savoir qu'est-ce qui me bloque sur tous mes projets en même temps et qu'est-ce
  que je peux faire en parallèle »* → bloquants **cross-projet** + opportunités en
  parallèle.
- **[35:32-35:48]** *« il y en a une que tu dois faire avant de pouvoir commencer une
  autre, tu n'as pas telle validation »* → **dépendances** + **validations bloquantes**.
- **[36:04-36:09]** *« Pareto : les vingt derniers pour cent prennent 80% du temps »*.
- **[36:09-36:17]** *« Murphy : tout ce qui doit arriver arrivera »* → conservatisme
  intégré dans les prédictions.
- **[36:39-37:25]** *« mes projets listés, j'en ai 15. Dans mes projets, ma liste de
  tâches avec des **icônes** : à quoi ça fait référence, niveau de priorité, dans quoi ça
  vient s'inscrire dans le projet, quelles sont les **incidences**, les choses
  directement liées »*.
- **[37:25-37:39]** *« sur-tâches avec des liens de dépendance, des tâches bloquantes
  pour des sous-tâches »* → arborescence parent/enfant + dépendances horizontales.
- ⭐ **Icônes manquantes côté W9** : *« à quoi ça fait référence »* (type de référence) ·
  *« dans quoi ça vient s'inscrire »* (phase/livrable de rattachement) · *« incidences »*
  (sur quoi cette tâche impacte).

### 3.10 · Accès de l'extérieur — le donneur d'ordre [38:40-39:09]
- **[38:40-39:00]** ⭐ *« cette tasse [page] qui liste de ce que j'ai prévu… si moi je
  te donne accès à ça, voilà maintenant c'est trop tôt… mais si on avance, **toi tu
  devrais y avoir accès, puis tu utilises avec ce qu'il y a à utiliser à ce moment-là,
  et à chaque fois tu vois un truc qui est bloquant**… »* → la métaphore canonique du
  **scope d'accès** + **bloquants visibles à l'invité**.

### 3.11 · L'IA accrochée au projet [40:00-40:33]
- **[40:00-40:11]** *« j'installe un lien qu'on appelle mini-AI CLI… tu mets l'IA dans
  ton projet 1 »*.
- **[40:11-40:33]** *« lui c'est tout le contexte du projet, c'est son contexte… si je
  lui dis ajoute une issue au projet, il le fait, et il va te la formater en disant
  c'est ça vient d'Etienne, constatation, aurait préféré ceci, cela »* → **création
  d'issues taguées auteur**, sans ouvrir le ticket à la main.

### 3.12 · Captures, photos, frictions [38:30-42:30]
- **[38:30]** *« preuves à futur »*.
- **[41:32-41:50]** *« des gens qui ont des problématiques différentes, qui aillent
  vraiment dans les problématiques, quelle est ma réalité, donc là quelles sont les
  frictions »* → **multi-utilisateurs avec frictions propres** → encore une fois,
  *multi-acteurs*.
- **[42:30-42:42]** photos : *« photo numéro, des fois plusieurs, des fois pas, ou photo
  temps à temps »* → 1-N photos, possible série temporelle.
- **[42:42-42:48]** **fissures : longueur · largeur · machin** → **mesures
  structurées** par type d'observation.

---

## 4 · Synthèse des manques v1+v2 que v3 doit combler

| Thème | v1 | v2 | À faire en v3 |
|---|---|---|---|
| Acteurs reconnus | atelier seul | 4 catégories | **MO, A, I, E** comme **utilisateurs** scoping + Aut/V comme objets |
| Phase Client ≠ Phase SIA | absent | absent | **Vue Client** avec vocabulaire client (mapping des 9 phases) |
| Checklist client | absente | tag actor | **Vue « Ce que vous devez fournir » côté client** + cocher |
| Checklist mandataire | absente | tag actor | **Vue « Vos plans à jour, vos livrables » côté mandataire** + uploader |
| Checklist collaborateur | absente | absente | **Vue hebdo « cette semaine »** par collaborateur |
| BRS sources (PV, tél) | sources libres | sources libres | **PV** comme objet structuré ; **téléphone** comme canal natif |
| Annuaire portable | non | non | **annuaire cross-projet** (carnet d'adresses transverse) |
| Doc « à jour » | versions | versions | **flag « doc à jour »** + alerte si versions divergentes |
| Procès-verbaux | docs | docs | **PV = objet** : participants, décisions, points reportés, points à valider |
| Bloquants externes | bloquants atelier | identifiés | **panneau « En attente de X »** consolidé multi-projet |
| Point unique « Coordination » | dispersé | identifié | **vue unique** : qui doit quoi · où ça bloque · documents · validations |
| Tâche icônes | priorité, dep | priorité, dep | + **type de référence**, **rattachement** (phase/livrable), **incidences** |
| Honoraires : tarif horaire perso | calculé | calculé | **boucle d'apprentissage** : recommander un tarif dès projet #2 |
| Photos fissures | flag photo | flag photo | **mesures structurées** (longueur, largeur, etc.) + **série temporelle** |
| Lexique SIA | générique | générique | **22 termes** du dépliant (tooltips/glossaire) |
| Étapes de la checklist | 28 génériques | ~47 par acteur | **base = liste SIA Vaud retranscrite verbatim §1.3** |

---

## 5 · Modèle conceptuel cible (v3)

### 5.1 · Quatre acteurs-utilisateurs
**MO**, **Architecte/atelier (+ collaborateurs)**, **Mandataire**, **Entreprise**. Chacun
est un *user* avec un *scope* défini par les `AccessGrant` et un *rôle* qui détermine
les capacités (lire/écrire/valider) et la vue par défaut.

### 5.2 · Mapping Phase SIA → Phase Client
| Phase SIA | Étiquette technique | Vocabulaire client |
|---|---|---|
| 11 | Définition des objectifs | *« On définit votre projet ensemble »* |
| 21 | Études préliminaires · faisabilité | *« On vérifie que c'est faisable »* |
| 22 | Choix des mandataires | *« On choisit les spécialistes »* |
| 31 | Avant-projet | *« On dessine le concept »* |
| 32 | Projet de l'ouvrage | *« On finalise le projet »* |
| 33 | Demande d'autorisation | *« On prépare le permis »* |
| 41 | Appels d'offres | *« On consulte les entreprises »* |
| 51 | Projet d'exécution | *« On finalise les plans pour le chantier »* |
| 52 | Exécution / chantier | *« Le chantier »* |
| 53 | Mise en service | *« Vos clefs et la garantie »* |
| 61 | Exploitation | *« On reste à vos côtés »* |

### 5.3 · Checklist par acteur — vraie source : §1.3
Chaque step `(phase, acteur, titre)` ; vue filtrable par acteur. La vue client n'affiche
*que ses* steps avec le vocabulaire client (5.2).

### 5.4 · PV (procès-verbaux) — objet de premier ordre
- Champs : *date · phase · participants (intervenants) · points discutés · décisions ·
  points à valider · points reportés · pièces jointes*.
- Génère **automatiquement** : entrées BRS (les décisions) + tâches (les points à
  valider/reportés) + bloquants (les blocages détectés).

### 5.5 · Bloquants externes = steps externes en retard
Un step `actor ∈ {mo, mandataire, entreprise}` encore `todo` :
- avec `is_retroactive=true`, ou
- dont la `phase_code` est ≤ à la phase courante du projet,
→ apparaît dans le **panneau « En attente de X »**.

### 5.6 · Point unique « Coordination »
Quatre cadrans :
1. **Qui doit quoi** : par acteur, ses steps `todo`.
2. **Où ça bloque** : externes (par acteur) + atelier (par collaborateur).
3. **Documents** : derniers documents par catégorie, à valider en premier.
4. **À valider** : queue Architecte (canonique/indicatif/refusé + checklist + BRS).

### 5.7 · Annuaire portable
Une `Person` (org + nom + rôle + contact) **transverse aux projets**, instanciée par
projet via une `Intervenant` row qui pointe la `Person`. Recyclable.

---

## 6 · Roadmap v3 — par module

### Wave 10 (en cours — refonte sur des fondations correctes)
**P0** :
1. **Checklist exhaustive** = retranscription verbatim de §1.3 dans le seed
   (`sia_checklist.py`). Chaque step porte son `actor`. ✅ déjà commencé.
2. **`ChecklistItem.actor`** + `responsible_intervenant_id` + migration. ✅ déjà fait.
3. **Vue *Mes devoirs*** côté client/mandataire/collaborateur (filtre par acteur + libellés
   adoucis pour le MO via 5.2).
4. **Endpoint `coordination`** (5.6) : 4 cadrans agrégés en une seule réponse.
5. **Bloquants externes** dans le panneau « À valider ».
6. **Rôle `external` + invitation** : un Intervenant peut devenir un User scoped.

**P1** :
7. **PV** comme entité (5.4) + génération auto BRS + tâches.
8. **Annuaire portable** (5.7).
9. **Documents : flag « à jour »** + alerte si plus récente version pas validée.

**P2** :
10. **Vue Phase pour Client** avec vocabulaire de 5.2.
11. **Mesures structurées** sur captures photo (fissure : longueur/largeur).
12. **Recommandation d'honoraires** (boucle projet #2).
13. **Tâches : icônes type/rattachement/incidences**.

### Wave 11 (suivante)
- Scan opposition (jurisprudence locale + profil voisin).
- Règlement à l'étude : sourcing automatisé Vaud + alerte sur paramètres affectés
  (hauteur corniche, densité).

---

## 7 · Garde-fous (à respecter strictement)

- **Pur soft sauf collision/prédiction/scan public** — confirmé note 2 + transcript 15:32.
- **L'architecte est la référence finale de validation systématique** — transcript 25:23.
- **Source de tout : retraçable** — sourçage canonique, sources, attribution (BRS, PV,
  tâches, captures).
- **LPD** — `confidential` strict + accès scoping.
- **Chaque acteur ne voit que sa part** — `AccessGrant` strict.
- **Aucune donnée inventée** — *« sourcé ou inconnu »*.
- **1 clic = done** — UX critique (transcript 16:30).

---

## 8 · Sources

- **Feuille SIA Vaud** (intégral ré-transcrit en §1.3) :
  <https://www.vd.sia.ch/sites/vd.sia.ch/files/181130_SIA-DEPLIANT-DOC_FINAL.pdf>
- **SIA 112:2014** *Modèle d'étude et conduite de projet* :
  <https://solsetconstructions.ch/methodes/Mthodes/Normes/SIA%20112_2014_Extrait.pdf>
- **prSIA 102:2024** *Prestations et honoraires* :
  <https://cms.sia.ch/fr/api/getMedia/990>
- **Annexe N1 SIA 102** (guide romand VD) :
  <https://www.vd.ch/fileadmin/user_upload/organisation/dinf/sg-dinf/guide_romand/n1_liste-prestations-architectes-sia-102.xls>
- **Transcription locale (confidentielle, hors-repo)** :
  `C:\Users\decarvalhoe\AppData\Local\Temp\audio-transcripts-2026-06-06\aedifica-session-etienne-2026-06-05.txt`
- **Notes manuscrites (4 images, hors-repo)** :
  `C:\Users\decarvalhoe\AppData\Local\Temp\aedifica-notes-2026-06-06\image-0{1..4}.jpeg`
