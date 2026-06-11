"""NOMOS bundle import adapter for Aedifica's existing reception tables.

W20-1 (#300): the importer is aligned on the *real* `nomos bundle` emitter
contract (``ckm-bundle-v1``, cf. NOMOS specs/canonical-knowledge-bundle.cue):

- ``schema_version`` is mandatory and gated (unknown/absent -> 422 with the
  explicit ``NOMOS_BUNDLE_SCHEMA_UNSUPPORTED`` code);
- spans are accepted in both the legacy ``{start, end}`` and the emitted
  ``{start_line, end_line}`` forms and normalized internally to the latter;
- ``feeds[].version`` is optional — when absent it is derived deterministically
  from ``bundle_id @ generated_at`` (same bundle -> same version -> immutability
  still holds);
- ``feeds[].jurisdiction`` is optional — the import endpoint is project-scoped,
  so missing fields default from the target project's commune/canton/country;
- ``rag_metadata`` is supported in the emitted bundle-level *list* form (joined
  to nodes by ``node_id``) in addition to the legacy feed-level dict; the joined
  per-node metadata is persisted (no silent ``{}`` loss).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import re
from typing import Any

from ..db import models as m

#: Bundle contract version this adapter understands (NOMOS SchemaVersion).
SCHEMA_VERSION = "ckm-bundle-v1"


class NomosBundleError(ValueError):
    """Raised when a NOMOS bundle cannot be safely imported.

    ``code`` is the structured API error code surfaced with the 422; the schema
    gate overrides it so a consumer can distinguish "wrong contract version"
    from "invalid payload".
    """

    code = "NOMOS_BUNDLE_INVALID"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


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


def _hash_digest(source_hash: str) -> str:
    """Return the hex digest of a possibly algo-prefixed hash (``sha256:<hex>``)."""
    if ":" in source_hash:
        return source_hash.split(":", 1)[1]
    return source_hash


def _normalize_span(span: Any, field: str) -> dict:
    """Accept both ``{start, end}`` (legacy) and ``{start_line, end_line}`` (emitted).

    Normalized to the emitted ``ckm-bundle-v1`` form. Extra span keys
    (``start_byte``/``end_byte``/``locator``) are preserved verbatim.
    """
    if not isinstance(span, dict):
        raise NomosBundleError(f"NOMOS bundle field {field} must trace start/end")
    start = span.get("start_line", span.get("start"))
    end = span.get("end_line", span.get("end"))
    if start is None or end is None:
        raise NomosBundleError(f"NOMOS bundle field {field} must trace start/end")
    normalized = {key: value for key, value in span.items() if key not in {"start", "end", "start_line", "end_line"}}
    normalized["start_line"] = start
    normalized["end_line"] = end
    return normalized


def _derive_version(bundle_id: str, generated_at: Any) -> str:
    """Deterministic feed version when the bundle does not carry one.

    The real emitter has no per-feed version; ``bundle_id@generated_at`` keeps
    re-imports of the *same* emitted artifact hitting the immutability check
    while distinct emissions stay distinct. Capped to CommunePack.version's 40
    chars with a deterministic hash tail when too long.
    """
    stamp = str(generated_at).strip() if generated_at else "unversioned"
    derived = f"{bundle_id}@{stamp}"
    if len(derived) > 40:
        derived = f"{derived[:31]}-{hashlib.sha256(derived.encode('utf-8')).hexdigest()[:8]}"
    return derived


def _validate_node(feed_id: str, node: Any) -> dict:
    node = _mapping(node, f"{feed_id}.nodes[]")
    node_id = _text(node.get("node_id"), f"{feed_id}.nodes[].node_id")
    text = _text(node.get("text"), f"{feed_id}.{node_id}.text")
    source_path = _text(node.get("source_path"), f"{feed_id}.{node_id}.source_path")
    source_hash = _text(node.get("source_hash"), f"{feed_id}.{node_id}.source_hash")
    span = _normalize_span(node.get("span"), f"{feed_id}.{node_id}.span")
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


def _bundle_rag_index(bundle: dict) -> dict[str, dict]:
    """Index the emitted bundle-level ``rag_metadata`` list by ``node_id``."""
    rag = bundle.get("rag_metadata")
    if rag is None or isinstance(rag, dict):
        # Legacy bundles carry rag metadata per feed (dict) or not at all.
        return {}
    if not isinstance(rag, list):
        raise NomosBundleError("NOMOS bundle field rag_metadata must be a list of node entries")
    index: dict[str, dict] = {}
    for position, entry in enumerate(rag):
        entry = _mapping(entry, f"rag_metadata[{position}]")
        node_id = _text(entry.get("node_id"), f"rag_metadata[{position}].node_id")
        index[node_id] = entry
    return index


def _feed_rag_metadata(feed: dict, feed_id: str, node_ids: list[str], bundle_rag: dict[str, dict]) -> dict[str, dict]:
    """Join rag metadata onto this feed's nodes (bundle-level list and/or legacy dict)."""
    joined: dict[str, dict] = {node_id: bundle_rag[node_id] for node_id in node_ids if node_id in bundle_rag}
    legacy = feed.get("rag_metadata")
    if legacy is not None:
        legacy = _mapping(legacy, f"{feed_id}.rag_metadata")
        for node_id, entry in legacy.items():
            joined[str(node_id)] = _mapping(entry, f"{feed_id}.rag_metadata[{node_id}]")
    return joined


def _validate_feed(bundle: dict, feed: Any, *, project: m.Project, bundle_rag: dict[str, dict]) -> dict:
    feed = _mapping(feed, "feeds[]")
    feed_id = _slug(_text(feed.get("feed_id"), "feeds[].feed_id"), 40)
    if feed.get("version") is not None:
        version = _text(feed.get("version"), f"{feed_id}.version")
    else:
        version = _derive_version(str(bundle.get("bundle_id") or "nomos-bundle"), bundle.get("generated_at"))
    # The emitter carries no jurisdiction: the import endpoint is project-scoped,
    # so the target project's own jurisdiction is the honest default.
    jurisdiction = feed.get("jurisdiction")
    if jurisdiction is None:
        jurisdiction = {}
    jurisdiction = _mapping(jurisdiction, f"{feed_id}.jurisdiction")
    commune = _text(jurisdiction.get("commune") or project.commune, f"{feed_id}.jurisdiction.commune")
    canton = _text(jurisdiction.get("canton") or project.canton, f"{feed_id}.jurisdiction.canton")
    country = _text(jurisdiction.get("country") or project.country or "CH", f"{feed_id}.jurisdiction.country")
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
        "country": country,
        "trace_manifest": trace_manifest,
        "nodes": validated_nodes,
        "rag_metadata": _feed_rag_metadata(feed, feed_id, node_ids, bundle_rag),
    }


def _validate_bundle(bundle: dict, *, project: m.Project) -> list[dict]:
    bundle = _mapping(bundle, "bundle")
    schema_version = bundle.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise NomosBundleError(
            f"NOMOS bundle schema_version {schema_version!r} is not supported (expected {SCHEMA_VERSION!r})",
            code="NOMOS_BUNDLE_SCHEMA_UNSUPPORTED",
        )
    feeds = bundle.get("feeds")
    if not isinstance(feeds, list) or not feeds:
        raise NomosBundleError("NOMOS bundle has no feeds")
    bundle_rag = _bundle_rag_index(bundle)
    validated = [_validate_feed(bundle, feed, project=project, bundle_rag=bundle_rag) for feed in feeds]
    all_node_ids = {node["node_id"] for feed in validated for node in feed["nodes"]}
    orphans = sorted(set(bundle_rag) - all_node_ids)
    if orphans:
        raise NomosBundleError(f"NOMOS bundle rag_metadata references unknown node ids: {', '.join(orphans[:5])}")
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
    return _slug(f"nomos:{feed_id}:{_hash_digest(source_hash)[:12]}", 80)


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

    feeds = _validate_bundle(bundle, project=project)
    bundle_id = str(bundle.get("bundle_id") or "nomos-bundle")
    bundle_version = str(bundle.get("version") or bundle.get("generated_at") or "unknown")
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
                        "rag_metadata": feed["rag_metadata"],
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
