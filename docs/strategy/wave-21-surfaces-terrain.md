# Wave 21 — Surfaces dédiées & test terrain (l'OS Archi rendu visible)

> **Constat (2026-06-11).** La direction validée en séance avec Etienne (2026-06-05,
> cf. `session-2026-06-05-etienne-synthesis.md`) est **largement construite** côté
> backend *et* UI (W9–W18), et la couche savoir NOMOS (W19/W20) est prouvée par tests
> e2e — mais : (a) le démo Fly est **gelé au 7 juin** (release v42, déploiement manuel,
> 19 commits de retard), (b) la couche NOMOS n'a **aucune surface** (W19-04/W19-05
> prévus au masterplan, pas livrés), (c) quelques promesses de séance restent sans UI
> complète. **W21 = rendre visible, testable par Etienne, et boucler point par point.**

## Principe

Pas (ou peu) de nouvelles capacités backend : on **expose ce qui existe** et on prépare
le **test terrain réel** (accord de séance §10 : « que ça fonctionne pour de vrai, qu'on
puisse tester »). Doctrine inchangée (`development-approach.md`) : additif, flag OFF par
défaut, citations sourcées ou abstention, l'architecte décide.

## Chantiers

| ID | Chantier | Prio | Contenu / DoD |
|---|---|---|---|
| W21-0 | **Démo à jour, en continu** | P0 ⚡ | `flyctl deploy` immédiat ; puis job de déploiement auto sur `main` (ou étape release outillée) pour que le démo ne regèle plus silencieusement. DoD : `/api/health` expose `features` ; smoke e2e pointable sur le démo. |
| W21-1 | **Copilote · Question doctrine (cite-or-abstain)** | P0 | Panneau Q&A dans Copilote → `POST /copilote/nomos` : réponse avec **citations** (source_path, span, trust_tier — réutilise `TrustMeta`) ou **abstention explicite** (`requires_human_decision` → « hors corpus, décision humaine »). Flag-gated : surface absente si `features.nomos=false`. DoD : e2e Playwright flag ON + OFF. |
| W21-2 | **Documents & sources · corpus juridictionnel** | P0 | État du corpus de la juridiction du projet (nb chunks, fraîcheur, répartition trust tiers) + **import de bundle NOMOS** (admin, flag-gated) avec provenance/facettes visibles. DoD : le golden bundle (74 nœuds) importé et visible en UI. |
| W21-3 | **Mémoire/Terrain · facettes & lens** | P1 | Filtres par facette/tier sur les claims et sources ; le « trier · retrouver » d'Etienne appliqué au savoir réglementaire. |
| W21-4 | **Opposition crédible v1** | P2 | (Réserve d'Etienne — approfondir, pas vitrine.) Recalcul sur la **doc canonique du dossier** avec citations ; wording ciblé (« attention à CE point ») au lieu d'un score générique. Scan des décisions publiques/jurisprudence : différé. |
| W21-5 | **Compléments séance** | P1/P2 | Sous-groupes d'intervenants (arborescence groupe ⊃ sous-groupe ⊃ personne) ; **intervenants par phase** sur le tableau de bord (feuille SIA Vaud) ; étape « validation des phases » au flow de création de projet ; (étude) double référentiel SIA 102:2020 / 102:2024 (phase 0 + scission 41/42). |
| W21-6 | **Test terrain Etienne** | P0 (dépend W21-0) | Projet réel seedé, boucle de friction active (captures `friction`), protocole `docs/validation/partner-agent-demo-protocol.md`, journal de frictions → issues. |

## Hors scope W21

Prédictif « pondération apprise » par personne (facteur ×3 d'Etienne) au-delà de
l'existant (`/tasks/predict` + benchmark atelier) ; scan public opposition ;
granularité d'accès par donnée (différée en séance).

## Références

`session-2026-06-05-etienne-synthesis.md` (la source des points A–M et des priorités) ·
`nomos-pivot-masterplan.md` (W19-04/W19-05 = les surfaces promises) ·
`development-approach.md` (doctrine) · `phase-value-catalog.md` (intelligence par phase).
