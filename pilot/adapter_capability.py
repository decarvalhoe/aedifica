"""Adapter capability manifests — comparable capability declarations per software.

Loads per-adapter manifests (read/write/export/dry-run/transaction/verification),
validates them against the capability schema, and answers capability questions so
the demo can report unavailable capabilities clearly instead of failing.
"""
from __future__ import annotations

import glob
import json
import os

import jsonschema_mini

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS_DIR = os.path.join(HERE, "adapters")
SCHEMA_PATH = os.path.join(HERE, "schemas", "adapter-capability.schema.json")
BOOLEAN_KINDS = {"dry_run", "transaction", "verification"}
LIST_KINDS = {"read", "write", "export"}


class AdapterCapabilityError(ValueError):
    pass


def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_manifest_paths() -> list:
    return sorted(glob.glob(os.path.join(ADAPTERS_DIR, "*.manifest.json")))


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def all_manifests() -> list:
    return [_load(path) for path in list_manifest_paths()]


def load_manifest(adapter_id: str) -> dict:
    for manifest in all_manifests():
        if manifest.get("adapter_id") == adapter_id:
            return manifest
    raise AdapterCapabilityError(f"unknown adapter: {adapter_id}")


def validate_manifest(manifest: dict, schema: dict | None = None) -> list:
    return jsonschema_mini.validate(manifest, schema or load_schema())


def supports(manifest: dict, kind: str, capability: str | None = None) -> bool:
    caps = manifest.get("capabilities", {})
    if kind in BOOLEAN_KINDS:
        return bool(caps.get(kind))
    return capability in caps.get(kind, [])


def missing_capabilities(manifest: dict, required: dict) -> list:
    """Return the required capabilities the adapter does not support."""
    caps = manifest.get("capabilities", {})
    missing = []
    for kind, value in required.items():
        if kind in BOOLEAN_KINDS:
            if value and not caps.get(kind):
                missing.append(kind)
        elif kind in LIST_KINDS:
            for capability in value:
                if capability not in caps.get(kind, []):
                    missing.append(f"{kind}:{capability}")
        else:
            missing.append(f"unknown_kind:{kind}")
    return missing


def require_capabilities(manifest: dict, required: dict) -> dict:
    missing = missing_capabilities(manifest, required)
    if missing:
        raise AdapterCapabilityError(
            f"adapter {manifest.get('adapter_id')} missing capabilities: {missing}"
        )
    return manifest
