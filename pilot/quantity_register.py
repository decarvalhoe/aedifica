"""Quantity source register and versioning.

Registers quantity sources (manual input, model snapshot, IFC/Speckle, office
export) with a version, capture date, unit system and confidence. A source can be
superseded without deleting history, tender assumptions can link to a specific
quantity source version, and the validator rejects unitless quantities.
"""
from __future__ import annotations

ORIGINS = {"manual", "model_snapshot", "ifc", "speckle", "office_export"}


def validate_source(source: dict) -> list:
    errors = []
    source_id = source.get("source_id") or "<missing>"
    for key in ("source_id", "version", "captured_at", "unit_system", "confidence"):
        if not (isinstance(source.get(key), str) and source.get(key).strip()):
            errors.append(f"{source_id}.{key} must be a non-empty string")
    if source.get("origin") not in ORIGINS:
        errors.append(f"{source_id}.origin must be one of {sorted(ORIGINS)}")
    quantities = source.get("quantities")
    if not isinstance(quantities, list) or not quantities:
        errors.append(f"{source_id}.quantities must be a non-empty list")
        quantities = []
    for index, quantity in enumerate(quantities):
        if not isinstance(quantity, dict):
            errors.append(f"{source_id}.quantities[{index}] must be an object")
            continue
        value = quantity.get("quantity")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{source_id}.quantities[{index}].quantity must be a number")
        if not (isinstance(quantity.get("unit"), str) and quantity.get("unit").strip()):
            errors.append(f"{source_id}.quantities[{index}] is unitless; a unit is required")
        if not (isinstance(quantity.get("item"), str) and quantity.get("item").strip()):
            errors.append(f"{source_id}.quantities[{index}].item must be a non-empty string")
    return errors


def validate_register(register: dict) -> list:
    errors = []
    if not isinstance(register.get("sources"), list) or not register["sources"]:
        return ["register.sources must be a non-empty list"]
    for source in register["sources"]:
        errors.extend(validate_source(source))
    return errors


def add_source(register: dict, source: dict) -> dict:
    errors = validate_source(source)
    if errors:
        raise ValueError(f"invalid quantity source: {errors}")
    register.setdefault("sources", []).append(source)
    return register


def supersede_source(register: dict, source_id: str, new_source: dict) -> dict:
    """Mark the active version of source_id superseded and append the new version (history kept)."""
    for source in register.get("sources", []):
        if source.get("source_id") == source_id and not source.get("superseded"):
            source["superseded"] = True
    new_source["superseded"] = False
    return add_source(register, new_source)


def history(register: dict, source_id: str) -> list:
    return [s for s in register.get("sources", []) if s.get("source_id") == source_id]


def active_sources(register: dict) -> list:
    return [s for s in register.get("sources", []) if not s.get("superseded")]


def find_version(register: dict, source_id: str, version: str) -> dict | None:
    for source in register.get("sources", []):
        if source.get("source_id") == source_id and source.get("version") == version:
            return source
    return None


def link_resolves(register: dict, ref: dict) -> bool:
    return find_version(register, (ref or {}).get("source_id"), (ref or {}).get("version")) is not None
