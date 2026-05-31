"""Minimal stdlib JSON Schema (draft-07 subset) validator.

Aedifica stays stdlib-only, but several contracts deserve a real, documented
JSON Schema file. This module validates an instance against the subset of
draft-07 keywords those schemas use and returns a list of human-readable error
strings (empty list == valid). No third-party dependency.

Supported keywords: type, required, properties, additionalProperties (bool),
const, enum, pattern, minLength, maxLength, minimum, maximum, minItems,
maxItems, items, anyOf, oneOf, format ("date", "date-time").
"""
from __future__ import annotations

from datetime import date, datetime
import re


_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _check_format(value: str, fmt: str) -> bool:
    if fmt == "date":
        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    if fmt == "date-time":
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    return True


def validate(instance, schema, path: str = "$") -> list:
    """Return a list of error strings; empty means the instance is valid."""
    errors: list = []
    _validate(instance, schema, path, errors)
    return errors


def is_valid(instance, schema) -> bool:
    return not validate(instance, schema)


def _validate(instance, schema, path, errors) -> None:
    if not isinstance(schema, dict):
        return

    declared_type = schema.get("type")
    if declared_type:
        types = declared_type if isinstance(declared_type, list) else [declared_type]
        if not any(_TYPE_CHECKS.get(t, lambda v: True)(instance) for t in types):
            errors.append(f"{path}: expected type {declared_type}, got {type(instance).__name__}")
            return  # downstream keyword checks would be misleading

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: does not match pattern {schema['pattern']}")
        if "format" in schema and not _check_format(instance, schema["format"]):
            errors.append(f"{path}: invalid {schema['format']} value")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems {schema['maxItems']}")
        items = schema.get("items")
        if isinstance(items, dict):
            for index, element in enumerate(instance):
                _validate(element, items, f"{path}[{index}]", errors)

    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                errors.append(f"{path}: missing required property '{required}'")
        properties = schema.get("properties", {})
        for key, subschema in properties.items():
            if key in instance:
                _validate(instance[key], subschema, f"{path}.{key}", errors)
        if schema.get("additionalProperties") is False:
            extra = set(instance) - set(properties)
            if extra:
                errors.append(f"{path}: unexpected properties {sorted(extra)}")

    if "anyOf" in schema and not any(is_valid(instance, sub) for sub in schema["anyOf"]):
        errors.append(f"{path}: does not match anyOf")
    if "oneOf" in schema:
        matches = sum(1 for sub in schema["oneOf"] if is_valid(instance, sub))
        if matches != 1:
            errors.append(f"{path}: must match exactly one oneOf schema (matched {matches})")
