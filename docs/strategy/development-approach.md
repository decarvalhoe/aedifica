# Approche & doctrine de développement — NOMOS × Aedifica

> **Vantage : Aedifica** (produit, 1ᵉʳ vertical). Doc compagnon côté moteur :
> `RBOKproject/NOMOS` → `docs/43-development-doctrine.md`.
> Document **formel de référence** — s'applique à toute contribution. Statut : doctrine.
> Date : 2026-06-10.

## 1. Les deux produits & leur relation

- **NOMOS** — moteur de **savoir canonique certifié** (réglementaire **+ métier**) :
  ingestion *read-only* de sources d'autorité → atomes à spans + hash → TOC certifiée →
  matrice de traçabilité → feed RAG sourcé → *fidelity gate* → evidence. Domain-agnostic,
  spécialisé par **packs minces**.
- **Aedifica** — assistant de **conduite de projet** pour l'architecte suisse, sur tout
  le cycle SIA. **Premier vertical** qui consomme NOMOS via un **bundle contract
  versionné**, **derrière feature flag**, l'**OFS-direct restant le défaut sûr**.
- **Couture** : Aedifica dépend de l'**artefact** (bundle), jamais du code NOMOS. Les
  deux produits avancent à leur rythme, sans se bloquer.

## 2. Principes non négociables

1. **Deux produits vivants, zéro régression.** Tout est **additif / rétro-compatible** ;
   flags + defaults sûrs ; les harnais de non-régression (NOMOS CKM-00, Aedifica
   guardrail W19-00, flag OFF par défaut) restent verts à chaque PR.
2. **Claim-boundary.** On n'affirme que ce qu'on prouve ; toute revendication non prouvée
   est **downgradée**, jamais maquillée. (cf. `hardening-discipline.md`.)
3. **Pas de *done* sans preuve adversariale.** Un test qui passe ne prouve rien ; un test
   qui **échoue sans le fix** prouve. Le tamis : bug → *revert-and-confirm* ; crypto →
   *tamper-fail* ; mécanique → **consommée par le moteur + test moteur** ; résultat de
   pipeline → **calculé**, jamais déclaré ; connecteur → **fetch réel + hash réel**.
4. **L'IA propose, le spécialiste décide.** Sourcé ou inconnu ; jamais de donnée
   fabriquée ; **l'abstention est une réponse légitime**.
5. **Mécaniques au cœur, spécificités au pack.** Faceting, lens, canon promu,
   attestation, gate = NOMOS-core ; un pack domaine ne fournit que vocabulaires +
   connecteurs. Réglementaire **et** métier dans **une même** architecture certifiée.
6. **Capitaliser honnêtement.** Standards ouverts → adopter ; OSS permissif → intégrer ;
   AGPL → **isoler** (frontière process/API) ; commercial → s'inspirer du concept, jamais
   code/contenu/IP ; payant (SIA/ISO) → **jamais de texte intégral**. Les concurrents sont
   un **tremplin**, pas un frein.

## 3. Modèle de savoir (vocabulaire commun aux deux dev)

- **Facettes** (axes contrôlés) : `nature` {regulatory · metier · project} · `discipline`
  /rôle · `activity` · `scope_level` · `trust_tier` {certified · indicative · unverified}
  · `provenance` {official · user_promoted} · `confidentiality` · `applicability`.
- **Lens** : prédicat inclusion/exclusion sur facettes → **scope le retrieval**
  (anti-parasite), au niveau base, défaut = *no lens* = comportement actuel.
- **Canon promu** : tout utilisateur autorisé élève une source au canon **sous droits +
  validation** ; `user_promoted` ≠ `official` ; le confidentiel reste **en silo projet**.
- **Trust honnête** : toute citation porte son **tier** ; un savoir promu ou métier
  n'usurpe jamais le `certified` officiel.

## 4. Process

- **Branche de feature + PR + CI + gate de non-régression.** **Branch-protection
  respectée** : revue requise, **pas d'override admin**.
- Toute issue revendiquant une **capacité** passe la **barre d'acceptation** de
  `hardening-discipline.md`.
- **LPD** : confidentiel en silo projet ; transcription/traitement **local** ; cloud LLM
  exclut le confidentiel ; pas d'audio/transcript brut commité.

## 5. Références (côté Aedifica, `docs/strategy/`)

`nomos-pivot-masterplan.md` · `nomos-knowledge-mesh-and-built-environment.md` ·
`nomos-state-of-the-art-positioning.md` · `nomos-capitalization-and-improvement-plan.md`
· `nomos-implementation-audit.md` · `hardening-discipline.md`.
Côté NOMOS : `docs/39-42` (mêmes analyses) + `docs/43-development-doctrine.md` (ce doc) +
`public-claim-boundary.md`, `08-governance-and-change.md`. Epics : NOMOS #481 (pivot),
#518 (durcissement) ; Aedifica #278 (W19).
