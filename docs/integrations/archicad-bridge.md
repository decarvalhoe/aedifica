# Archicad JSON-bridge — branchement de la maquette

> **Statut** : Aedifica sait interroger un endpoint compatible pour lire les
> informations produit et la sélection. Ce chemin est vérifié contre le serveur
> replay, mais attend encore la preuve sur un siège réel (#105 / #115). La mutation
> Archicad décrite plus bas est un contrat cible, pas une capacité livrée.

## Pourquoi un bridge

Aedifica ne doit pas embarquer Archicad dans son serveur. Le connecteur actuel envoie
des commandes de lecture officielles à un endpoint local compatible :
`API.GetProductInfo`, `API.GetSelectedElements`, `API.GetTypesOfElements`, les
commandes de lecture des classifications, puis les commandes de résolution et de
lecture des propriétés. Il normalise la réponse, audite les métadonnées et prépare
un diff sans écrire dans la maquette.

Cela permet :
- **Confidentialité** : la maquette ne quitte jamais le poste/serveur de l'atelier
- **Versionnage Archicad** : un bridge par version d'Archicad, indépendant du backend Aedifica
- **Réversibilité cible** : une future mutation devra produire un `undo`; ce chemin
  n'est pas encore implémenté

## Contrat de lecture actuel

Le connecteur poste des commandes JSON sur l'endpoint configuré :

```json
POST /
Content-Type: application/json

{
  "command": "API.GetProductInfo"
}
```

Puis :

```json
{
  "command": "API.GetSelectedElements",
  "parameters": {}
}
```

`GetSelectedElements` ne renvoie que des GUID. Aedifica appelle ensuite
`API.GetTypesOfElements`, `API.GetAllClassificationSystems`,
`API.GetClassificationsOfElements`, `API.GetDetailsOfClassificationItems`,
`API.GetAllPropertyNames`, `API.GetPropertyIds` et
`API.GetPropertyValuesOfElements` pour enrichir la sélection. Les propriétés
utilisateur sont résolues par leur paire complète `[groupe, nom]`; un nom absent ou
ambigu bloque le mode live au lieu de produire un faux `before=null`. Le contrat
replay représentatif vit dans `pilot/model/archicad_json_api_fixture.json`.
`pilot/archicad_harness.py --endpoint ... --no-fallback --json` constitue le client
de référence pour le pilote read-only.

## Contrat cible de mutation

Une future implémentation devra recevoir une transaction approuvée, appliquer une
opération réversible et retourner une preuve telle que :

```json
{
  "mode": "live",
  "executed": true,
  "ledger_id": "ARC-2026-06-06T18:24:17Z-O1",
  "rollback_handle": "RB-2026-06-06T18:24:17Z-O1"
}
```

La durée de conservation du `rollback_handle`, le protocole d'approbation et le
transport restent à spécifier et tester avant toute mutation partenaire.

## Modes & sécurité

| Mode | Comportement |
|---|---|
| `live` | Connexion réelle en lecture seule : produit, sélection, audit et diff. |
| `dry-run` | Transaction préparée localement ; aucune écriture externe. |
| `fixture_fallback` | Si le bridge est injoignable, Aedifica retombe sur un modèle de fixture (compréhension du flux uniquement). |
| Mutation | Non implémentée ; exige un futur contrat approuvé et réversible. |

Un futur bridge de mutation devra :
- N'accepter que les connexions depuis `127.0.0.1` (ou le réseau atelier si vous configurez explicitement)
- Logger chaque mutation avec timestamp + op_id + ledger_id
- Refuser une opération sans `op_id` ou sans `undo`
- Refuser une opération `live` sans header `X-Aedifica-Approval` (jeton émis par Aedifica après validation architecte)

## Côté Aedifica

Renseignez l'URL du bridge dans le panneau Copilote du workspace :
- URL vide → mode `fixture_fallback` (utile pour comprendre le flux d'approbation sans bridge)
- URL renseignée + bridge joignable → inspection `live` en lecture seule
- URL renseignée + bridge injoignable → bascule automatique sur `fixture_fallback` avec banner explicite

L'URL est résolue par le backend FastAPI. Le backend hébergé sur Fly ne peut pas
atteindre `localhost` sur le poste de l'architecte. Pour un endpoint local, utilisez
le harness ou une API Aedifica locale ; n'exposez pas Archicad sur Internet.

## Distribution

- **Aujourd'hui** : harness read-only et serveur replay dans le dépôt.
- **Étape partenaire** : valider les réponses contre une version Archicad réelle.
- **Après validation** : décider du packaging et d'un éventuel chemin de mutation.

## Pour un développeur tiers

Si vous voulez écrire votre propre bridge :
1. Le contrat ci-dessus est stable
2. Le serveur `pilot/replay_server.py` permet de tester le connecteur sans siège.
3. La démo hébergée permet d'explorer le flux replay, pas de joindre un bridge local.

Les intentions `set_property`, `rename` et `set_category` peuvent être préparées en
dry-run. Elles ne sont pas envoyées à Archicad par l'implémentation actuelle.
