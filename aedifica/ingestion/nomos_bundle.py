"""NOMOS bundle import adapter for Aedifica's existing reception tables."""
from __future__ import annotations

import datetime as _dt
import re
from typing import Any

from ..db import models as m


class NomosBundleError(ValueError):
    """Raised when a NOMOS bundle cannot be safely imported."""


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _slug(value: str, max_len: int) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "-", value.strip()).strip("-")
    return (cleaned or "unknown")[:max_len]


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NomosBundleError(f"NOMOS bundle field {field} is required")
    return value.strip()


def _mapping(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise NomosBundleError(f"NOMOS bundle field {field} must be an object")
    return value


def _validate_node(feed_id: str, node: Any) -> dict:
    node = _mapping(node, f"{feed_id}.nodes[]")
    node_id = _text(node.get("node_id"), f"{feed_id}.nodes[].node_id")
    text = _text(node.get("text"), f"{feed_id}.{node_id}.text")
    source_path = _text(node.get("source_path"), f"{feed_id}.{node_id}.source_path")
    source_hash = _text(node.get("source_hash"), f"{feed_id}.{node_id}.source_hash")
    span = node.get("span")
    if not isinstance(span, dict) or "start" not in span or "end" not in span:
        raise NomosBundleError(f"NOMOS bundle field {feed_id}.{node_id}.span must trace start/end")
    facets = node.get("facets", {})
    if facets is not None and not isinstance(facets, dict):
        raise NomosBundleError(f"NOMOS bundle field {feed_id}.{node_id}.facets must be an object")
    parent_chain = node.get("parent_chain", [])
    if parent_chain is not None and not isinstance(parent_chain, list):
        raise NomosBundleError(f"NOMOS bundle field {feed_id}.{node_id}.parent_chain must be a list")
    return {
        "node": node,
        "node_id": node_id,
        "text": text,
        "source_path": source_path,
        "source_hash": source_hash,
        "span": span,
    }


def _validate_feed(bundle: dict, feed: Any) -> dict:
    feed = _mapping(feed, "feeds[]")
    feed_id = _slug(_text(feed.get("feed_id"), "feeds[].feed_id"), 40)
    version = _text(feed.get("version"), f"{feed_id}.version")
    jurisdiction = _mapping(feed.get("jurisdiction"), f"{feed_id}.jurisdiction")
    commune = _text(jurisdiction.get("commune"), f"{feed_id}.jurisdiction.commune")
    canton = _text(jurisdiction.get("canton"), f"{feed_id}.jurisdiction.canton")
    trace_manifest = feed.get("trace_manifest") or bundle.get("trace_manifest")
    if not isinstance(trace_manifest, dict) or not trace_manifest:
        raise NomosBundleError(f"NOMOS bundle feed {feed_id} has no trace manifest")
    nodes = feed.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise NomosBundleError(f"NOMOS bundle feed {feed_id} has no nodes")
    validated_nodes = [_validate_node(feed_id, node) for node in nodes]
    node_ids = [node["node_id"] for node in validated_nodes]
    if len(set(node_ids)) != len(node_ids):
        raise NomosBundleError(f"NOMOS bundle feed {feed_id} has duplicate node ids")
    return {
        "feed": feed,
        "feed_id": feed_id,
        "version": version,
        "commune": commune,
        "canton": canton,
        "trace_manifest": trace_manifest,
        "nodes": validated_nodes,
    }


def _validate_bundle(bundle: dict) -> list[dict]:
    bundle = _mapping(bundle, "bundle")
    feeds = bundle.get("feeds")
    if not isinstance(feeds, list) or not feeds:
        raise NomosBundleError("NOMOS bundle has no feeds")
    validated = [_validate_feed(bundle, feed) for feed in feeds]
    seen_versions: set[tuple[str, str, str]] = set()
    for feed in validated:
        key = (feed["commune"], feed["canton"], feed["version"])
        if key in seen_versions:
            raise NomosBundleError(f"NOMOS feed version {feed['version']!r} is immutable")
        seen_versions.add(key)
    return validated


def _source_id(feed_id: str, source_hash: str, node: dict) -> str:
    explicit = node.get("source_id")
    if explicit:
        return _slug(str(explicit), 80)
    return _slug(f"nomos:{feed_id}:{source_hash[:12]}", 80)


def _claim_title(node: dict, text: str) -> str:
    claim = node.get("claim") if isinstance(node.get("claim"), dict) else {}
    title = claim.get("title") or node.get("title")
    if title:
        return str(title)[:300]
    return text[:80]


def _claim_value(node: dict, text: str) -> Any:
    claim = node.get("claim") if isinstance(node.get("claim"), dict) else {}
    if "value" in claim:
        return claim["value"]
    return {"text": text}


def _zone_entry(node: dict, text: str) -> tuple[str, Any] | None:
    claim = node.get("claim") if isinstance(node.get("claim"), dict) else {}
    facets = node.get("facets") if isinstance(node.get("facets"), dict) else {}
    zone = claim.get("zone") or node.get("zone") or facets.get("zone")
    if not zone:
        return None
    return str(zone), _claim_value(node, text)


def _source_ref(source_id: str, parsed_node: dict) -> dict:
    node = parsed_node["node"]
    return {
        "source_id": source_id,
        "node_id": parsed_node["node_id"],
        "source_hash": parsed_node["source_hash"],
        "source_path": parsed_node["source_path"],
        "span": parsed_node["span"],
        "parent_chain": node.get("parent_chain", []),
    }


def import_nomos_bundle(
    session,
    project: m.Project,
    bundle: dict,
    *,
    nomos_enabled: bool = False,
    activate: bool = False,
) -> dict:
    """Import a versioned NOMOS bundle into CommunePack/Source/Evidence/Claim.

    The adapter is deliberately flag-gated and additive. Each feed version creates
    a new immutable CommunePack row; it never mutates an existing pack version.
    """
    if not nomos_enabled:
        raise NomosBundleError("NOMOS bundle import is disabled")

    feeds = _validate_bundle(bundle)
    bundle_id = str(bundle.get("bundle_id") or "nomos-bundle")
    bundle_version = str(bundle.get("version") or "unknown")
    imported = {"packs": 0, "sources": 0, "evidence": 0, "claims": 0, "activated": [], "versions": []}

    with session.begin_nested():
        for feed in feeds:
            exists = (
                session.query(m.CommunePack)
                .filter_by(commune=feed["commune"], canton=feed["canton"], version=feed["version"])
                .first()
            )
            if exists is not None:
                raise NomosBundleError(f"NOMOS feed version {feed['version']!r} is immutable")

        for feed in feeds:
            raw_feed = feed["feed"]
            zones: dict[str, Any] = {}
            for parsed_node in feed["nodes"]:
                entry = _zone_entry(parsed_node["node"], parsed_node["text"])
                if entry is not None:
                    zones[entry[0]] = entry[1]

            pack = m.CommunePack(
                commune=feed["commune"],
                canton=feed["canton"],
                version=feed["version"],
                status="supported" if activate else "ingested",
                source_authority=raw_feed.get("source_authority"),
                valid_as_of=raw_feed.get("valid_as_of"),
                review_due=raw_feed.get("review_due"),
                ingested_at=_now_iso(),
                data={
                    "zones": zones,
                    "nomos": {
                        "bundle_id": bundle_id,
                        "bundle_version": bundle_version,
                        "feed_id": feed["feed_id"],
                        "feed_version": feed["version"],
                        "trace_manifest": feed["trace_manifest"],
                        "rag_metadata": raw_feed.get("rag_metadata", {}),
                    },
                },
            )
            session.add(pack)
            session.flush()
            session.add(
                m.IngestionJob(
                    commune_pack_id=pack.id,
                    status="done",
                    sources=[
                        {
                            "node_id": node["node_id"],
                            "source_path": node["source_path"],
                            "source_hash": node["source_hash"],
                        }
                        for node in feed["nodes"]
                    ],
                    notes=f"NOMOS bundle {bundle_id}@{bundle_version}",
                )
            )
            imported["packs"] += 1
            imported["versions"].append(feed["version"])
            if activate:
                imported["activated"].append(feed["version"])

            seen_sources: set[str] = set()
            for parsed_node in feed["nodes"]:
                node = parsed_node["node"]
                facets = dict(node.get("facets") or {})
                source_id = _source_id(feed["feed_id"], parsed_node["source_hash"], node)
                if source_id not in seen_sources:
                    seen_sources.add(source_id)
                    session.add(
                        m.Source(
                            project_id=project.id,
                            source_id=source_id,
                            title=str(node.get("source_title") or parsed_node["source_path"])[:300],
                            kind="nomos_bundle",
                            locator=parsed_node["source_path"],
                            valid_as_of=raw_feed.get("valid_as_of"),
                            retrieved_at=_now_iso(),
                            sha256=parsed_node["source_hash"],
                            trust_tier=facets.get("trust_tier", "unverified"),
                            provenance=facets.get("provenance", "official"),
                            facets=facets,
                        )
                    )
                    imported["sources"] += 1

                evidence_id = _slug(f"nomos:{feed['feed_id']}:{parsed_node['node_id']}", 120)
                session.add(
                    m.Evidence(
                        project_id=project.id,
                        evidence_id=evidence_id,
                        kind="nomos_node",
                        file_ref=parsed_node["source_path"],
                        sha256=parsed_node["source_hash"],
                        source_id=source_id,
                        valid_as_of=raw_feed.get("valid_as_of"),
                        retrieved_at=_now_iso(),
                    )
                )
                imported["evidence"] += 1

                claim = node.get("claim") if isinstance(node.get("claim"), dict) else {}
                claim_id = _slug(str(claim.get("claim_id") or f"nomos:{feed['feed_id']}:{parsed_node['node_id']}"), 120)
                session.add(
                    m.Claim(
                        project_id=project.id,
                        claim_id=claim_id,
                        title=_claim_title(node, parsed_node["text"]),
                        claim_type=str(claim.get("claim_type") or "regulatory"),
                        state="sourced",
                        value=_claim_value(node, parsed_node["text"]),
                        confidence=str(claim.get("confidence") or "high"),
                        source_refs=[_source_ref(source_id, parsed_node)],
                        trust_tier=facets.get("trust_tier", "unverified"),
                        provenance=facets.get("provenance", "official"),
                        facets=facets,
                    )
                )
                imported["claims"] += 1
        session.flush()

    return imported
