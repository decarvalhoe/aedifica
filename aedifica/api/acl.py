"""W16 — fine-grained ACL resolver for internal collaborators.

Doctrine:
- Externals (role=external) are unaffected; they keep their scoped view.
- Owners (role=owner) are ALWAYS full-write; overrides for them are ignored.
- Members and viewers fall back to their role default unless a CollaboratorScope
  row tightens (or in rare cases loosens) access for a specific (project, surface)
  triple.

Resolution by specificity:
  1. exact  (user, project, surface)
  2. project-wide  (user, project, NULL)
  3. surface-wide  (user, NULL, surface)
  4. user-default  (user, NULL, NULL)
  5. role-default
"""
from __future__ import annotations

from ..db import models as m


# Role-default access levels for the non-scoped path. Owners override before
# we reach this table.
ROLE_DEFAULT: dict[str, str] = {
    "owner": "write",
    "member": "write",
    "viewer": "read",
    "external": "none",  # safety net; externals never hit this resolver
}

LEVEL_RANK = {"none": 0, "read": 1, "write": 2}


def _row_for(session, user_id: int, project_id: int | None, surface: str | None):
    return (session.query(m.CollaboratorScope)
            .filter_by(user_id=user_id, project_id=project_id, surface=surface).first())


def resolve_access(session, user: m.User, project: m.Project | None, surface: str | None) -> str:
    """Return the effective level (`none|read|write`) for the (user, project,
    surface) triple. None for `surface` means "the access level applied to
    the whole project chrome (nav membership)".
    """
    if user.role == "owner":
        return "write"
    if user.role == "external":
        return "none"

    pid = project.id if project is not None else None
    # Walk most-specific to least-specific. Stop at first hit.
    for q in (
        _row_for(session, user.id, pid, surface) if pid and surface else None,
        _row_for(session, user.id, pid, None) if pid else None,
        _row_for(session, user.id, None, surface) if surface else None,
        _row_for(session, user.id, None, None),
    ):
        if q is not None:
            return q.level

    return ROLE_DEFAULT.get(user.role or "", "none")


def has_level(actual: str, needed: str) -> bool:
    return LEVEL_RANK.get(actual, 0) >= LEVEL_RANK.get(needed, 0)


def user_access_map(session, user: m.User) -> dict:
    """Return a compact map for the frontend: per-project per-surface levels +
    a default. Used by the workspace shell to hide/disable surfaces without
    making one API call per surface."""
    if user.role == "owner":
        return {"role": "owner", "default": "write", "projects": {}}
    if user.role == "external":
        return {"role": "external", "default": "none", "projects": {}}

    org_projects = session.query(m.Project).filter_by(org_id=user.org_id).all()
    rows = session.query(m.CollaboratorScope).filter_by(user_id=user.id).all()
    # Pre-index by triple.
    by_triple: dict[tuple[int | None, str | None], str] = {}
    for r in rows:
        by_triple[(r.project_id, r.surface)] = r.level

    role_default = ROLE_DEFAULT.get(user.role or "", "none")
    user_default = by_triple.get((None, None), role_default)
    out_projects: dict[str, dict] = {}

    for p in org_projects:
        proj_default = by_triple.get((p.id, None), user_default)
        surfaces: dict[str, str] = {}
        for s in m.SCOPED_SURFACES:
            # exact → surface-wide (NULL project) → project default
            lvl = (by_triple.get((p.id, s))
                   or by_triple.get((None, s))
                   or proj_default)
            surfaces[s] = lvl
        out_projects[p.project_id] = {"default": proj_default, "surfaces": surfaces}

    return {
        "role": user.role,
        "default": user_default,
        "projects": out_projects,
    }
