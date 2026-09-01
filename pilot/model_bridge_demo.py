#!/usr/bin/env python3
"""Offline prototype of the local model bridge contract.

It does not connect to Archicad. It proves the first-bridge decision can produce
a dry-run plan from the adapter capability matrix before any mutating command.
"""
import json
import os
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request


HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX_PATH = os.path.join(HERE, "research", "adapter_capability_matrix.json")
SELECTION_FIXTURE = os.path.join(HERE, "model", "archicad_selection_fixture.json")
DESIGN_INTENT_FIXTURE = os.path.join(HERE, "model", "design_intent_fixture.json")
REQUIRED_SPACE_PROPERTIES = ("RoomUsage", "SIA416SurfaceType")


def _load_matrix():
    with open(MATRIX_PATH, encoding="utf-8") as f:
        return json.load(f)


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _endpoint_url(endpoint):
    if endpoint.startswith(("http://", "https://")):
        return endpoint
    return f"http://{endpoint}"


def _post_json(endpoint, payload, timeout=2.0):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        _endpoint_url(endpoint),
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_command(endpoint, command, parameters=None, timeout=2.0):
    payload = {"command": command}
    if parameters is not None:
        payload["parameters"] = parameters
    data = _post_json(endpoint, payload, timeout=timeout)
    if not isinstance(data, dict):
        raise ValueError(f"{command} returned a non-object response")
    if data.get("succeeded") is False:
        raise ValueError(f"{command} failed: {data.get('error') or data}")
    result = data.get("result", data.get("Result", data.get("response", data)))
    if not isinstance(result, dict):
        raise ValueError(f"{command} returned an invalid result")
    return result


def _first_dict(*candidates):
    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate
    return {}


def select_adapter(adapter_id="archicad_json"):
    matrix = _load_matrix()
    for adapter in matrix["adapters"]:
        if adapter["adapter_id"] == adapter_id:
            return adapter
    raise KeyError(adapter_id)


def health_check(adapter_id="archicad_json", endpoint=None, timeout=1.0):
    adapter = select_adapter(adapter_id)
    running = False
    error = None
    product_info = None
    if endpoint:
        try:
            product = live_product_info(endpoint, timeout=timeout)
            running = product["running"]
            product_info = product.get("product_info")
            error = product.get("error")
        except (OSError, urllib.error.URLError) as exc:
            error = str(exc)
    return {
        "adapter_id": adapter_id,
        "running": running,
        "endpoint": endpoint,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "product_info": product_info,
        "read_capabilities": adapter.get("read_capabilities", []),
        "write_capabilities": adapter.get("write_capabilities", []),
        "error": error,
    }


def live_product_info(endpoint, timeout=2.0):
    """Query an Archicad JSON-style endpoint for product info.

    The response parser is intentionally tolerant so the same function can be
    tested against a local fixture server and later against the official bridge.
    """
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        result = _post_command(endpoint, "API.GetProductInfo", timeout=timeout)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        return {
            "adapter_id": "archicad_json",
            "running": False,
            "endpoint": endpoint,
            "checked_at": checked_at,
            "product_info": None,
            "error": str(exc),
        }
    product_info = _first_dict(result.get("productInfo"), result.get("product_info"), result)
    official_response = "version" in result and "buildNumber" in result
    return {
        "adapter_id": "archicad_json",
        "running": bool(product_info),
        "endpoint": endpoint,
        "checked_at": checked_at,
        "product_info": {
            "name": product_info.get("name") or product_info.get("product") or product_info.get("Product") or ("Archicad" if official_response else None),
            "version": product_info.get("version") or product_info.get("Version"),
            "build": product_info.get("build") or product_info.get("buildNumber") or product_info.get("Build"),
            "language": product_info.get("language") or product_info.get("languageCode"),
            "raw": product_info,
        },
        "error": None,
    }


def inspect_selected_elements(snapshot_path=SELECTION_FIXTURE):
    snapshot = _load_json(snapshot_path)
    return {
        "source_model_version": snapshot["model_version"],
        "source_model_ref": snapshot["source_model_ref"],
        "selected_elements": [
            {
                "element_id": item["element_id"],
                "type": item["type"],
                "classification": item["classification"],
                "classifications": [{"id": item["classification"]}],
                "classifications_available": True,
                "properties": item.get("properties", {}),
                "properties_available": True,
                "property_states": {
                    name: {"status": "normal" if value is not None else "userUndefined", "value": value}
                    for name, value in item.get("properties", {}).items()
                },
            }
            for item in snapshot.get("selected_elements", [])
        ],
    }


def _normalize_live_element(item):
    element_id = item.get("element_id") or item.get("elementId") or item.get("id")
    if isinstance(element_id, dict):
        element_id = element_id.get("guid") or element_id.get("id") or element_id.get("value")
    classification = item.get("classification") or item.get("type") or item.get("elementType")
    properties_available = "properties" in item or "propertyValues" in item
    properties = item.get("properties") or item.get("propertyValues") or {}
    return {
        "element_id": str(element_id),
        "type": item.get("type") or item.get("elementType") or classification,
        "classification": item.get("classification") or classification,
        "classifications": item.get("classifications") or [],
        "classifications_available": bool(item.get("classification") or classification),
        "properties": properties if isinstance(properties, dict) else {},
        "properties_available": properties_available,
        "property_states": item.get("property_states") or {},
    }


def _element_guid(item):
    element_id = item.get("elementId") or item.get("element_id") or item.get("id")
    if isinstance(element_id, dict):
        return element_id.get("guid") or element_id.get("id") or element_id.get("value")
    return element_id


def _property_name(item):
    localized = item.get("localizedName")
    if isinstance(localized, list) and localized:
        return localized[-1]
    return item.get("nonLocalizedName") or item.get("name")


def _property_state(item):
    if not isinstance(item, dict):
        return {"status": "missing_response", "value": None}
    if isinstance(item.get("error"), dict):
        return {"status": "error", "value": None, "error": item["error"].get("message")}
    value = item.get("propertyValue")
    if not isinstance(value, dict):
        return {"status": "missing_response", "value": None}
    status = value.get("status") or "missing_status"
    return {"status": status, "value": value.get("value") if status == "normal" else None}


def _guid(value):
    if not isinstance(value, dict):
        return None
    return value.get("guid") or value.get("id") or value.get("value")


def _classification_data(endpoint, elements, timeout):
    systems_result = _post_command(endpoint, "API.GetAllClassificationSystems", timeout=timeout)
    systems = systems_result.get("classificationSystems") or []
    system_refs = [
        {"classificationSystemId": item["classificationSystemId"]}
        for item in systems
        if isinstance(item, dict) and isinstance(item.get("classificationSystemId"), dict)
    ]
    if not system_refs:
        return [{} for _ in elements], {}, "no classification system is available"

    classifications_result = _post_command(
        endpoint,
        "API.GetClassificationsOfElements",
        {"elements": elements, "classificationSystemIds": system_refs},
        timeout=timeout,
    )
    rows = classifications_result.get("elementClassifications") or []
    item_refs = []
    seen_item_ids = set()
    for row in rows:
        for value in row.get("classificationIds", []) if isinstance(row, dict) else []:
            classification_id = value.get("classificationId") if isinstance(value, dict) else None
            item_id = classification_id.get("classificationItemId") if isinstance(classification_id, dict) else None
            guid = _guid(item_id)
            if guid and guid not in seen_item_ids:
                seen_item_ids.add(guid)
                item_refs.append({"classificationItemId": item_id})

    details_by_id = {}
    if item_refs:
        details_result = _post_command(
            endpoint,
            "API.GetDetailsOfClassificationItems",
            {"classificationItemIds": item_refs},
            timeout=timeout,
        )
        for row in details_result.get("classificationItems") or []:
            detail = row.get("classificationItem") if isinstance(row, dict) else None
            item_id = detail.get("classificationItemId") if isinstance(detail, dict) else None
            guid = _guid(item_id)
            if guid:
                details_by_id[guid] = detail

    systems_by_id = {
        _guid(item.get("classificationSystemId")): item
        for item in systems
        if isinstance(item, dict) and _guid(item.get("classificationSystemId"))
    }
    return rows, {"details": details_by_id, "systems": systems_by_id}, None


def live_selected_elements(endpoint, timeout=2.0, required_properties=None):
    required_properties = tuple(
        dict.fromkeys((*REQUIRED_SPACE_PROPERTIES, *(required_properties or ())))
    )
    try:
        result = _post_command(endpoint, "API.GetSelectedElements", {}, timeout=timeout)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        return {
            "source_model_version": None,
            "source_model_ref": endpoint,
            "selected_elements": [],
            "error": str(exc),
        }
    enriched = result.get("selected_elements") or result.get("selectedElements") or result.get("selection")
    if isinstance(enriched, list):
        return {
            "source_model_version": result.get("source_model_version") or result.get("model_version") or result.get("modelVersion"),
            "source_model_ref": result.get("source_model_ref") or result.get("sourceModelRef") or endpoint,
            "selected_elements": [_normalize_live_element(item) for item in enriched if isinstance(item, dict)],
            "unavailable_properties": [],
            "error": None,
        }

    elements = result.get("elements") or []
    if not isinstance(elements, list):
        return {
            "source_model_version": None,
            "source_model_ref": endpoint,
            "selected_elements": [],
            "error": "API.GetSelectedElements returned an invalid element list",
        }
    if not elements:
        return {
            "source_model_version": None,
            "source_model_ref": endpoint,
            "selected_elements": [],
            "error": None,
        }

    try:
        types_result = _post_command(endpoint, "API.GetTypesOfElements", {"elements": elements}, timeout=timeout)
        classification_rows, classification_metadata, classification_error = _classification_data(
            endpoint, elements, timeout
        )
        property_names_result = _post_command(endpoint, "API.GetAllPropertyNames", timeout=timeout)
        available_names = property_names_result.get("properties") or []
        matches = {
            name: [item for item in available_names if _property_name(item) == name]
            for name in required_properties
        }
        unavailable_properties = {
            name: "property definition not found" if not items else "property name is ambiguous across groups"
            for name, items in matches.items()
            if len(items) != 1
        }
        requested_names = [matches[name][0] for name in required_properties if len(matches[name]) == 1]
        property_ids = []
        property_labels = []
        if requested_names:
            ids_result = _post_command(endpoint, "API.GetPropertyIds", {"properties": requested_names}, timeout=timeout)
            id_rows = ids_result.get("properties") or []
            for position, label_item in enumerate(requested_names):
                id_item = id_rows[position] if position < len(id_rows) else {}
                label = _property_name(label_item)
                if isinstance(id_item, dict) and isinstance(id_item.get("propertyId"), dict):
                    property_ids.append({"propertyId": id_item["propertyId"]})
                    property_labels.append(label)
                else:
                    error = id_item.get("error") if isinstance(id_item, dict) else None
                    unavailable_properties[label] = (
                        error.get("message") if isinstance(error, dict) else "property id was not returned"
                    )
        values_result = {"propertyValuesForElements": [{} for _ in elements]}
        if property_ids:
            values_result = _post_command(
                endpoint,
                "API.GetPropertyValuesOfElements",
                {"elements": elements, "properties": property_ids, "onlySupportedTypes": False},
                timeout=timeout,
            )
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        return {
            "source_model_version": None,
            "source_model_ref": endpoint,
            "selected_elements": [],
            "error": f"selected-element enrichment failed: {exc}",
        }

    type_rows = types_result.get("typesOfElements") or []
    value_rows = values_result.get("propertyValuesForElements") or []
    classification_details = classification_metadata.get("details") or {}
    classification_systems = classification_metadata.get("systems") or {}
    normalized = []
    for index, element in enumerate(elements):
        type_row = type_rows[index] if index < len(type_rows) else {}
        type_info = type_row.get("typeOfElement") if isinstance(type_row, dict) else {}
        element_type = type_info.get("elementType") if isinstance(type_info, dict) else None
        value_row = value_rows[index] if index < len(value_rows) else {}
        raw_values = value_row.get("propertyValues") if isinstance(value_row, dict) else []
        property_states = {
            name: _property_state(raw_values[position] if position < len(raw_values) else None)
            for position, name in enumerate(property_labels)
        }
        for name, error in unavailable_properties.items():
            property_states[name] = {"status": "unavailable", "value": None, "error": error}
        properties = {name: state.get("value") for name, state in property_states.items()}

        classification_row = classification_rows[index] if index < len(classification_rows) else {}
        classifications = []
        for value in classification_row.get("classificationIds", []) if isinstance(classification_row, dict) else []:
            classification_id = value.get("classificationId") if isinstance(value, dict) else None
            if not isinstance(classification_id, dict):
                continue
            system_id = _guid(classification_id.get("classificationSystemId"))
            item_id = _guid(classification_id.get("classificationItemId"))
            detail = classification_details.get(item_id) or {}
            system = classification_systems.get(system_id) or {}
            classifications.append(
                {
                    "system": system.get("name"),
                    "system_id": system_id,
                    "item_id": item_id,
                    "id": detail.get("id"),
                    "name": detail.get("name"),
                }
            )
        classification = next(
            (item.get("id") or item.get("name") for item in classifications if item.get("id") or item.get("name")),
            None,
        )
        properties_available = not unavailable_properties and all(
            property_states.get(name, {}).get("status") in {"normal", "userUndefined"}
            for name in required_properties
        )
        normalized.append(
            {
                "element_id": str(_element_guid(element)),
                "type": element_type,
                "classification": classification,
                "classifications": classifications,
                "classifications_available": not classification_error and bool(classification),
                "properties": properties,
                "properties_available": properties_available,
                "property_states": property_states,
            }
        )
    return {
        "source_model_version": None,
        "source_model_ref": endpoint,
        "selected_elements": normalized,
        "unavailable_properties": unavailable_properties,
        "classification_error": classification_error,
        "error": None,
    }


def selection_problem(selection):
    if selection.get("error"):
        return selection["error"]
    selected = selection.get("selected_elements") or []
    if not selected:
        return "no selected element was returned"
    zones = [item for item in selected if item.get("type") == "Zone" or item.get("classification") == "IfcSpace"]
    if not zones:
        return "the selection contains no Archicad Zone/IfcSpace"
    if selection.get("classification_error") or any(not item.get("classifications_available") for item in zones):
        return selection.get("classification_error") or "classifications are unavailable for a selected zone"
    unavailable = selection.get("unavailable_properties") or {}
    if unavailable:
        return "required properties are unavailable: " + ", ".join(sorted(unavailable))
    if any(not item.get("properties_available") for item in zones):
        return "required property values are unavailable for a selected zone"
    return None


def load_design_intent(path=DESIGN_INTENT_FIXTURE):
    intent = _load_json(path)
    required = {"intent_id", "project_context", "items"}
    missing = sorted(required - set(intent))
    if missing:
        raise ValueError(f"design intent missing fields: {missing}")
    if not isinstance(intent.get("items"), list) or not intent["items"]:
        raise ValueError("design intent requires at least one item")
    return intent


def missing_metadata_audit(selection, required_space_properties=REQUIRED_SPACE_PROPERTIES):
    missing = []
    for element in selection.get("selected_elements", []):
        if element.get("classification") != "IfcSpace" and element.get("type") != "Zone":
            continue
        properties = element.get("properties") or {}
        for prop in required_space_properties:
            if properties.get(prop) in (None, ""):
                missing.append(
                    {
                        "element_id": element["element_id"],
                        "classification": element["classification"],
                        "missing_property": prop,
                        "proposed_fix": f"Set {prop} from room program or architect approval.",
                    }
                )
    return {
        "source_model_version": selection.get("source_model_version"),
        "missing_count": len(missing),
        "missing": missing,
    }


def _selected_element_map(selection):
    return {item["element_id"]: item for item in selection.get("selected_elements", [])}


def dry_run_design_intent(intent=None, selection=None, ledger_data=None):
    intent = intent or load_design_intent()
    selection = selection or inspect_selected_elements()
    approved = _has_ledger_approval(ledger_data, scope_keyword="dry-run")
    elements = _selected_element_map(selection)
    actions = []
    for item in intent["items"]:
        if item["kind"] == "property_update":
            target = elements.get(item["target_element_id"], {})
            before = (target.get("properties") or {}).get(item["property_name"])
            actions.append(
                {
                    "item_id": item["item_id"],
                    "action": "set_property",
                    "target_element_id": item["target_element_id"],
                    "property_name": item["property_name"],
                    "before": before,
                    "after": item["proposed_value"],
                    "basis": item.get("basis", {}),
                    "supported": bool(target),
                }
            )
        elif item["kind"] == "drawing_annotation":
            actions.append(
                {
                    "item_id": item["item_id"],
                    "action": "prepare_annotation",
                    "target_view": item["target_view"],
                    "before": None,
                    "after": item["text"],
                    "basis": item.get("basis", {}),
                    "supported": True,
                }
            )
        else:
            actions.append(
                {
                    "item_id": item.get("item_id", "unknown"),
                    "action": "unsupported",
                    "before": None,
                    "after": None,
                    "basis": item.get("basis", {}),
                    "supported": False,
                }
            )
    return {
        "intent_id": intent["intent_id"],
        "adapter_id": intent["project_context"].get("adapter_id"),
        "source_model_version": selection.get("source_model_version"),
        "dry_run": True,
        "blocked": not approved,
        "approval_scope": "dry-run only",
        "action_count": len(actions),
        "unsupported_count": len([action for action in actions if not action["supported"]]),
        "actions": actions,
    }


def render_before_after_diff(dry_run):
    lines = [
        f"Intent: {dry_run['intent_id']}",
        f"Adapter: {dry_run['adapter_id']}",
        f"Model: {dry_run['source_model_version']}",
        f"Blocked: {str(dry_run['blocked']).lower()}",
    ]
    for action in dry_run["actions"]:
        if action["action"] == "set_property":
            lines.append(
                "Before/After: "
                f"{action['target_element_id']}.{action['property_name']} "
                f"{action['before']!r} -> {action['after']!r}"
            )
        elif action["action"] == "prepare_annotation":
            lines.append(
                "Before/After: "
                f"{action['target_view']} annotation None -> {action['after']!r}"
            )
        else:
            lines.append(f"Unsupported: {action['item_id']}")
    return "\n".join(lines)


def _has_ledger_approval(ledger_data, scope_keyword="property update"):
    if not ledger_data:
        return False
    for entry in ledger_data.get("entries", []):
        if entry.get("event_type") == "approval":
            after = entry.get("after_state") or {}
            text = " ".join(str(value).lower() for value in [entry.get("summary"), after.get("approval_scope")])
            if scope_keyword in text or "dry-run" in text:
                return True
        approval = entry.get("approval") or {}
        if approval.get("approved_by") and scope_keyword in approval.get("scope", "").lower():
            return True
    return False


def dry_run_property_update(element_id, property_name, value, ledger_data=None, before=None):
    approved = _has_ledger_approval(ledger_data)
    return {
        "action": "set_property",
        "element_id": element_id,
        "property_name": property_name,
        "before": before,
        "after": value,
        "proposed_value": value,
        "dry_run": True,
        "blocked": not approved,
        "required_approval": None if approved else {
            "approved_by": "required",
            "approved_at": "required",
            "basis": "required",
            "scope": f"Approve property update {element_id}.{property_name}",
        },
    }


def build_bridge_plan(adapter_id="archicad_json", action="inspect_selected_elements"):
    adapter = select_adapter(adapter_id)
    if action == "inspect_selected_elements":
        required_reads = {"selection", "elements", "properties"}
        mutating = False
    elif action == "set_room_usage_property":
        required_reads = {"selection", "elements", "properties"}
        required_write = "set_properties"
        mutating = True
        if required_write not in adapter["write_capabilities"]:
            raise ValueError(f"{adapter_id} cannot {required_write}")
    else:
        raise ValueError(f"unsupported action {action}")
    missing = sorted(required_reads - set(adapter["read_capabilities"]))
    if missing:
        raise ValueError(f"{adapter_id} missing read capabilities: {missing}")
    return {
        "adapter_id": adapter_id,
        "action": action,
        "mutating": mutating,
        "dry_run_required": mutating,
        "approval_required": mutating,
        "steps": [
            "check_adapter_alive",
            "capture_before_snapshot",
            "execute_read_commands" if not mutating else "prepare_write_commands",
            "render_diff_or_report",
            "write_memory_record",
        ],
    }


def build_agent_demo(ledger_path=None):
    ledger_data = _load_json(ledger_path) if ledger_path else None
    health = health_check("archicad_json")
    selection = inspect_selected_elements()
    audit = missing_metadata_audit(selection)
    intent = load_design_intent()
    dry_run = dry_run_design_intent(intent, selection, ledger_data)
    return {
        "demo_id": "AEDIFICA-R1A-AGENT-TO-SOFTWARE",
        "fixture_mode": True,
        "health": health,
        "selection": selection,
        "missing_metadata": audit,
        "design_intent": {
            "intent_id": intent["intent_id"],
            "item_count": len(intent["items"]),
        },
        "dry_run": dry_run,
        "diff": render_before_after_diff(dry_run),
    }


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(health_check("archicad_json"), ensure_ascii=False, indent=2))
    print(json.dumps(inspect_selected_elements(), ensure_ascii=False, indent=2))
    print(json.dumps(missing_metadata_audit(inspect_selected_elements()), ensure_ascii=False, indent=2))
    print(json.dumps(build_agent_demo(), ensure_ascii=False, indent=2))
    for action in ("inspect_selected_elements", "set_room_usage_property"):
        plan = build_bridge_plan("archicad_json", action)
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
