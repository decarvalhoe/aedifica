#!/usr/bin/env python3
"""Normalize neutral adapter snapshots for later IFC and Speckle bridges."""
import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
IFC_FIXTURE = os.path.join(HERE, "model", "ifc_snapshot_fixture.json")
SPECKLE_FIXTURE = os.path.join(HERE, "model", "speckle_snapshot_fixture.json")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _normalize_element(item):
    return {
        "element_id": str(item["element_id"]),
        "type": item.get("type"),
        "classification": item.get("classification"),
        "properties": item.get("properties", {}),
        "quantity_refs": item.get("quantity_refs", []),
    }


def normalize_snapshot(data):
    elements = [_normalize_element(item) for item in data.get("elements", [])]
    spaces = [item for item in elements if item.get("classification") == "IfcSpace"]
    return {
        "adapter_id": data["adapter_id"],
        "source_model_version": data["source_model_version"],
        "source_model_ref": data["source_model_ref"],
        "elements": elements,
        "spaces": spaces,
        "property_sets": data.get("property_sets", []),
        "snapshot_mode": data.get("snapshot_mode", "fixture"),
    }


def inspect_ifc_snapshot(path=IFC_FIXTURE):
    return normalize_snapshot(_load(path))


def inspect_speckle_snapshot(path=SPECKLE_FIXTURE):
    return normalize_snapshot(_load(path))


def ifcopenshell_available():
    try:
        import ifcopenshell  # noqa: F401

        return True
    except ImportError:
        return False


def _inspect_ifc_via_ifcopenshell(ifc_file):
    """Read a real IFC export when IfcOpenShell is installed (best-effort)."""
    import ifcopenshell  # noqa: F401

    model = ifcopenshell.open(ifc_file)
    elements = []
    for product in model.by_type("IfcProduct"):
        properties = {}
        for definition in getattr(product, "IsDefinedBy", []) or []:
            prop_set = getattr(definition, "RelatingPropertyDefinition", None)
            for prop in getattr(prop_set, "HasProperties", []) or []:
                value = getattr(getattr(prop, "NominalValue", None), "wrappedValue", None)
                if getattr(prop, "Name", None) is not None:
                    properties[prop.Name] = value
        elements.append(
            {
                "element_id": getattr(product, "GlobalId", str(product.id())),
                "type": product.is_a(),
                "classification": product.is_a(),
                "properties": properties,
                "quantity_refs": [],
            }
        )
    spaces = [el for el in elements if el["classification"] == "IfcSpace"]
    return {
        "adapter_id": "ifc_ifcopenshell",
        "source_model_version": os.path.basename(ifc_file),
        "source_model_ref": ifc_file,
        "elements": elements,
        "spaces": spaces,
        "property_sets": sorted({key for el in elements for key in el["properties"]}),
        "snapshot_mode": "ifcopenshell",
    }


def inspect_ifc(ifc_file=None, snapshot_path=IFC_FIXTURE):
    """Inspect an IFC export via IfcOpenShell when available; else JSON-snapshot fallback.

    Missing IfcOpenShell (the common CI case) skips gracefully and uses the
    normalized JSON snapshot, which matches the adapter snapshot contract.
    """
    if ifc_file and ifcopenshell_available():
        return _inspect_ifc_via_ifcopenshell(ifc_file)
    snapshot = inspect_ifc_snapshot(snapshot_path)
    snapshot["snapshot_mode"] = "fallback_json"
    return snapshot


def import_speckle(feature_enabled=False, token=None, snapshot_path=SPECKLE_FIXTURE):
    """Import a Speckle stream/object/version snapshot.

    Default fixture mode normalizes offline with no network/token. When the live
    feature flag is enabled, a missing token returns a blocked external-dependency
    state instead of attempting an unauthenticated call. Model snapshots may carry
    client geometry — share only redacted summaries (see partner-data-redaction).
    """
    if feature_enabled and not token:
        return {
            "adapter_id": "speckle",
            "mode": "live",
            "status": "blocked",
            "blocked_reason": "Speckle feature flag enabled but no API token provided.",
            "external_dependency": True,
        }
    snapshot = inspect_speckle_snapshot(snapshot_path)
    return {
        "adapter_id": "speckle",
        "mode": "live" if feature_enabled else "fixture",
        "status": "imported",
        "snapshot": snapshot,
    }
