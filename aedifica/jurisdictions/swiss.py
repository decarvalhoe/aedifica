"""Swiss canton + commune resolver, backed by the official OFS register.

The dataset lives at ``aedifica/jurisdictions/data/ch_communes.json`` and is
a snapshot of the Federal Statistical Office (BFS) "Application du
répertoire officiel des communes de Suisse" (AGVCH) — see
https://www.agvchapp.bfs.admin.ch . The snapshot is refreshed via
``pilot/refresh_communes.py`` (manually or by the monthly GitHub Actions
workflow), so every push to main carries an up-to-date register.

Two flavours of name appear in the OFS data:

  - Unique communes: the canonical name is the single field (e.g.,
    "Lausanne", "Neuchâtel", "Sion"). A user typing the exact (or
    diacritic-normalised) name lands on an "exact" verdict.

  - Disambiguated homonyms: when several communes share the same base
    name, OFS appends the canton in parentheses — "Wald (AR)", "Wald (BE)",
    "Wald (ZH)" — so the canonical form is unique. The resolver detects
    this pattern: typing just "Wald" returns an "ambiguous" verdict with
    the three candidates so the UI can ask.

A small Aedifica-curated alias table covers bilingual/synonym entries
(Bienne→Biel/Bienne, Saint-Gall→St. Gallen, Berne→Bern, Genf→Genève) — every
alias is marked as such; the source of truth stays the OFS register.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data" / "ch_communes.json"

# ---------------------------------------------------------------------------
# Canton register (26 cantons) — kept in code (small, stable, multilingual)
# ---------------------------------------------------------------------------

CANTONS: dict[str, dict[str, str]] = {
    "AG": {"fr": "Argovie", "de": "Aargau", "it": "Argovia"},
    "AI": {"fr": "Appenzell Rhodes-Intérieures", "de": "Appenzell Innerrhoden", "it": "Appenzello Interno"},
    "AR": {"fr": "Appenzell Rhodes-Extérieures", "de": "Appenzell Ausserrhoden", "it": "Appenzello Esterno"},
    "BE": {"fr": "Berne", "de": "Bern", "it": "Berna"},
    "BL": {"fr": "Bâle-Campagne", "de": "Basel-Landschaft", "it": "Basilea Campagna"},
    "BS": {"fr": "Bâle-Ville", "de": "Basel-Stadt", "it": "Basilea Città"},
    "FR": {"fr": "Fribourg", "de": "Freiburg", "it": "Friburgo"},
    "GE": {"fr": "Genève", "de": "Genf", "it": "Ginevra"},
    "GL": {"fr": "Glaris", "de": "Glarus", "it": "Glarona"},
    "GR": {"fr": "Grisons", "de": "Graubünden", "it": "Grigioni"},
    "JU": {"fr": "Jura", "de": "Jura", "it": "Giura"},
    "LU": {"fr": "Lucerne", "de": "Luzern", "it": "Lucerna"},
    "NE": {"fr": "Neuchâtel", "de": "Neuenburg", "it": "Neuchâtel"},
    "NW": {"fr": "Nidwald", "de": "Nidwalden", "it": "Nidvaldo"},
    "OW": {"fr": "Obwald", "de": "Obwalden", "it": "Obvaldo"},
    "SG": {"fr": "Saint-Gall", "de": "St. Gallen", "it": "San Gallo"},
    "SH": {"fr": "Schaffhouse", "de": "Schaffhausen", "it": "Sciaffusa"},
    "SO": {"fr": "Soleure", "de": "Solothurn", "it": "Soletta"},
    "SZ": {"fr": "Schwytz", "de": "Schwyz", "it": "Svitto"},
    "TG": {"fr": "Thurgovie", "de": "Thurgau", "it": "Turgovia"},
    "TI": {"fr": "Tessin", "de": "Tessin", "it": "Ticino"},
    "UR": {"fr": "Uri", "de": "Uri", "it": "Uri"},
    "VD": {"fr": "Vaud", "de": "Waadt", "it": "Vaud"},
    "VS": {"fr": "Valais", "de": "Wallis", "it": "Vallese"},
    "ZG": {"fr": "Zoug", "de": "Zug", "it": "Zugo"},
    "ZH": {"fr": "Zurich", "de": "Zürich", "it": "Zurigo"},
}

# ---------------------------------------------------------------------------
# Curated bilingual / synonym aliases.
# ---------------------------------------------------------------------------
# Source of truth = OFS canonical name. These aliases catch common
# alternative spellings the OFS register does NOT list (a French speaker
# typing "Berne" instead of the canonical "Bern", or "Bienne" instead of
# "Biel/Bienne"). Each entry maps an alias → the OFS canonical name.
ALIASES: dict[str, str] = {
    # Capital + major French-speaking aliases
    "Berne": "Bern",
    "Bienne": "Biel/Bienne",
    "Biel": "Biel/Bienne",
    "Bâle": "Basel",
    "Bale": "Basel",
    "Genf": "Genève",
    "Geneva": "Genève",
    "Ginevra": "Genève",
    "Saint-Gall": "St. Gallen",
    "Sankt Gallen": "St. Gallen",
    "San Gallo": "St. Gallen",
    "Lugano": "Lugano",
    "Zurich": "Zürich",
    "Zurigo": "Zürich",
    "Coire": "Chur",
    "Soleure": "Solothurn",
    "Lucerne": "Luzern",
    "Lucerna": "Luzern",
    "Schaffhouse": "Schaffhausen",
    "Sciaffusa": "Schaffhausen",
    "Sion": "Sion",
    "Sitten": "Sion",
    "Sierre": "Sierre",
    "Siders": "Sierre",
    "Neuenburg": "Neuchâtel",
    "Friburgo": "Fribourg",
    "Freiburg": "Fribourg",
    "Thoune": "Thun",
    "Berthoud": "Burgdorf",
    "Delemont": "Delémont",
    "Yverdon": "Yverdon-les-Bains",
    "Bellinzone": "Bellinzona",
    "Bellinzona": "Bellinzona",
}


# ---------------------------------------------------------------------------
# Normalisation + indexing
# ---------------------------------------------------------------------------


def _normalise(name: str) -> str:
    """Strip casing, diacritics, and most punctuation. Keeps slashes
    (Biel/Bienne) and digits as significant. Collapses runs of whitespace
    and hyphens so 'Saint-Aubin' and 'Saint Aubin' collide."""
    nfkd = unicodedata.normalize("NFKD", name.strip().casefold())
    stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return " ".join(stripped.replace("-", " ").replace(".", " ").split())


# OFS disambiguation suffix, e.g. "Wald (AR)" → ("Wald", "AR").
_SUFFIX_RE = re.compile(r"^(?P<base>.+?)\s*\((?P<canton>[A-Z]{2})\)\s*$")


@lru_cache(maxsize=1)
def _load() -> dict:
    """Load + index the OFS snapshot. Cached so module import stays cheap."""
    if not DATA.exists():
        return {"meta": {}, "exact": {}, "homonyms": {}, "all_cantons": list(CANTONS.keys())}
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    # Build two indices:
    #   exact[norm_name]    → {"canonical": ..., "canton": ..., "bfs": ...}
    #   homonyms[norm_base] → [{"canton": ..., "canonical": "Wald (AR)", "bfs": ...}, ...]
    exact: dict[str, dict] = {}
    homonyms: dict[str, list[dict]] = {}
    for canonical, entries in raw.get("communes", {}).items():
        for e in entries:
            norm_full = _normalise(canonical)
            exact[norm_full] = {"canonical": canonical, "canton": e["canton"], "bfs": e["bfs"]}
            m = _SUFFIX_RE.match(canonical)
            if m:
                norm_base = _normalise(m.group("base"))
                homonyms.setdefault(norm_base, []).append(
                    {"canonical": canonical, "canton": m.group("canton"), "bfs": e["bfs"]}
                )
    # Resolve aliases against the exact map.
    for alias, target in ALIASES.items():
        norm_alias = _normalise(alias)
        if norm_alias in exact:
            continue  # alias collides with a real commune name — keep the real one
        norm_target = _normalise(target)
        if norm_target in exact:
            exact[norm_alias] = {**exact[norm_target], "alias_of": target}
    return {
        "meta": {
            "source": raw.get("source"),
            "snapshot_date": raw.get("snapshot_date"),
            "fetched_at": raw.get("fetched_at"),
            "n_communes": raw.get("n_communes"),
            "n_cantons": raw.get("n_cantons"),
        },
        "exact": exact,
        "homonyms": homonyms,
        "all_cantons": list(CANTONS.keys()),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_swiss(commune: str) -> dict:
    """Three-state verdict for a free-text commune input."""
    if not commune or not commune.strip():
        return {"country": "CH", "commune": commune, "confidence": "unknown", "candidates": [],
                "all_cantons": list(CANTONS.keys())}
    index = _load()
    key = _normalise(commune)

    # 1) Exact match (after normalisation + alias resolution).
    hit = index["exact"].get(key)
    if hit:
        return {
            "country": "CH",
            "commune": commune,
            "canton": hit["canton"],
            "confidence": "exact",
            "candidates": [{"canton": hit["canton"], "name": CANTONS[hit["canton"]]["fr"]}],
            "canonical": hit["canonical"],
            "bfs": hit["bfs"],
            **({"alias_of": hit["alias_of"]} if "alias_of" in hit else {}),
        }

    # 2) Homonym base — user typed "Wald" and OFS only knows "Wald (XX)".
    hcandidates = index["homonyms"].get(key, [])
    if hcandidates:
        cantons: list[str] = []
        for h in hcandidates:
            if h["canton"] not in cantons:
                cantons.append(h["canton"])
        if len(cantons) == 1:
            # All disambiguated entries land in the same canton — treat as
            # exact with the first canonical form.
            h0 = hcandidates[0]
            return {
                "country": "CH",
                "commune": commune,
                "canton": h0["canton"],
                "confidence": "exact",
                "candidates": [{"canton": h0["canton"], "name": CANTONS[h0["canton"]]["fr"]}],
                "canonical": h0["canonical"],
                "bfs": h0["bfs"],
            }
        return {
            "country": "CH",
            "commune": commune,
            "confidence": "ambiguous",
            "candidates": [
                {"canton": c, "name": CANTONS[c]["fr"],
                 "canonical": next(h["canonical"] for h in hcandidates if h["canton"] == c)}
                for c in cantons
            ],
        }

    # 3) Unknown — fall back to the 26-canton dropdown.
    return {"country": "CH", "commune": commune, "confidence": "unknown",
            "candidates": [], "all_cantons": list(CANTONS.keys())}


def list_swiss_cantons() -> list[dict]:
    return [{"canton": code, "name": names["fr"]}
            for code, names in sorted(CANTONS.items(), key=lambda kv: kv[1]["fr"])]


def freshness() -> dict:
    """Metadata about the loaded OFS snapshot. Used by the UI to surface
    the data-freshness chip ("Données OFS au 1.1.2025")."""
    return _load()["meta"]
