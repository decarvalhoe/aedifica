# Aedifica — Plan global du projet

> **Point d'entrée.** Présentation structurée et à jour de l'ensemble du projet : vision, approche,
> architecture, feuille de route, et **ce qui est déjà fonctionnel**. Les documents détaillés sont liés
> en fin de page. État : concept + stratégie + **pilote fonctionnel** (mai 2026).

---

## 1 · En une phrase

Aedifica (**ArchiOS Suisse**) est une **couche d'intelligence réglementaire et projet** qui transforme une
parcelle + un programme + les registres suisses liants en **savoir de projet sourcé et phase-aware**, le
porte comme **mémoire continue** sur tout le mandat SIA, et assiste l'architecte dans son travail
**fiduciaire, de coordination, économique, réglementaire et de responsabilité** — pas seulement le dessin.

## 2 · Le problème

Un projet suisse est contraint dès le départ par une pile **fédéral → cantonal → communal → parcelle**,
éclatée sur **26 cantons, ~2 100 communes, 4 langues**, partiellement harmonisée et en dérive constante.
Ces contraintes vivent dans des PDF, géoportails, plans et la mémoire humaine. Les petits/moyens bureaux
ne sont **pas matures en BIM** (~35 %, marché au stade 2/4) : un produit « Auto-BIM » présuppose un modèle
qu'ils n'ont pas.

## 3 · Le message produit

> Le rêve « parler à une IA qui dessine » ≈ **5 %** de la valeur. Les **95 %** : un gain concret **à chaque
> étape**, de la gestion documentaire initiale à la livraison finale — sourcé, tracé, dans les outils du bureau.

Produit **généralisable** (pas verrouillé sur Archicad, pas un logiciel de dessin). Le bureau partenaire
(Archicad/BIM) est le **premier utilisateur pilote**, pas l'identité du produit.

## 4 · L'approche

- **Canonical-first (bottom-up)** : sources → unités canoniques traçables (NOMOS), avec provenance + validité temporelle.
- **Orchestration top-down** : des agents proposent / vérifient / journalisent ; l'humain reste responsable.
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
[`research/swiss-phase-lifecycle-matrix.md`](research/swiss-phase-lifecycle-matrix.md),
[`research/pilot-source-registry.md`](research/pilot-source-registry.md),
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

## 7 · Feuille de route MVP (séquence révisée)

| Jalon | Cœur | Statut |
|---|---|---|
| **MVP0 Foundation** | moteur + schéma NOMOS + packs + contrat de preuve | 🟡 en cours (corpus pilote semé) |
| **MVP1 Parcelle & Contraintes** | parcelle → contraintes + enveloppe sourcées (sans BIM) | ✅ **prototype fonctionnel** |
| **MVP2 Permis & Opposition** | radar d'opposition + complétude dossier (phase 33) | 🟡 radar + pré-check dossier/compliance prototypes |
| **MVP3 Honoraires, Coûts & Soumission** | copilote SIA 102 + pont eCCC↔NPK↔CFC | 🔜 |
| **MVP4 Mémoire & Coordination** | mémoire de projet continue + traçabilité | 🔜 |
| **Later** | Auto-BIM/Archicad (fil hybride), voice-to-design | 🔜 (fil démo Archicad actif) |

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
| `trust.py` | footer/contrat de rendu non-autoritaire partagé par les sorties pilote | ✅ |
| `selfcheck.py` | tests hors-ligne | ✅ 41/41 |

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

## 9 · Backlog & gouvernance

- **38 issues** GitHub, **6 milestones** (MVP0→4 + Later), labels de priorité P0–P3, [carte des dépendances #38](https://github.com/decarvalhoe/aedifica/issues/38).
- Code relié aux issues par commentaires de progression ([#15](https://github.com/decarvalhoe/aedifica/issues/15), [#23](https://github.com/decarvalhoe/aedifica/issues/23), [#24](https://github.com/decarvalhoe/aedifica/issues/24), [#26](https://github.com/decarvalhoe/aedifica/issues/26), [#27](https://github.com/decarvalhoe/aedifica/issues/27)).
- Décisions tracées dans [`strategy/decisions.md`](strategy/decisions.md) ; corrections en cours dans [`review/foundations-audit.md`](review/foundations-audit.md).

## 10 · Décisions prises & questions ouvertes

**Prises** (voir [`strategy/decisions.md`](strategy/decisions.md)) : wedge **hybride** (intelligence réglementaire +
fil Archicad) ; pilote **Vaud / Lausanne** ; cold-start **hybride** (ingestion à la demande + corpus semé) ;
**route réglementaire** composable ; projet **contexte-first** pour les petits projets.

**Ouvertes** : périmètre du « pack-0 » (séparation moteur/pack maintenant vs refactor plus tard) ; **modèle
économique / qui paie**.

## 11 · Prochaines étapes

1. Adjacence de voisinage réelle + ombres sur la volumétrie réelle (radar).
2. Passage à l'échelle : plus de communes (ingestion à la demande).
3. Formaliser le **moteur neutre + packs** (ADR [#22](https://github.com/decarvalhoe/aedifica/issues/22)).
4. Prochain bloc produit : copilote **honoraires/coûts**
   ([#29](https://github.com/decarvalhoe/aedifica/issues/29)/[#30](https://github.com/decarvalhoe/aedifica/issues/30)).

## 12 · Carte des documents (où lire quoi)

| Pour… | Lire |
|---|---|
| Le pitch visuel (1 page) | [`pitch/aedifica-one-pager.html`](pitch/aedifica-one-pager.html) |
| La vision complète | [`vision.md`](vision.md) · [`product/holistic-assistance.md`](product/holistic-assistance.md) |
| Le challenge + brainstorm | [`strategy/challenge-and-brainstorm.md`](strategy/challenge-and-brainstorm.md) |
| Le métier d'architecte (réel, SIA) | [`strategy/architect-reality.md`](strategy/architect-reality.md) |
| La pile réglementaire suisse | [`strategy/swiss-regulatory-stack.md`](strategy/swiss-regulatory-stack.md) |
| L'architecture de connaissance | [`strategy/knowledge-architecture.md`](strategy/knowledge-architecture.md) |
| Le régime de connaissance projet | [`architecture/project-knowledge-regime.md`](architecture/project-knowledge-regime.md) |
| La mémoire projet cross-phase | [`architecture/project-memory-contract.md`](architecture/project-memory-contract.md) |
| La valeur phase par phase | [`strategy/phase-value-catalog.md`](strategy/phase-value-catalog.md) |
| La matrice phase par phase validée | [`research/swiss-phase-lifecycle-matrix.md`](research/swiss-phase-lifecycle-matrix.md) |
| Le registre de sources pilote | [`research/pilot-source-registry.md`](research/pilot-source-registry.md) |
| La spec MVP1 | [`specs/mvp1-parcel-constraints-intake.md`](specs/mvp1-parcel-constraints-intake.md) |
| La spec assistant permis | [`specs/mvp2-permit-dossier-assistant.md`](specs/mvp2-permit-dossier-assistant.md) |
| La spec Auto-BIM / Model Intelligence | [`specs/later-model-intelligence.md`](specs/later-model-intelligence.md) |
| La spec tender/quantités | [`specs/later-tender-quantity-workflows.md`](specs/later-tender-quantity-workflows.md) |
| La spec direction travaux | [`specs/mvp4-direction-travaux-agentique.md`](specs/mvp4-direction-travaux-agentique.md) |
| La spec voice-to-design | [`specs/later-voice-to-design.md`](specs/later-voice-to-design.md) |
| La preuve API (Lausanne) | [`strategy/poc-lausanne-parcel.md`](strategy/poc-lausanne-parcel.md) |
| Le pilote (code) | [`../pilot/README.md`](../pilot/README.md) |

_Dernière mise à jour : 2026-05-29._
