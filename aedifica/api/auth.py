"""Token auth + capability model (local-first, non-production).

A user authenticates with a bearer token; capabilities are derived from the role.
This is the vNext-style capability pattern: mutations require an explicit
capability, and a report/read capability never grants adapter execution.
"""
from __future__ import annotations

import secrets

ROLE_CAPABILITIES = {
    "owner": {"project.read", "project.write", "commune.write", "adapter.execute", "org.manage"},
    "member": {"project.read", "project.write", "commune.write"},
    "viewer": {"project.read"},
}

ROLES = ("owner", "member", "viewer")


def new_token() -> str:
    return secrets.token_urlsafe(24)


def capabilities_for(role: str) -> set:
    return ROLE_CAPABILITIES.get(role, set())


def has_capability(role: str, capability: str) -> bool:
    return capability in capabilities_for(role)
