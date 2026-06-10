# NOMOS × Aedifica — Audit d'implémentation réel (post-pivot CKM/W19)

> Audit adversarial du code **réellement mergé** après l'exécution autonome du pivot
> (NOMOS epic CKM #481 + Aedifica epic W19 #278). Méthode : lecture des diffs mergés,
> `cue vet`, `go test`, `pytest`, et **end-to-end flag-ON contre l'API HTTP réelle**.
> Consigne : présumer STUB jusqu'à preuve du contraire ; **CI-verte ≠ substance**.
> Date : 2026-06-10. Toolchain : go 1.26.2 · cue 0.16.1 · python 3.13.11.

## Verdict en une phrase

**Zéro théâtre (0 stub / 22 issues), mais un écart net entre les titres d'issues et la
réalité — asymétrique : Aedifica a livré une intégration qui *marche vraiment* (prouvée
end-to-end), NOMOS a livré des *contrats + validateurs + CI*, pas l'implémentation dans
son moteur Go.**

| Repo | REAL | PARTIAL | STUB |
|---|---:|---:|---:|
| **Aedifica W19** (7) | **6** | 1 | 0 |
| **NOMOS CKM** (15) | 4 | **11** | 0 |

> **Le principe « deux produits vivants, zéro régression » a parfaitement tenu** : le
> moteur Go de NOMOS n'a pas été touché (CLI/profils/RBOK intacts), Aedifica flag-off =
> **182 tests verts**, cycle OFS-direct inchangé. Les produits sont **sains et sûrs** ;
> l'écart est de *profondeur/câblage*, pas de casse.

---

## 1. Aedifica W19 — la bonne surprise (6/7 REAL, prouvé end-to-end)

Hot-path prouvé contre le vrai FastAPI via HTTP : bundle → mapping champ-par-champ réel,
rollback transactionnel, refus des mauvais bundles, cite-or-abstain discriminant.

| Issue | Verdict | Évidence |
|---|---|---|
| W19-00 Keep-shipping guardrail | **REAL** | `nomos_enabled=False` par défaut ; 182 verts flag-off ; cycle OFS seed→ingest→promote inchangé ; endpoints renvoient `403 NOMOS_DISABLED` avant DB |
| W19-01 Bundle import adapter | **REAL** | `import_nomos_bundle` : mapping réel feeds/nodes → CommunePack/Source/Evidence/Claim (valeur IUS, spans, trace) ; `begin_nested()` rollback ; mauvais bundle → 422, **0 ligne fuitée** |
| W19-02 Facet-aware fields | **REAL** | Migration **additive nullable** (`trust_tier`/`provenance`/`facets` sur source+claim) ; colonnes **réellement lues** par import/doctrine/repository |
| W19-03 Lens-scoped retrieval | **PARTIAL** | Filtrage par facettes **réel** (WHERE include/exclude ; exclut un chunk confidentiel) **mais** `embedding vector(1536)` + pgvector + RLS **créés et jamais interrogés** → ranking **lexical**, pas sémantique |
| W19-04 Cite-or-abstain doctrine | **REAL** | Branche d'abstention réelle, forme 4-clés spec-exacte ; cite avec source_path+span+trust_tier ; s'abstient sur question sans recouvrement |
| W19-05 Trust-tier UI | **REAL** | `claims_for` expose trust_tier/provenance ; UI map certified/indicative/unverified + bandeau « Pas une autorité » (rendu visuel non testé navigateur) |
| W19-06 Design note → NOMOS core | **REAL** (doc) | `docs/strategy/w19-06-nomos-core-feedback.md` (116 l.) |

---

## 2. NOMOS CKM — « contrats réels, moteur non touché » (11/15 PARTIAL)

Pattern constant sur faceting/lens/promotion/métier : **CUE schemas réels + validateurs
Python réels + fixtures `invalid` qui échouent + gates CI**, mais **zéro intégration
Go** — l'`Atom`/`Chunk` Go ne porte aucune facette, la CLI n'a ni `--lens` ni
`--promote`, et les mécaniques vivent en **scripts Python sidecar** (`scripts/ckm_*.py`)
+ CUE, pas dans le moteur d'atomisation Go.

| Issue | Verdict | Évidence clé |
|---|---|---|
| CKM-00 Non-regression harness | **REAL** | `.github/workflows/ckm-non-regression.yml` + `scripts/ckm-non-regression.sh` (207 l., 11 étapes : go build/test, pytest, cue vet, e2e, RBOK-E2E) |
| CKM-01 Knowledge Faceting | **PARTIAL** | CUE `#FacetedAtom` réel, `invalid-trust-tier` rejeté par `cue vet` ; **mais** struct Go `Atom` n'a aucun champ `Facets` → schéma **orphelin** |
| CKM-02 Knowledge Lens | **PARTIAL** | `ckm_knowledge_lens_filter.py` fonctionne (exclut le plausible-non-applicable) ; **jamais appelé** par le pipeline Go ; pas de `--lens` |
| CKM-03 Canon Promotion | **PARTIAL** | `ckm_canon_promotion_validate.py` enforce droits/provenance/silo-confidentiel/certificat (invalid → exit 1, 3 findings) ; **aucun code Go** ne l'invoque |
| CKM-04 nature=metier | **PARTIAL** | `"metier"`/`"business_bible"` ajoutés aux enums ; **mais** « feed/TOC/ledger/gate green » sont des chaînes **déclarées** dans une fixture YAML, pas calculées par un run réel |
| CKM-05 Attestation supply-chain | **PARTIAL** | Prédicat réel **mais hash-only** : **zéro signature crypto** (pas de Sigstore/cosign/Rekor ; enveloppe cosign hardcode `Sig:""`) ; jamais émis par une commande CLI |
| CKM-06 Body-ledger Merkle | **PARTIAL + BUG** | Vrai Merkle **mais** preuves d'inclusion valides **uniquement pour un nb de feuilles puissance de 2** (cassent n=3,5,6,7,9…) ; le test passe car la fixture a 2 feuilles |
| CKM-07 Claim-boundary signé | **PARTIAL** | Prédicat de refus réel **mais hash-only, non signé** ; fonction test-only, jamais émise par la CLI |
| CKM-08 Cite-or-abstain gate | **REAL** | Calcule recall/precision réels, bloque exit 1, câblé en CI ; **caveat** : sous-score *faithfulness* **auto-déclaré**, non recalculé |
| CKM-09 Built-environment profile | **PARTIAL** | `cue vet` OK avec vrais IDs d'autorité (CH-RPG, VD-LATC, LAUSANNE-RPGA) ; **mais** fixture statique, `status: planned`, aucune source live |
| CKM-10 Connecteurs sources CH | **PARTIAL** | Manifeste CUE + tests **mais hashes synthétiques** (`sha256:1111…`) ; **aucun code** n'appelle Fedlex/swisstopo/RDPPF/OFS |
| CKM-11 Point-in-time | **REAL** | `ckm_point_in_time_resolve.py` : `effective_from/to`, sélectionne la version en vigueur, refuse les dates hors plage |
| CKM-12 Facet ontology | **PARTIAL** | Disjonction enforced **uniquement par term-scan Python** ; `cue vet` **accepte** `invalid-overlap` (CUE n'enforce pas la disjonction) |
| CKM-13 Bundle contract | **PARTIAL** | Schéma + validateur réels (refusent feed absent / rag-metadata orpheline) ; **aucun émetteur Go** (`nomos bundle` absent) → Aedifica consomme un bundle **hand-crafté** |
| CKM-14 Governance | **REAL** | Docs substantiels (wordmark clearance, FTO note, license register avec politique d'isolation AGPL `process_api_boundary`), testés au fond |

---

## 3. Constats transversaux (honnêtes)

1. **Asymétrie consommateur/moteur.** Le *consommateur* (Aedifica) a livré plus
   d'intégration réelle que le *moteur* (NOMOS) n'a livré de mécaniques réelles. NOMOS a
   reçu une excellente **couche contrat + validation + CI** (le bon premier pas
   additif, qui préserve la zéro-régression) — **pas l'implémentation moteur** que les
   titres d'issues laissent croire.

2. **⚠️ Violation de claim-boundary : « signé / Sigstore / certifié » n'est pas vrai.**
   CKM-05 et CKM-07 sont **hash-only** ; rien n'est cryptographiquement signé. C'est
   exactement le différenciant que le positionnement disait défendable (« supply-chain
   du savoir certifié ») — **revendiqué mais non implémenté**. La doctrine propre de
   NOMOS (« admet ce qu'il prouve, refuse le reste ») impose de **soit implémenter la
   signature, soit downgrader le claim** en « tamper-evident par hash ».

3. **Bug de correction réel (Merkle).** La DoD « chaque chunk indépendamment
   vérifiable » casse sur tout corpus réel (≠ puissance de 2).

4. **Pattern « script Python sidecar ».** Les mécaniques CKM vivent dans
   `scripts/ckm_*.py` + CUE, pas dans le moteur Go. Pour la productisation, il faut
   soit les remonter dans le moteur (Go), soit assumer explicitement une couche de
   validation séparée.

5. **Le bundle consommé par Aedifica est hand-crafté** (pas d'émetteur NOMOS) — la
   couture marche, mais sur un artefact que NOMOS ne produit pas encore.

---

## 4. Backlog de durcissement → issues

Priorisé par enjeu. Toujours **additif / zéro-régression**. Matérialisé : epic
**NOMOS #518** + Aedifica #295.

| # | Action | Issue | Repo |
|---|---|---|---|
| 1 | Signature crypto réelle (Sigstore/cosign) pour attestation + claim-boundary — OU downgrade honnête du claim | [CKM-H1 #519](https://github.com/RBOKproject/NOMOS/issues/519) | NOMOS |
| 2 | Merkle : preuves d'inclusion pour n quelconque + test négatif non-power-of-2 | [CKM-H2 #520](https://github.com/RBOKproject/NOMOS/issues/520) | NOMOS |
| 3 | Câbler `#Facets` dans le moteur Go (Atom/Chunk + atomisation) — débloque lens/promotion in-engine | [CKM-H3 #521](https://github.com/RBOKproject/NOMOS/issues/521) | NOMOS |
| 4 | Émetteur de bundle Go `nomos bundle` (produit le contrat CKM-13) | [CKM-H4 #522](https://github.com/RBOKproject/NOMOS/issues/522) | NOMOS |
| 5 | Un connecteur suisse **live** end-to-end (OFS ou Fedlex/ELI), hash réel | [CKM-H5 #523](https://github.com/RBOKproject/NOMOS/issues/523) | NOMOS |
| 6 | Recalculer la *faithfulness* dans la gate cite-or-abstain (ne pas faire confiance à l'auto-déclaré) | [CKM-H6 #524](https://github.com/RBOKproject/NOMOS/issues/524) | NOMOS |
| 7 | Retrieval **sémantique** réel pour le lens (brancher pgvector ; RLS exercé sur Postgres) | [W19-H1 #295](https://github.com/decarvalhoe/aedifica/issues/295) | Aedifica |

Secondaires (notés, non bloquants) : CKM-12 enforcer la disjonction en CUE (pas que
Python) ; CKM-04 faire **tourner** un corpus métier dans le pipeline au lieu de
déclarer « green ».

---

## Annexe — méthode & sources
4 agents d'audit adversariaux en parallèle (NOMOS core / flag-bearer / infra-pack /
Aedifica e2e). Chacun a lu les diffs mergés (`git show` des commits CKM/W19), exécuté
`cue vet` sur fixtures valid+invalid, `go test`, `pytest`, et — côté Aedifica — un
harnais e2e jetable contre l'API HTTP (supprimé après run, aucun fichier commité
modifié). Verdicts classés REAL/PARTIAL/STUB avec citations de code.
