# Wave 22 — Le documentaire aligné canonical-first

> **Constat (2026-06-11, après W21).** La couche documentaire vit à côté de la
> couche savoir au lieu de l'alimenter : `POST /documents/{id}/validate` pose le
> niveau **et rien d'autre** ; `ProjectKnowledgeChunk` (le silo projet réservé au
> canon promu depuis W20) n'a **aucun producteur** ; l'ingestion communale est
> traçable en base (CommunePack + IngestionJob + OFS live W18) mais ni pilotable
> ni lisible en UI ; la récolte de documents officiels reste manuelle. **W22 =
> la doctrine de `development-approach.md` §3 (« canon promu ») appliquée au
> documentaire existant, point par point.**

## Principe

La validation par l'architecte maître **est** l'acte de promotion (séance
Etienne §E : sourçage canonique manuel + injection manuelle d'une source).
Trust honnête : un savoir promu **n'usurpe jamais** le `certified` officiel —
tier plafonné à `indicative`, provenance `user_promoted`, confidentiel en silo
projet. Tout additif, flag NOMOS pour les surfaces de retrieval.

## Chantiers

| ID | Chantier | Prio | Contenu / DoD |
|---|---|---|---|
| W22-1 | **Canon promu — document canonique ⇄ silo projet** | P0 | Valider un document en **canonique** (avec un **extrait citable** fourni/édité par l'architecte) crée/actualise un `ProjectKnowledgeChunk` (`chunk_id=doc:<id>`, hash du texte, `trust_tier=indicative`, `provenance=user_promoted`, embedding immédiat) ; tout autre niveau **rétracte** le chunk ; suppression du document = suppression du chunk. La doctrine cite alors les pièces de l'atelier (« Indicatif · Promu atelier », décision humaine maintenue). UI : éditeur d'extrait au clic « Canonique », chip « citable », compteur Projet du corpus (W21-2) qui bouge. DoD : pytest (promotion/rétractation/isolation projet/flag-off inchangé) + e2e boucle complète (valider → citer → rétrograder → abstention). |
| W22-2 | **Ingestion officielle traçable** | P1 | Surface admin des packs communaux : jobs d'ingestion (statut, sources, notes), bouton promote (`/communes/{id}/promote`), registre des sources officielles par pack (`source_authority`, `valid_as_of`, `review_due`), fraîcheur OFS + « règlement à l'étude » reliés. DoD : un pack se suit de la demande à la promotion sans toucher la DB. |
| W22-3 | **Récolte automatisée des référentiels officiels** | P1/P2 | La couture NOMOS (CKM-10, #492) : connecteurs sources CH (Fedlex/ELI, RDPPF/ÖREB, swisstopo, OFS) + pipeline PDF PGA/PAZ → **bundle émis**, qu'Aedifica importe déjà (W21-2). Côté Aedifica : suivi du seam, import programmable (cron) d'un bundle publié, et **aucune ingestion sauvage** — uniquement l'artefact certifié. DoD : un bundle produit par les connecteurs NOMOS s'importe et se cite sans glue. |

## Hors scope W22

Extraction de texte PDF côté Aedifica (c'est l'atomisation NOMOS) ; promotion
au `certified` (réservé au pipeline officiel certifié) ; granularité d'accès
par donnée (différée en séance).

## Références

`development-approach.md` §3 (canon promu, trust honnête) ·
`session-2026-06-05-etienne-synthesis.md` §E ·
`nomos-pivot-masterplan.md` (CKM-03 promotion, CKM-10 connecteurs) ·
`wave-21-surfaces-terrain.md` (les surfaces que W22 alimente).
