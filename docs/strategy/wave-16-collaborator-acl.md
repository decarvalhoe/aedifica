# Wave 16 — Gestion d'accès fine pour collaborateurs internes

## Pourquoi

Les externes (W10/W11) ont déjà leur vue scopée par `AccessGrant` sur les documents + l'`ExternalView` qui ne montre que ce qui les concerne. Les collaborateurs internes (rôle `member` ou `viewer`) ont actuellement un accès uniforme : tout ou rien sur tout l'atelier.

Le user veut :
- Un collaborateur peut accéder à la vue projet
- Peut changer certaines choses
- A des éléments en lecture seule
- N'a pas accès du tout à certaines parties (surfaces ou documentations)

## Doctrine

- **Granularité (user × project × surface)** : le triplet qui suffit. Pas besoin d'une matrice complexe par champ.
- **Niveaux** : `none`, `read`, `write`. Trois est assez. (`write` implique `read`.)
- **Résolution par spécificité** :
  1. Exact `(user, project, surface)` → ce niveau
  2. `(user, project, NULL)` → projet-wide
  3. `(user, NULL, surface)` → surface-wide
  4. `(user, NULL, NULL)` → user default
  5. Rôle par défaut (owner=write, member=write, viewer=read)
- **Owner échappe** : un owner garde toujours `write`. Les overrides ne s'appliquent qu'aux non-owners.
- **Owner-only management** : seuls les owners peuvent assigner les scopes.
- **Audit** : toute écriture de scope est tracée.

## Modèle

```python
class CollaboratorScope(Base):
    __tablename__ = "collaborator_scope"
    id: int (pk)
    org_id: int (fk)
    user_id: int (fk)              # le collaborateur impacté
    project_id: int | None (fk)    # null = tous les projets de l'org
    surface: str | None (≤ 30)     # null = toutes les surfaces
    level: str (none|read|write)
    created_at: datetime
    created_by_user_id: int (fk)
```

Index unique sur `(user_id, project_id, surface)` pour éviter les doublons : l'écriture par l'owner est un upsert.

## Surfaces concernées

```
dashboard, foresight, taches, checklist, terrain, copilote, memoire,
coordination, intervenants, documents, brs,
permis, opposition, conformite,
couts, chantier
```

(`atelier`, `equipe`, `settings` restent gérés par rôle global pour éviter les blocages d'administration.)

## Tranches

- [x] **W16.A** — Modèle + migration + helpers `resolve_access(user, project, surface)` + endpoints owner-only de management
- [x] **W16.B** — Enforcement sur les routes : `require_access(user, project, surface, level)` injecté
- [x] **W16.C** — Frontend : `useAccess(view)` hook ; NAV cache les vues `none` ; bandeau « Lecture seule » + désactivation des boutons d'écriture
- [x] **W16.D** — Settings : nouveau panneau « Permissions collaborateurs » avec sélection user → projet → matrice surfaces

## Garde-fous

- Empêcher un owner de se mettre lui-même en `none` (UI bloque, backend ignore le scope si user est owner).
- Une vue marquée `none` est cachée du nav ET le hit direct sur l'URL renvoie un empty-state ("Vous n'avez pas accès à cette surface").
- Les externes restent intouchés — la résolution s'applique seulement à role ∈ {member, viewer}.
