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
