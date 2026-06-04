# Aedifica — Plan global du projet

> **Point d'entrée.** Présentation structurée et à jour de l'ensemble du projet : vision, approche,
> architecture, feuille de route, et **ce qui est déjà fonctionnel**. Les documents détaillés sont liés
> en fin de page. État : concept + stratégie + **pilote fonctionnel** + **produit web multi-projets déployé**
> (vagues W1–W7 mergées sur `main`, juin 2026).

---

## 1 · En une phrase

Aedifica (**ArchiOS Suisse**) est une **couche d'intelligence réglementaire et projet** qui transforme une
parcelle + un programme + les registres suisses liants en **savoir de projet sourcé et phase-aware**, le
porte comme **mémoire continue** sur tout le mandat SIA, et assiste l'architecte dans son travail
**fiduciaire, de coordination, économique, réglementaire, de dessin/modèle et de responsabilité**.

## 2 · Le problème

Un projet suisse est contraint dès le départ par une pile **fédéral → cantonal → communal → parcelle**,
éclatée sur **26 cantons, ~2 100 communes, 4 langues**, partiellement harmonisée et en dérive constante.
Ces contraintes vivent dans des PDF, géoportails, plans et la mémoire humaine. Les petits/moyens bureaux
ne sont **pas matures en BIM** (~35 %, marché au stade 2/4) : un produit « Auto-BIM » présuppose un modèle
qu'ils n'ont pas.

## 3 · Le message produit

> Le rêve « parler à une IA qui dessine » est visible et reste important, mais il ne suffit pas. La valeur est
> un gain concret **à chaque étape**, de la gestion documentaire initiale à la livraison finale — sourcé, tracé,
> et capable d'agir dans les outils du bureau quand l'architecte l'approuve.

Produit **généralisable** (pas verrouillé sur Archicad, pas un logiciel de dessin). Le bureau partenaire
(Archicad/BIM) est le **premier utilisateur pilote**, pas l'identité du produit. L'API multi-logiciels
pour assister le dessin, le modèle, les exports et les contrôles reste un axe produit natif.

## 4 · L'approche

- **Canonical-first (bottom-up)** : sources → unités canoniques traçables (NOMOS), avec provenance + validité temporelle.
- **Orchestration top-down** : des agents proposent / vérifient / journalisent ; l'humain reste responsable.
- **Action layer multi-logiciels** : MCP/API pour inspecter, générer, contrôler ou modifier des dessins/modèles/documents après dry-run, approbation et ledger.
- **Moteur neutre + jurisdiction packs** : la Suisse = 1ᵉ pack (le plus profond). Internationaliser = ajouter un pack.
- **Route réglementaire (sélecteur)** : par projet, on n'active que `Fédéral + canton choisi + commune choisie`.
- **Contrat de preuve** : chaque affirmation est sourcée (article + version + date) ou marquée hypothèse — **jamais une autorité**.
- **Ancrage sur les registres liants** : fedlex, geo.admin.ch + 26 géoportails, **cadastre RDPPF/ÖREB**, registre foncier.

## 5 · Architecture (en bref)

```
MOTEUR NEUTRE (universel)                         JURISDICTION PACK : CH (1er)
• ontologie projet/contrainte/décision/preuve     • modèle de phases SIA 112/102
• cycle phase-aware (le modèle de phases = pack)   • sources fédéral/cantonal/communal/parcelle
• schéma d'unité canonique + 2-RAG                 • connecteurs: fedlex, geo.admin, RDPPF, CAMAC
• contrat de preuve + registre de traçabilité      • coûts CFC/eCCC/NPK (.crbx) ; normes SIA/AEAI
• API/MCP d'adaptateurs (tool-neutral)             • packs de langue FR/DE/IT
```

Références de construction:
[`architecture/adr-0001-neutral-engine-and-jurisdiction-packs.md`](architecture/adr-0001-neutral-engine-and-jurisdiction-packs.md),
[`nomos/nomos-archi-schema-v0.md`](nomos/nomos-archi-schema-v0.md),
[`nomos/phase-aware-constraint-matrix.md`](nomos/phase-aware-constraint-matrix.md),
[`architecture/trust-contract-and-ledger.md`](architecture/trust-contract-and-ledger.md),
[`architecture/project-knowledge-regime.md`](architecture/project-knowledge-regime.md),
[`architecture/project-memory-contract.md`](architecture/project-memory-contract.md),
[`architecture/local-model-bridge-prototype.md`](architecture/local-model-bridge-prototype.md),
[`research/swiss-phase-lifecycle-matrix.md`](research/swiss-phase-lifecycle-matrix.md),
[`research/pilot-source-registry.md`](research/pilot-source-registry.md),
[`research/bim-adapter-capability-map.md`](research/bim-adapter-capability-map.md),
[`research/swiss-competitions-and-study-mandates.md`](research/swiss-competitions-and-study-mandates.md),
[`research/swiss-construction-management-tools.md`](research/swiss-construction-management-tools.md),
[`research/competitive-positioning.md`](research/competitive-positioning.md),
[`product/business-model-and-pricing.md`](product/business-model-and-pricing.md),
[`architecture/multilingual-regulatory-graph.md`](architecture/multilingual-regulatory-graph.md),
[`cost/sia102-fee-profitability-copilot.md`](cost/sia102-fee-profitability-copilot.md),
[`cost/eccc-npk-cfc-bridge.md`](cost/eccc-npk-cfc-bridge.md),
[`permit/vd-camac-permit-completeness.md`](permit/vd-camac-permit-completeness.md),
[`compliance/phase33-compliance-gates.md`](compliance/phase33-compliance-gates.md),
[`specs/mvp2-permit-dossier-assistant.md`](specs/mvp2-permit-dossier-assistant.md).

## 6 · Contexte suisse — 3 niveaux + parcelle

| Niveau | Ce qu'il fixe | Où vivent les données |
|---|---|---|
| Fédéral | Cadre (LAT/RPG, OPB bruit, LHand, AEAI incendie, énergie) | fedlex, map.geo.admin.ch |
| Cantonal (VD) | Procédure de permis, énergie, l'essentiel des règles (LATC) | géoportail VD, prestations.vd.ch |
| Communal | Plan d'affectation + règlement : zones, indices, hauteurs, distances | commune ; surfacé via géoportail |
| Parcelle | RDPPF/ÖREB, servitudes (registre foncier), DS bruit | cadastre RDPPF, registre foncier |

Cette fragmentation est **le fossé concurrentiel** : aucun outil étranger ne la couvre.

## 7 · Feuille de route MVP (séquence rebasée)

| Jalon | Cœur | Statut |
|---|---|---|
| **MVP0 Foundation** | moteur + schéma NOMOS + packs + contrat de preuve | ✅ moteur stdlib, **261 checks** |
| **R1A Agent → API → logiciel** | boucle agentique, bridge Archicad, intention, dry-run diff, approval/ledger | ✅ **dans le produit** ; connexion Archicad **live** (lecture seule) faite (#190) |
| **R1B Workspace projet** | parcelle → contraintes + enveloppe sourcées, rapport, mémoire | ✅ **productisé** : app multi-projets / multi-comptes (W5) |
| **R2 Permis & Opposition** | radar d'opposition + complétude dossier (phase 33) | ✅ **par projet** : dépôt de pièces permis, opposition, conformité (W6) |
| **R3 Mémoire & Ledger** | décisions, preuves, approvals, handoffs | ✅ runtime : mémoire + ledger + approbations scoped (W4) |
| **R4 Adapters live** | Archicad JSON réel d'abord, puis IFC/Speckle/Revit/Rhino/… | 🟢 Archicad live **read-only** fait ; mutation live + autres adapters à venir |
| **R5/R6 Économie + chantier** | honoraires, coûts, soumissions, PV, défauts, handover | ✅ **par projet** : coûts & appels d'offres, chantier & remise (W6) |

La traduction logicielle de cette séquence vit désormais dans
[`planning/software-roadmap.md`](planning/software-roadmap.md) et
[`planning/epics-and-backlog.md`](planning/epics-and-backlog.md).

## 8 · Ce qui est déjà fonctionnel — le pilote ([`../pilot/`](../pilot/))

Code Python (stdlib), ancré sur les **API publiques gratuites** suisses, poussé sur `main` :

| Outil | Rôle | Statut |
|---|---|---|
| `oereb.py` | parseur OEREB/RDPPF VD — **toute parcelle** (zone, DS, alignements, surface RF, lois) | ✅ |
| `mvp1_demo.py` | parcelle → contraintes + **enveloppe constructible** sourcée | ✅ |
| `opposition_radar.py` | radar de risque d'opposition (patrimoine, bruit, voisinage, ombres…) | ✅ prototype |
| `selector.py` | **route réglementaire** : fédéral + canton + commune | ✅ |
| `lausanne/` + `pully/` | **2 communes ingérées**, sourcées (Lausanne PGA 2006 géométrique/IUS ; Pully RCATC 2017 IOS) | ✅ |
| `fiche.py` | **fiche A4 imprimable** (contraintes + enveloppe + radar) | ✅ |
| `validate_packs.py` | contrat/versioning des packs réglementaires (stdlib) | ✅ |
| `validate_matrix.py` | validation de la matrice phase-aware MVP1 | ✅ |
| `validate_permit.py` | pre-check de complétude dossier VD/ACTIS-CAMAC avec détection de manquants | ✅ |
| `validate_compliance.py` | gates phase 33 énergie/incendie/accessibilité/structure + BIM contractuel | ✅ |
| `validate_research.py` | validation matrice phases SIA + registre sources pilote | ✅ |
| `validate_memory.py` | mémoire projet cross-phase + requêtes avec provenance | ✅ |
| `validate_cost.py` | honoraires SIA 102 + pont eCCC/NPK/CFC + round-trip `.crbx` | ✅ |
| `model_bridge_demo.py` | prototype dry-run du bridge modèle local Archicad JSON | ✅ |
| `model/design_intent_fixture.json` | intention structurée de dessin/modèle pour le demo agent → API → logiciel | ✅ |
| `agent_software_demo.py` | CLI dédié R1A : inspection modèle, items générés, dry-run diff, état d'approbation | ✅ |
| `trust.py` | footer/contrat de rendu non-autoritaire partagé par les sorties pilote | ✅ |
| `selfcheck.py` | tests hors-ligne | ✅ 261/261 |

**Preuve réelle** (parcelle Place de la Palud, Lausanne, nº 10072) : Zone centrale 15 LAT · DS III ·
alignements · LATC/LAT — en quelques secondes, **sans maquette ni identifiant**. Validé aussi sur Pully.

```
python pilot/mvp1_demo.py        ["adresse"|EGRID] [hauteur]
python pilot/opposition_radar.py ["adresse"]        [hauteur]
python pilot/fiche.py            ["adresse"]        [hauteur]   # → pilot/out/*.html
python pilot/selector.py    ·    python pilot/validate_packs.py    ·    python pilot/selfcheck.py
```

> Limite assumée : l'**enveloppe numérique** (indices/hauteurs) n'est **pas** en open data — uniquement dans
> les PDF communaux → ingestion par commune (couche capitalisable). Le radar est **indicatif**.

Un premier contrat de pack versionné est documenté dans
[`architecture/jurisdiction-pack-contract.md`](architecture/jurisdiction-pack-contract.md) et validé par CI.
La matrice de cycle suisse et le registre de sources pilote sont également structurés dans `pilot/research/`
et validés par CI.

### 8b · Au-delà du pilote — le produit (app web)

Par-dessus le moteur, Aedifica tourne désormais comme **app web multi-tenant déployable** (FastAPI + Next.js,
design system Datum) — voir [`../README.md`](../README.md) §Product et
[`architecture/adr-0002-product-architecture.md`](architecture/adr-0002-product-architecture.md) :

- **Comptes & équipe** (org + utilisateurs, rôles owner/member/viewer), **projets** (créer/ouvrir/changer).
- **Surfaces SIA par projet** (données du projet, vides par défaut, jamais fabriquées) : Terrain & zonage
  (recherche live), Dossier de permis (**dépôt de pièces**), Opposition, Conformité, Coûts & appels d'offres,
  Chantier & remise.
- **Copilote IA · maquette** : boucle `inspecter → dry-run diff → approbation scoped → exécuter → ledger` ;
  **connexion Archicad live** (lecture seule) branchable par endpoint, repli replay sinon ; aucune mutation
  sans approbation `adapter_execution`.
- Persistance SQLAlchemy + Alembic, Postgres/SQLite, Docker/GHCR, CI (moteur 261 + suite produit + Alembic +
  **smoke E2E Playwright**). Déploiement : [`operations/deploy-runbook.md`](operations/deploy-runbook.md).

## 9 · Backlog & gouvernance

- Les premières vagues GitHub `AED-001` à `AED-080` sont fermées : elles ont servi à transformer les fondations
  en docs, contrats, fixtures, validations et preuve offline agent -> logiciel.
- La vague active est définie comme backlog logiciel dans
  [`planning/epics-and-backlog.md`](planning/epics-and-backlog.md) : `AED-081` à `AED-123`, soit 43 issues
  GitHub re-atomisées autour de la productisation R1B, puis R2/R3/R4/R5/R6.
  **Statut : les 43 issues sont implémentées** (package `aedifica/` + modules pilote, schémas,
  validateurs et surfaces Datum) avec gate de release vert
  (`python pilot/release_gate.py R1B` → 19 validateurs + selfcheck). Voir
  [`architecture/package-boundaries.md`](architecture/package-boundaries.md).
- **Phase produit (2026-06) :** un substrat de livraison a été construit (vagues W1/W3 — package `aedifica/db`,
  API FastAPI, app Next.js Datum, Postgres, Docker/GHCR, multi-tenant, ingestion de communes à la demande).
  Voir [`architecture/adr-0002-product-architecture.md`](architecture/adr-0002-product-architecture.md).
- **Réancrage (2026-06-02, décision B)** après le contrôle d'alignement
  [`review/direction-alignment.md`](review/direction-alignment.md) : le produit **n'est pas** la web-app de
  workspace réglementaire — c'est la **couche ArchiOS** (moteur + mémoire + **API universelle d'action** +
  agents). La prochaine vague **W4** expose dans le runtime la moitié top-down encore absente : **boucle
  d'action multi-logiciels** (dry-run → approbation → ledger), **requêtes mémoire**, et un **orchestrateur
  « prochaine étape par phase »** — pas de nouvelles surfaces CRUD. Backlog :
  [`planning/wave-4-action-layer-backlog.md`](planning/wave-4-action-layer-backlog.md).
- **Vagues W4–W7 mergées** (juin 2026) : boucle d'action + mémoire + orchestration (W4), app
  multi-projets/comptes (W5), profondeur **par projet** — permis/coûts/chantier + dépôt de pièces, sortie du
  statique (W6), et durcissement — docs, E2E Playwright, déploiement vérifié (W7). La **connexion Archicad
  live (lecture seule)** est faite (`#190`) et un **Partner Pilot Kit** prêt à dérouler existe
  ([`validation/partner-pilot-kit.md`](validation/partner-pilot-kit.md)).
- Les seules issues encore ouvertes sont **partner-gated** : exécuter la séance sur une vraie maquette
  (`#105`, `#115`, épic `#171`) — plus de code requis côté socle, il faut un poste Archicad partenaire.
- Les listes de delivery, Definition of Ready/Done, release gates et checklists démo vivent dans
  [`planning/development-checklists.md`](planning/development-checklists.md).
- Décisions tracées dans [`strategy/decisions.md`](strategy/decisions.md) ; corrections et dette historique
  restent visibles dans [`review/foundations-audit.md`](review/foundations-audit.md).

## 10 · Décisions prises & questions ouvertes

**Prises** (voir [`strategy/decisions.md`](strategy/decisions.md)) : wedge **hybride** (intelligence réglementaire +
fil Archicad) ; pilote **Vaud / Lausanne** ; cold-start **hybride** (ingestion à la demande + corpus semé) ;
**route réglementaire** composable ; projet **contexte-first** pour les petits projets.

**Ouvertes pour le passage logiciel** : app locale web vs desktop-local ; stockage `files + manifest` seul vs
SQLite local ; version Archicad live disponible pour le `R1A` réel ; prochaine commune à ingérer après Lausanne/Pully ;
prochaine commune à ingérer après Lausanne/Pully.

## 11 · Prochaines étapes

1. **Dérouler le Partner Pilot Kit** avec le bureau partenaire : pré-vol + séance **read-only** sur sa vraie
   maquette Archicad (inspecter → audit → dry-run diff → garde-fou), puis décision (`#105`, `#115`).
2. Sur « go » : ouvrir la **mutation live** scoped + réversible (au-delà de la lecture seule), puis câbler les
   autres adapters (IFC/Speckle/Revit/…).
3. **Largeur juridictionnelle** : ajouter des communes/cantons réels via l'ingestion à la demande — dès qu'on
   dispose de **vraies sources réglementaires** (pas de fabrication).
4. **Mise en production** : déployer le stack (Postgres + API + web) selon
   [`operations/deploy-runbook.md`](operations/deploy-runbook.md) quand l'hébergement est décidé.

## 12 · Carte des documents (où lire quoi)

| Pour… | Lire |
|---|---|
| Le pitch visuel (1 page) | [`pitch/aedifica-one-pager.html`](pitch/aedifica-one-pager.html) |
| Le brand book Datum canonique | [`design-system/aedifica-brand-book.html`](design-system/aedifica-brand-book.html) |
| Le plan de développement logiciel | [`planning/software-development-plan.md`](planning/software-development-plan.md) |
| La roadmap d'exécution | [`planning/software-roadmap.md`](planning/software-roadmap.md) |
| Les épics et le backlog candidat | [`planning/epics-and-backlog.md`](planning/epics-and-backlog.md) |
| Les listes de delivery | [`planning/development-checklists.md`](planning/development-checklists.md) |
| La vision complète | [`vision.md`](vision.md) · [`product/holistic-assistance.md`](product/holistic-assistance.md) |
| Le garde-fou de scope produit | [`product/scope-realignment.md`](product/scope-realignment.md) |
| Le design system validé | [`design-system/README.md`](design-system/README.md) · [`design-system/design-system-manifest.json`](design-system/design-system-manifest.json) |
| Le challenge + brainstorm | [`strategy/challenge-and-brainstorm.md`](strategy/challenge-and-brainstorm.md) |
| Le métier d'architecte (réel, SIA) | [`strategy/architect-reality.md`](strategy/architect-reality.md) |
| La pile réglementaire suisse | [`strategy/swiss-regulatory-stack.md`](strategy/swiss-regulatory-stack.md) |
| L'architecture de connaissance | [`strategy/knowledge-architecture.md`](strategy/knowledge-architecture.md) |
| Le régime de connaissance projet | [`architecture/project-knowledge-regime.md`](architecture/project-knowledge-regime.md) |
| La mémoire projet cross-phase | [`architecture/project-memory-contract.md`](architecture/project-memory-contract.md) |
| La valeur phase par phase | [`strategy/phase-value-catalog.md`](strategy/phase-value-catalog.md) |
| La matrice phase par phase validée | [`research/swiss-phase-lifecycle-matrix.md`](research/swiss-phase-lifecycle-matrix.md) |
| Le registre de sources pilote | [`research/pilot-source-registry.md`](research/pilot-source-registry.md) |
| Les adapters BIM/CAD | [`research/bim-adapter-capability-map.md`](research/bim-adapter-capability-map.md) |
| Le prototype de bridge modèle | [`architecture/local-model-bridge-prototype.md`](architecture/local-model-bridge-prototype.md) |
| Concours et MEP | [`research/swiss-competitions-and-study-mandates.md`](research/swiss-competitions-and-study-mandates.md) |
| Outils direction travaux | [`research/swiss-construction-management-tools.md`](research/swiss-construction-management-tools.md) |
| Positionnement concurrentiel | [`research/competitive-positioning.md`](research/competitive-positioning.md) |
| Business/pricing | [`product/business-model-and-pricing.md`](product/business-model-and-pricing.md) |
| Graphe multilingue | [`architecture/multilingual-regulatory-graph.md`](architecture/multilingual-regulatory-graph.md) |
| Le copilote honoraires | [`cost/sia102-fee-profitability-copilot.md`](cost/sia102-fee-profitability-copilot.md) |
| Le pont eCCC/NPK/CFC | [`cost/eccc-npk-cfc-bridge.md`](cost/eccc-npk-cfc-bridge.md) |
| La spec MVP1 | [`specs/mvp1-parcel-constraints-intake.md`](specs/mvp1-parcel-constraints-intake.md) |
| La spec R1A agent → logiciel | [`specs/mvp1a-agent-to-architecture-software-demo.md`](specs/mvp1a-agent-to-architecture-software-demo.md) |
| La spec assistant permis | [`specs/mvp2-permit-dossier-assistant.md`](specs/mvp2-permit-dossier-assistant.md) |
| La spec Auto-BIM / Model Intelligence | [`specs/later-model-intelligence.md`](specs/later-model-intelligence.md) |
| La spec tender/quantités | [`specs/later-tender-quantity-workflows.md`](specs/later-tender-quantity-workflows.md) |
| La spec direction travaux | [`specs/mvp4-direction-travaux-agentique.md`](specs/mvp4-direction-travaux-agentique.md) |
| La spec voice-to-design | [`specs/later-voice-to-design.md`](specs/later-voice-to-design.md) |
| La preuve API (Lausanne) | [`strategy/poc-lausanne-parcel.md`](strategy/poc-lausanne-parcel.md) |
| Le pilote (code) | [`../pilot/README.md`](../pilot/README.md) |

_Dernière mise à jour : 2026-06-04 (produit W1–W7 mergé ; connexion Archicad live + Partner Pilot Kit)._
