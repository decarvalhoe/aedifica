# Wave 12 — Foresight : la couche IA prédictive et suggestive

> **Doctrine non négociable**
> - L'IA **propose**, l'architecte **décide**. Aucune mutation appliquée sans approbation.
> - **Sourcé ou inconnu, jamais inventé.** Une prédiction sans data suffisante dit "données insuffisantes" — elle ne fabrique pas de chiffre.
> - **Opérationnel = pur soft.** Les surfaces opérationnelles fonctionnent SANS IA. La couche Foresight est *additionnelle*, jamais un préalable.
> - **LPD : local d'abord.** Toute donnée confidentielle reste sur la machine de l'atelier ; les modèles cloud sont opt-in explicite et n'ingèrent jamais les pièces marquées confidentielles.
> - **Tout est tracé.** Chaque proposition IA est un objet horodaté, signé, basé sur des sources nommées, et passe par le ledger d'approbation comme une opération adaptateur.

## Objectif

Donner à l'architecte et à son équipe **un copilote de conduite de projet** qui :
1. **Prédit** ce qui prend du temps et coûte de l'argent (heures, CHF, échéances)
2. **Repère** ce qui dérape avant que ça casse (erreurs, omissions, charges, dépendances)
3. **Suggère** des actions concrètes (réutilisation de jurisprudence-atelier, complétion de checklist, équilibrage de charge)
4. **Assiste** la coordination (qui doit quoi, quand, en fonction de quelle dépendance)

Tout en restant **un assistant**. L'architecte garde la main, le ledger garde la trace, et le modèle apprend de la jurisprudence de **cet atelier** (pas d'un benchmark générique).

---

## Architecture en six tranches

### W12.A — Moteur de signaux dérivés *(déterministe, base de tout le reste)*

Le moteur Foresight est d'abord **déterministe et explicable**. Aucun modèle stochastique. On exploite la data existante : ledger, tasks, attachments, BRS, captures, intervenants, costs, regulatory.

**Module `aedifica/foresight/`** — stdlib + SQLAlchemy, zéro dépendance externe :
- `duration.py` — prédiction d'heures par tâche
  - **Méthode** : régression linéaire sur les tâches *similaires* (même phase SIA + même catégorie + même atelier) avec `actual_hours` vs `estimate_hours`. Si l'écart historique est >1.3× : prédire `actual = estimate × ratio_atelier`. Sinon, faire confiance à l'estimate.
  - **Source** : tâches `status="done"` de l'atelier dont le `estimate_hours` est non-null et dont le ledger `task_done` a un `actual_hours` calculable.
  - **Confidence** : `count_comparables / 20`, capé à 1.0.
- `cost.py` — extension SIA 102 avec facteurs atelier
  - **Méthode** : SIA 102 reste l'ancre (déjà implémenté). On ajoute un *coefficient de complexité atelier* dérivé du delta historique entre estimé-SIA et réel-facturé sur les projets terminés.
  - **Source** : projets `status="archived"` avec un `cost_final` renseigné vs `cost_estimate_sia102`.
  - **Confidence** : `count_archived_projects / 5`.
- `risk.py` — détection d'anomalies cross-surface
  - **Règles déterministes** :
    1. *BRS-after-permit* — un BRS de type `requirement_change` créé après `permit_submitted` → risque opposition + recoût
    2. *Cascade overdue* — si une tâche P0 dépasse l'échéance ET a des dépendances aval : alerter chaque dépendance
    3. *Surcharge collaborateur* — heures sommées sur 7 jours > 50h pour un collaborateur → risque qualité
    4. *Permis sans pièces critiques* — `status="ready_for_review"` mais une pièce `required=true` du dossier-type Vaud manque → blocage probable
    5. *Cost-by-phase drift* — heures réelles d'une phase > 1.3× plan SIA → alerte rentabilité
    6. *Friction récurrente* — ≥ 3 captures `friction` du même `source_ref` ou même mot-clé en 30 jours → pattern à traiter
    7. *Règlement à l'étude impactant* — un capture `regulation` chevauche une phase ≤ 33 du projet → alerter
- `comparables.py` — retrieval atelier
  - Pour un projet courant, retrouver les projets terminés *les plus similaires* (commune, type de mandat, surface brute, phase) — top 3 avec score de similarité explicite.
  - Sert d'input à `duration.py` et `cost.py`, et de surface "Projets comparables" dans le Dashboard.
- `suggest.py` — synthétiseur de propositions
  - Combine les sorties des modules précédents en `Proposal` objects (cf. modèle ci-dessous).

**Modèle `Proposal`** *(nouveau, jamais inventé — toujours basé sur des sources nommées)* :
```python
class Proposal(Base):
    __tablename__ = "proposal"
    id: int
    project_id: int
    kind: str          # duration_adjust | cost_factor | risk_alert | reuse_brs | reuse_checklist | rebalance | next_step_ranked
    title: str         # "Re-estimer 7 tâches phase 33 à +30%"
    detail: str        # markdown
    basis: list[dict]  # [{"source_kind": "task", "source_id": 142, "ref": "Tâche A → 18h estimées, 24h réelles"}, ...]
    confidence: float  # 0..1
    proposed_at: datetime
    decided_at: datetime | None
    decided_by: str | None
    decision: str | None  # accepted | deferred | refused
    decision_basis: str | None
    apply_payload: dict | None  # what to write if accepted (PATCH paths + values)
```

**Endpoint `GET /api/projects/{pid}/foresight`** retourne :
```json
{
  "proposals": [...],
  "summary": {
    "predictions": 12,
    "risks": 4,
    "suggestions": 7,
    "confidence_avg": 0.62
  },
  "basis_data_freshness": "2026-06-06T18:30:00Z"
}
```

**Endpoint `POST /api/projects/{pid}/foresight/{proposal_id}/decide`** body `{decision: accept|defer|refuse, basis: "..."}` :
- `accept` → applique `apply_payload` (PATCH la ressource ciblée) + log `foresight_accepted` au ledger + audit log
- `defer` → laisse la proposition visible mais marquée différée
- `refuse` → archive avec basis

---

### W12.B — Surface "Foresight" dans le workspace

Une surface dédiée + des **inlays** dans les surfaces opérationnelles existantes (sans les polluer).

**Nouvelle surface `/workspace?view=foresight`** :
- Header : `ic-datum-target` (Foresight = ce qu'on vise) + h2 "Foresight · prédictions et suggestions"
- 3 panneaux Datum :
  1. **Prédictions** (durée, coût, échéances) — chaque ligne : titre, basis cliquable, confidence en pastille, boutons accept/defer/refuse
  2. **Risques** — chaque alerte avec sévérité (`is-conflict`, `is-assume`, `is-computed`) + référence au signal source
  3. **Suggestions** — réutilisation de BRS/checklist de projets comparables, rééquilibrage de charge

**Inlays** dans les surfaces existantes (subtils, non bloquants) :
- *Tâches & priorités* → quand on saisit `estimate_hours`, afficher en mono `« comparable atelier : 24h ± 4h »` sous l'input
- *Coûts & honoraires* → ajouter un panneau "Coefficient atelier" sous l'estimateur SIA, avec basis (projets archivés utilisés)
- *Dashboard alertes Atelier* (déjà câblé W11.C) → ajouter les risques W12.A.risk au flux existant
- *Permis* → quand `ready_for_review=false`, indiquer les pièces manquantes critiques (déjà fait) + une `proposal` Foresight si une réutilisation est disponible
- *Prochain pas* (déjà existe) → ranking par impact aval (combien de tâches débloque ce pas)

---

### W12.C — LLM opt-in pour les surfaces text-heavy

Là où la résumée / l'extraction sémantique apporte vraiment de la valeur :
- **BRS** : résumer un long fil d'échanges client en 3 points actionnables (avec lien vers chaque source)
- **Mémoire / captures friction** : clusteriser les frictions récurrentes pour faire émerger des patterns
- **Documents** : extraire les exigences réglementaires d'un règlement communal et les pousser comme propositions de claims `regulatory`

**Doctrine LLM** :
- **Local d'abord** : intégration Ollama (llama3.1 8B ou qwen2.5 7B selon disponibilité). Aucun appel cloud sans opt-in par projet.
- **Opt-in cloud par projet** : un switch dans les paramètres du projet, désactivé par défaut. Quand activé : tout contenu marqué `confidential=true` est exclu de l'envoi.
- **Sortie = `Proposal`** : le LLM ne mute jamais directement. Il produit des propositions qui passent par le même workflow d'approbation.
- **Audit log** : chaque appel LLM (local ou cloud, modèle, taille prompt, projet) est tracé.

---

### W12.D — Conduite de projet : `next_step` intelligent

L'endpoint `/next-step` existe déjà. Il devient :
- **Ranking par impact** : score = nombre de tâches/étapes débloquées en aval + criticité de phase
- **Détection de chemin critique** : sur le DAG des `task_dependency` + checklist, identifier la chaîne la plus longue depuis le présent jusqu'au prochain jalon (dépôt permis, remise, livraison)
- **Prochains 3 pas** : non plus une liste plate mais une recommandation argumentée *"Si vous attaquez X avant Y, vous gagnez Z jours"*

---

### W12.E — Apprentissage continu de l'atelier

Après quelques projets clos, on capitalise. Chaque clôture de projet déclenche :
- Recalcul du `ratio_atelier` (heures réelles / heures estimées par phase et catégorie)
- Mise à jour du `coefficient_complexité_atelier` (coût réel / SIA 102)
- Archivage des comparables (pour `comparables.py`)
- Persistence dans une table `AtelierBenchmark` versionnée par snapshot trimestriel — permet le rollback si une saison fausse la moyenne

---

### W12.F — Garde-fous et explicabilité

Sans cette tranche, rien n'est crédible :
- Chaque `Proposal` a un panneau "Pourquoi ?" qui liste **toutes** les sources : tâches comparables (avec liens), projets archivés, règles déclenchées, signal de drift.
- Bouton "Refaire le calcul" qui re-snapshote les inputs et regénère la proposition (utile si on rajoute de la data en cours de route).
- `GET /api/projects/{pid}/foresight/explain/{proposal_id}` → dump complet en JSON pour audit indépendant.
- Tests adversariaux : on construit des cas-limites (data très clairsemée, projets très atypiques) et on vérifie que le moteur dit "données insuffisantes" plutôt que de produire un chiffre.

---

## Pipeline d'exécution

Même discipline que Wave 11 :
1. Implémentation tranche par tranche
2. Tests unitaires + intégration par tranche
3. Build clean + audit visuel par tranche
4. PR par tranche
5. CI 5/5 vert obligatoire
6. Merge + deploy Fly + re-audit prod
7. Pas de tranche suivante tant que la précédente n'est pas en prod

## Échiquier — exécuté vs à venir

- [x] **W12 plan rédigé** *(ce document)*
- [ ] **W12.A** — Moteur déterministe : `aedifica/foresight/`, modèle `Proposal`, migration, endpoints, tests
- [ ] **W12.B** — Surface workspace + inlays dans Tâches/Coûts/Dashboard/Permis/Prochain pas
- [ ] **W12.D** — `next_step` v2 avec ranking d'impact (commande avant W12.C parce que déterministe)
- [ ] **W12.C** — LLM opt-in (Ollama local + switch cloud par projet)
- [ ] **W12.E** — Apprentissage continu + table `AtelierBenchmark` snapshot trimestriel
- [ ] **W12.F** — Garde-fous d'explicabilité + tests adversariaux + endpoint `/explain`
