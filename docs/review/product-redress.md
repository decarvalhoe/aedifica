# Bilan & roadmap de redressement produit

> Status: **point de redressement, 2026-06-04.** Après une vague de features rapide
> (W1–W7), l'expérience produit a décroché : l'app lit comme un outil
> d'informaticien, pas comme un assistant d'architecte. Ce document fait le bilan
> honnête, ré-ancre l'objectif initial, et pose une roadmap pour en faire une
> **vraie application professionnelle et commercialisable**.

## 1 · Le constat (cause racine)

On a livré beaucoup de **capacité**, mais la **cohérence produit** n'a pas suivi :
la valeur n'est pas lisible, le parcours n'est pas le parcours d'un architecte, et
l'identité visuelle a dérivé. **Bonne nouvelle** : le problème est surtout de
*présentation et de parcours*, pas de capacité manquante (voir §2).

## 2 · Bilan — ce qui est livré & fonctionnel, par phase SIA

La capacité couvre déjà **presque tout le mandat SIA**. Ce qui manque, c'est de la
présenter *comme un parcours de phase*.

| Phase SIA | Ce que fait l'architecte | Quick-win livré | État | Surface actuelle |
|---|---|---|---|---|
| **0 · Intake** | brief, parcelle, contraintes | parcelle → fiche de contraintes **sourcée** | ✅ | « Terrain & zonage » |
| **11 · Faisabilité** | capacité constructible | enveloppe (indices/hauteurs/distances) | ✅ | (dans Terrain) |
| **31 · Avant-projet** | concept, surfaces, coût | coût ordre de grandeur | 🟡 | (dans Coûts) |
| **32 · Projet / BIM** | coordination, métadonnées BIM | **Copilote Archicad** : inspect → dry-run → approbation → ledger (live #190) | ✅ | « Copilote IA » |
| **33 · Permis** | dossier, opposition | radar d'opposition + complétude dossier + gates conformité | ✅ | « Permis / Opposition / Conformité » |
| **41 · Appel d'offres** | métré, soumissions | coûts CFC/eCCC + comparatif | ✅ | « Coûts & appels d'offres » |
| **52 · Chantier** | PV, défauts, suivi | check-list remise + registre défauts | ✅ | « Chantier & remise » |
| **6 · Exploitation** | mémoire projet | inconnues + journal interrogeables | ✅ | « Mémoire » |

**Lecture :** un quick-win existe pour quasiment chaque phase. Le redressement est
donc surtout un **ré-emballage** (parcours + identité + langage), pas une
reconstruction du moteur.

## 3 · L'objectif, ré-ancré (depuis les docs fondatrices)

> Aedifica = **ArchiOS Suisse** : un assistant qui soutient l'architecte **à chaque
> phase SIA** — de la première fiche de contraintes à la remise — *sourcé, tracé, et
> capable d'agir dans ses outils sous son approbation*. « Parler à une IA qui
> dessine » ≈ **5 %** de la valeur ; le reste, c'est le **mandat entier**.
> (cf. `strategy/phase-value-catalog.md`, `vision.md`, `strategy/decisions.md`.)

Cible : l'**architecte suisse** (bureau petit/moyen), pas l'informaticien.
Colonne vertébrale = **le parcours de phase SIA**.

## 4 · Le problème, nommé (ce qui doit être redressé)

1. **Pas de colonne vertébrale par phase.** Liste plate d'onglets (terrain, permis,
   coûts…) → on ne voit pas *où on en est dans le projet* ni *quoi faire ensuite*.
2. **On ne comprend pas à quoi sert l'app.** Aucune accroche/valeur en langage
   architecte ; pas de « voici ce qu'Aedifica fait pour vous ».
3. **Langage d'informaticien.** « données de référence », « à venir », clés d'accès,
   `data_basis`, badges techniques → ça parle dev, pas métier.
4. **Login brouillon.** La « clé d'accès à recopier » n'est pas une vraie
   authentification professionnelle.
5. **DA abandonnée.** Une **DA Datum complète existe** (`design-system/` :
   `aedifica-datum-ui.css`, composants, logos, iconographie, brand book) — l'app a
   dérivé vers un CSS bricolé minimal qui ne l'utilise pas.

## 5 · Roadmap de redressement (vers une app pro & commercialisable)

**Principe : zéro nouvelle capacité tant que le parcours et l'identité ne sont pas
clairs.** On ré-emballe le livré autour de l'architecte.

- **R1 — Parcours par phase SIA (la refonte d'IA).** L'app s'organise autour de la
  **timeline SIA** du projet : on voit la phase courante, ce qu'Aedifica fait *ici*,
  et le **prochain pas**. Les features existantes deviennent les quick-wins *de leur
  phase*. Un « où en est-on ? » lisible d'un coup d'œil.
- **R2 — Restaurer la vraie DA Datum.** Reconstruire l'app sur
  `design-system/aedifica-datum-ui.css` + composants + **logos** + iconographie ;
  supprimer le CSS bricolé. Identité cohérente, pro, suisse.
- **R3 — Langage & flow architecte.** Retirer le jargon dev ; chaque écran a un but
  évident en mots métier et un flow clair (entrée → action → résultat → pas suivant).
- **R4 — Auth propre.** Vrai login (e-mail + mot de passe **ou** magic link) ; fin de
  la clé à recopier ; onboarding net.
- **R5 — Valeur & commercialisation.** Accroche claire (« à quoi ça sert »),
  onboarding guidé, états vides utiles, un **parcours de démo** vendeur ; base d'une
  offre (un bureau / un architecte).

## 6 · Ce qui ne change pas (et reste solide)

Le **moteur** (261 checks, sourcé/inconnu), la **boucle d'action** + garde-fous, la
**persistance** multi-projets, la **connexion Archicad live** (#190), le **socle
partenaire**. On garde tout — on le **réexpose** correctement.

## 7 · Décisions prises (2026-06-04)

1. **Double navigation** : par **phase SIA** *et* par **tâche/domaine** — les deux
   doivent être aussi claires l'une que l'autre (timeline de phase + accès direct
   aux capacités, croisés).
2. **Accueil combiné & soigné** : **recherche d'adresse → contraintes** *et*
   **liste des projets avec avancement SIA**, sur le même écran, avec un vrai
   travail UX/UI efficace et orienté utilisateur.
3. **Auth** : **e-mail + mot de passe** (vrai login ; fin de la clé à recopier).
4. Colonne vertébrale = parcours SIA, confirmé.

## 8 · Exécution (wave « Redressement »)

Ordre, en incréments vérifiés visuellement :
1. **Fondation DA** : reconstruire sur `design-system/aedifica-datum-ui.css` +
   polices + **logos** ; retirer le CSS bricolé.
2. **Shell + double nav** : timeline phase SIA + nav par tâche, cohérentes.
3. **Accueil** combiné (recherche adresse + projets/avancement SIA).
4. **Auth** e-mail + mot de passe (backend : hash + login/register ; UI propre).
5. **Langage architecte** sur chaque surface (retrait du jargon dev).
6. **Polish** valeur/onboarding/états vides → app présentable & commercialisable.
