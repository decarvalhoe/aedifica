"""Token auth + capability model (local-first, non-production).

A user authenticates with a bearer token; capabilities are derived from the role.
This is the vNext-style capability pattern: mutations require an explicit
capability, and a report/read capability never grants adapter execution.
"""
from __future__ import annotations

import hashlib
import secrets

# pbkdf2-hmac-sha256 password hashing (stdlib-only; no external deps).
_PBKDF2_ALGO = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 240_000

ROLE_CAPABILITIES = {
    "owner": {"project.read", "project.write", "commune.write", "adapter.execute", "org.manage"},
    "member": {"project.read", "project.write", "commune.write"},
    "viewer": {"project.read"},
    # W10: an external user (client / mandataire / entreprise) invited as a scoped guest.
    # They get NO global read; their access is gated per request to their linked intervenant.
    "external": {"project.external"},
}

ROLES = ("owner", "member", "viewer", "external")


def new_token() -> str:
    return secrets.token_urlsafe(24)


def hash_password(password: str) -> str:
    """Return a self-describing ``algo$iterations$salt$hash`` string."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_ALGO}${_PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    """Constant-time verify a password against a stored hash. False if no hash."""
    if not stored:
        return False
    try:
        algo, iterations, salt_hex, hash_hex = stored.split("$")
        if algo != _PBKDF2_ALGO:
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(dk.hex(), hash_hex)


def capabilities_for(role: str) -> set:
    return ROLE_CAPABILITIES.get(role, set())


def has_capability(role: str, capability: str) -> bool:
    return capability in capabilities_for(role)
