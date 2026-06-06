# Archicad JSON-bridge — branchement de la maquette

> **Statut** : le bridge n'est pas encore distribué publiquement. Cette page décrit le contrat HTTP qu'Aedifica attend afin qu'un atelier puisse écrire son propre bridge ou utiliser celui qu'on fournira en bêta privée.

## Pourquoi un bridge

Aedifica ne parle pas directement à Archicad : ce serait un couplage fort à une version du logiciel et une dépendance lourde côté serveur. Le bridge inverse la chaîne : Aedifica envoie une **opération JSON** au bridge (qui tourne sur la machine ou le serveur de l'atelier qui héberge Archicad), le bridge l'applique via l'API Archicad officielle (Archicad 26+ supporte le format JSON), et retourne le résultat — en `dry-run` (aperçu, lecture seule) ou en `live` (mutation appliquée).

Cela permet :
- **Confidentialité** : la maquette ne quitte jamais le poste/serveur de l'atelier
- **Versionnage Archicad** : un bridge par version d'Archicad, indépendant du backend Aedifica
- **Réversibilité** : le bridge enregistre un `undo` pour chaque mutation, qu'Aedifica peut déclencher via une opération inverse

## Contrat HTTP

Le bridge expose un seul endpoint HTTP local (par défaut `http://localhost:19723/aedifica`). Aedifica POST une transaction :

```json
POST /aedifica
Content-Type: application/json

{
  "adapter_id": "archicad_json",
  "operations": [
    {
      "op_id": "O1",
      "kind": "set_property",
      "target": "AC-SPACE-101",
      "property": "Classification",
      "after": "bureau",
      "undo": "restore"
    }
  ],
  "mode": "dry-run"
}
```

Le bridge répond :

```json
{
  "mode": "dry-run",
  "preview": {
    "product": { "name": "Archicad", "version": "26" },
    "operations": [
      {
        "op_id": "O1",
        "would_change": {
          "target": "AC-SPACE-101",
          "before": "espace générique",
          "after": "bureau"
        }
      }
    ]
  }
}
```

En `live`, après approbation de l'architecte, Aedifica POSTe la même transaction avec `mode: "live"`. Le bridge applique et retourne :

```json
{
  "mode": "live",
  "executed": true,
  "ledger_id": "ARC-2026-06-06T18:24:17Z-O1",
  "rollback_handle": "RB-2026-06-06T18:24:17Z-O1"
}
```

Le `rollback_handle` est conservé par le bridge pendant 30 jours et permet d'annuler la mutation via `POST /aedifica/rollback {"handle": "..."}`.

## Modes & sécurité

| Mode | Comportement |
|---|---|
| `dry-run` | Lecture seule. Le bridge calcule le diff mais ne touche pas à la maquette. |
| `live` | Mutation. Demande une approbation de l'architecte côté Aedifica avant l'appel. |
| `fixture_fallback` | Si le bridge est injoignable, Aedifica retombe sur un modèle de fixture (compréhension du flux uniquement). |

Le bridge doit :
- N'accepter que les connexions depuis `127.0.0.1` (ou le réseau atelier si vous configurez explicitement)
- Logger chaque mutation avec timestamp + op_id + ledger_id
- Refuser une opération sans `op_id` ou sans `undo`
- Refuser une opération `live` sans header `X-Aedifica-Approval` (jeton émis par Aedifica après validation architecte)

## Côté Aedifica

Renseignez l'URL du bridge dans le panneau Copilote du workspace :
- URL vide → mode `fixture_fallback` (utile pour comprendre le flux d'approbation sans bridge)
- URL renseignée + bridge joignable → mode `live`/`dry-run`
- URL renseignée + bridge injoignable → bascule automatique sur `fixture_fallback` avec banner explicite

## Distribution

- **Aujourd'hui** : bêta privée sur demande à devlab@realisons.com
- **Court terme** : add-on Archicad packagé (XML installer + add-on .apx)
- **Moyen terme** : add-on signé distribué via le marketplace Graphisoft

## Pour un développeur tiers

Si vous voulez écrire votre propre bridge :
1. Le contrat ci-dessus est stable
2. Un test-suite minimal est livré dans `tests/integration/test_archicad_bridge.py` (mock côté Aedifica)
3. Vous pouvez le tester dès aujourd'hui contre `aedifica-demo.fly.dev` en mode `fixture_fallback`

Toutes les opérations supportées aujourd'hui : `set_property`, `rename`, `set_category`. La liste s'étend au fur et à mesure que les surfaces opérationnelles d'Aedifica les demandent.
