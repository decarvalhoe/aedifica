# Wave 23 — Industrialisation du seam (cross-repo NOMOS × Aedifica)

> **Constat (2026-06-11, après W21/W22).** La chaîne canonical-first est fermée
> et prouvée (source officielle → atomes ELI → bundle certifié → import →
> citation, cf. clôture de #320). W23 l'industrialise : les PDF communaux
> deviennent des bundles citables, le pack AEC se matérialise, l'artefact se
> publie et s'importe tout seul, la couverture des sources cantonales se
> complète. Quatre chantiers, deux repos, exécution inline.

## Chantiers

| ID | Chantier | Repo | Contenu / DoD |
|---|---|---|---|
| W23-1 | **Câblage `.pdf` → atomize/bundle** (même couture que NOMOS#587) | NOMOS | Le cœur d'extraction VRC-30 (lignes positionnées + pages unsupported) exporté de `fidelity` et consommé par `atomization.AtomizePDF` (locators `page+ligne+Y`, claim ladder) ; `atomize units --format pdf` ; `bundle.Build` accepte `.pdf` — **refus explicite** si une page est hors claim (un bundle ne porte jamais une source qu'il ne peut pas couvrir). DoD : fixture PDF générée → bundle valide → import + citation Aedifica, et PDF partiellement scanné → build refusé en nommant les pages. |
| W23-2 | **Géoportail cantonal (contrat 4→5) + fixtures offline** | NOMOS | `#BuiltEnvironmentSourceConnectors` passe de « exactement 4 » à « ≥ 4 » + famille `geoportail_cantonal` ; fetch réel d'un GetCapabilities cantonal machine (WMS/WFS) avec reçu committé ; le gate Python apprend la 5ᵉ famille ; **fixture offline par connecteur** (snippets réalistes embarqués, marqueurs de payload assertés sans réseau). DoD : 5/5 familles fetched, gates verts, zéro réseau dans la CI. |
| W23-3 | **Publication d'artefact + import programmé** (aedifica#323) | NOMOS + Aedifica | NOMOS : workflow `bundle-release` qui émet le bundle canonique + `facets-vocab.json` et les publie en assets de release (`publish_mode: artifact_only` déjà tracé). Aedifica : cron (pattern `refresh-communes`) qui télécharge l'artefact publié, vérifie `schema_version` + hash, et l'importe sur le démo via l'API (org ops dédiée, tolérance « version immuable déjà importée »). DoD : le démo consomme un artefact publié sans intervention. |
| W23-4 | **Pack AEC suisse (mince)** (VRC-34, NOMOS#571) | NOMOS | Dans la limite de ce que D1/D2 (contrat de pack + `pack validate`, #563/#564) permettent déjà : vocabulaires AEC (disciplines/activités SIA, hash-only pour les références payantes), **lens-presets archi** (« archi-conception », « DT-chantier », « permis ») exprimés sur les facettes existantes, golden corpus VD/Lausanne (synthétique license-safe) émis en bundle et **cité via les presets** dans Aedifica. DoD : presets exercés par tests (le preset « permis » filtre ce que « conception » laisse passer), corpus AEC vert de bout en bout. |

## Ordre d'exécution (levier décroissant, dépendances)

W23-1 (ferme la promesse PGA/PAZ) → W23-2 (couverture sources complète) →
W23-3 (le vendoring meurt) → W23-4 (le vertical se matérialise).

## Hors scope W23

OCR (hors claim tant que non prouvé) ; tagged-PDF ; signature Sigstore des
bundles (VRC-40) ; `pack validate` complet (VRC-21, prérequis partiel de W23-4
— on livre ce qui tient sur les gates existants).

## Références

`wave-22-documentaire-canonical-first.md` · NOMOS `docs/45` §4 C1/C2/C4/D5 ·
clôtures : aedifica#320, NOMOS#567/#568/#574 · successeur publication : aedifica#323.
