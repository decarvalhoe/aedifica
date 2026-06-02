"""Build a persistable parcel brief from a live address/EGRID (or offline fallback)."""
from __future__ import annotations

import os

from aedifica import _bootstrap  # noqa: F401  (puts the stdlib pilot engine on sys.path)

import domain as _domain  # noqa: E402  (pilot)
import opposition_radar as _radar  # noqa: E402  (pilot)
import selector as _selector  # noqa: E402  (pilot)
import trust as _trust  # noqa: E402  (pilot)
import workspace as _ws  # noqa: E402  (pilot)

DEMO_DIR = os.path.join(_bootstrap.PILOT_DIR, "projects", "demo_lausanne_palud")


def _fallback(reason: str) -> dict:
    brief = _ws.generate_offline_parcel_brief(DEMO_DIR)
    brief["mode"] = "fixture"
    brief["reason"] = reason
    return brief


def build_live_brief(query: str, live: bool = True) -> dict:
    """Return a brief dict (full engine claims + source refs) ready for save_brief."""
    if not (live and query):
        return _fallback("offline mode" if not live else "empty query")
    try:
        oereb_record, e, n, area = _radar.resolve(query)
        if not oereb_record or not oereb_record.get("egrid"):
            raise RuntimeError("no parcel resolved")
    except (Exception, SystemExit) as exc:
        return _fallback(f"live lookup unavailable ({exc})")

    commune = oereb_record.get("commune")
    rpga = _domain.load_commune_ruleset(commune)
    _, zone_params, _method = _domain.match_communal_zone(
        rpga, {"zone": oereb_record.get("zone"), "parcel": oereb_record.get("parcel")}
    )
    zone_params = zone_params or {}
    area_value = oereb_record.get("area_m2") or area
    envelope = _domain.calculate_envelope(area_value, zone_params)
    source_ref = {
        "source_id": "VD-OEREB",
        "locator": f"EGRID {oereb_record.get('egrid')}",
        "valid_as_of": oereb_record.get("valid_as_of", "live"),
        "confidence": "high",
    }
    claims = _ws._constraint_claims(oereb_record, source_ref) + _ws._envelope_claims(envelope, [source_ref])
    route = _selector.regulatory_route("CH", "VD", commune)

    return {
        "mode": "live",
        "reason": None,
        "brief_id": f"BRIEF-LIVE-{oereb_record.get('egrid')}",
        "parcel": {
            "egrid": oereb_record.get("egrid"),
            "number": oereb_record.get("parcel"),
            "commune": commune,
            "zone": oereb_record.get("zone"),
            "area_m2": area_value,
        },
        "claims": claims,
        "source_refs": [source_ref],
        "evidence_refs": [],
        "regulatory_route": route,
        "trust_footer": _trust.render_footer("fr"),
    }
