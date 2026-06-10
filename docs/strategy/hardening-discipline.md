# Discipline de durcissement — « pas de *done* sans preuve adversariale »

> Mécanise la discipline révélée par l'audit (`nomos-implementation-audit.md`) pour
> qu'elle tienne **sans re-audit humain à chaque fois**. S'applique à NOMOS (#518,
> CKM-H1..H6) et Aedifica (#295), et à toute issue future qui revendique une capacité.
> Date : 2026-06-10.

## 0. Règle d'or

**Une issue n'est `done` que si une preuve *adversariale* montre qu'elle échoue quand la
capacité est absente.** Un test qui passe ne prouve rien ; un test qui **échoue sans le
fix** prouve. CI-verte ≠ substance.

## 1. Le tamis (par type de travail)

| Type | Preuve obligatoire avant `done` |
|---|---|
| **Correction de bug** | Reverter *uniquement* la source → le nouveau test **échoue au point prédit** → restaurer. (Modèle : CKM-H2/#520 — revert → échec exact à n=3 leaf 2.) |
| **Capacité crypto** (signature, attestation) | Un artefact réellement signé dont la **vérification échoue sur tamper** (altérer 1 octet → `verify` rouge). Pas de champ rempli, pas de `Sig:""`. |
| **Mécanique moteur** (faceting/lens/promotion) | **Consommée par le moteur Go** + un **test Go** qui l'exerce. Un schéma CUE + script Python sidecar **ne suffit pas** → au mieux `PARTIAL`. |
| **Résultat de pipeline** | **Calculé par un run réel**, jamais une chaîne `"green"` déclarée dans une fixture. |
| **Connecteur / fetch** | Un **vrai appel réseau read-only** + hash **réel** du contenu (pas `sha256:1111…`). |
| **Métrique / gate** | La métrique est **recalculée depuis les données** (ex. faithfulness via NLI), pas auto-déclarée ; un input adversarial fait **échouer** la gate. |

## 2. Garde-fou claim-boundary (le plus important)

Doctrine NOMOS : *« admet ce qu'il prouve, refuse le reste ».* Donc :

> **Aucun mot de capacité ne doit apparaître dans README / marketing / attestations sans
> un test adversarial qui le prouve. Sinon : downgrader le claim.**

| Mot revendiqué | Preuve requise | Sinon, dire… |
|---|---|---|
| « signé / signed / Sigstore / cryptographically verified » | signature réelle + verify échoue sur tamper | « tamper-evident **par hash** » |
| « certifié / certified » | chaîne source→canon→evidence vérifiable de bout en bout | « sourcé / traçable » |
| « connecté à la source officielle » | fetch live + hash réel | « snapshot daté » |
| « le moteur fait X » | code moteur + test moteur | « contrat + validateur de X » |

État honnête **actuel** (audit 2026-06-10) à corriger ou à refléter dans la doc :
attestation/claim-boundary = **hash-only, non signé** (CKM-05/07) ; faceting/lens/
promotion = **specs + scripts, pas dans le moteur** ; connecteurs CH = **snapshots
synthétiques** ; bundle = **pas d'émetteur**. Tant que ce n'est pas durci, la doc NOMOS
ne doit pas revendiquer mieux.

## 3. Barre d'acceptation par issue de durcissement

- **CKM-H1 #519 (signature)** — `done` ssi : cosign/Sigstore réel signe attestation +
  claim-boundary ; `verify` **échoue** après altération d'un octet (test) ; prédicats
  **émis par une commande CLI**. *Ou* downgrade explicite de tous les claims « signé ».
  **+ ajouter une CI-guard claim-boundary** (§4).
- **CKM-H2 #520 (Merkle)** — ✅ fait & audité (PR #525) : revert → échec n=3 leaf 2.
- **CKM-H3 #521 (facettes moteur)** — `done` ssi : `Atom`/`Chunk` Go portent `Facets`,
  l'atomisation les émet, **test Go** ; un atome sans facette requise est rejeté.
- **CKM-H4 #522 (émetteur bundle)** — `done` ssi : `nomos bundle` produit un bundle qui
  passe `ckm_bundle_validate.py`, et **Aedifica importe un bundle émis par NOMOS** (e2e),
  pas le hand-crafté.
- **CKM-H5 #523 (connecteur live)** — `done` ssi : fetch réseau réel d'une source, hash
  **réel**, body-ledger 0 octet non couvert ; test qui échoue si la source est absente.
- **CKM-H6 #524 (faithfulness)** — `done` ssi : recalcul depuis spans ; test adversarial
  (auto-déclaré haut + support absent → gate rouge).
- **W19-H1 #295 (sémantique lens, Aedifica)** — `done` ssi : colonne `embedding`
  peuplée **et** interrogée (cosinus/ANN pgvector) ; RLS **exercée sur Postgres réel** ;
  flag OFF ⇒ 182 tests inchangés.

## 4. Mécanisation (à implémenter dans CKM-H1)

Ajouter une **CI-guard claim-boundary** : un check qui **échoue** si README/attestations
contiennent un mot de la colonne « revendiqué » (§2) alors que la capacité correspondante
n'est pas prouvée (capability-flag off / dépendance cosign absente / pas de test
tamper-fail). C'est le passage de « discipline écrite » à « discipline appliquée par la
machine » — le seul moyen que ça tienne quand le fleet itère vite.

## 5. Zéro-régression (rappel permanent)

Tout durcissement reste **additif** : harnais CKM-00 (NOMOS) + guardrail W19-00
(Aedifica, flag OFF par défaut) doivent rester verts. Les deux produits restent vivants
à chaque PR.
