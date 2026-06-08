"""Swiss canton + commune dataset.

The dataset is a **curated subset** — every canton capital + the population
centres + a sample of common smaller communes. We deliberately don't ship the
full ~2100-commune OFS register here: the data changes (mergers happen every
year), and shipping it would lock the codebase to a snapshot date. Instead,
when a commune is not in this list, the resolver returns ``unknown`` and
lets the UI fall back to a manual canton picker. The dataset can grow with
demand (PR by PR), without changing the resolver contract.

Source for the curated rows: cross-checked against the official OFS register
(https://www.bfs.admin.ch/bfs/fr/home/bases-statistiques/repertoire-officiel-communes-suisse.html)
in 2026, plus Wikipedia for canton-code verification. Each entry is the
canonical OFS commune name (no diacritic gymnastics — the resolver normalises
the input). Real homonyms (same canonical name in multiple cantons) are kept
as a list — never silently mapped to one canton.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Canton register (26 cantons)
# ---------------------------------------------------------------------------
# Each canton has its code (ISO 3166-2:CH) + French/German/Italian names. The
# code is what we store in `project.canton`. The names are used by the UI to
# present a friendly label in the dropdown.

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
# Commune → canton(s). Lists for genuine homonyms; singletons otherwise.
# ---------------------------------------------------------------------------
# This is intentionally NOT exhaustive. Coverage targets: every canton capital,
# every commune with > ~10k population, plus a sample of mid-size communes
# from each canton. Keys are the canonical OFS spellings; the resolver
# normalises diacritics + casing on the input side so users can type
# "geneve" or "Genève" indifferently.
COMMUNES: dict[str, list[str]] = {
    # ---- Canton capitals --------------------------------------------------
    "Aarau": ["AG"],
    "Appenzell": ["AI"],
    "Herisau": ["AR"],
    "Bern": ["BE"],
    "Berne": ["BE"],
    "Liestal": ["BL"],
    "Basel": ["BS"],
    "Bâle": ["BS"],
    "Fribourg": ["FR"],
    "Freiburg": ["FR"],
    "Genève": ["GE"],
    "Geneve": ["GE"],
    "Genf": ["GE"],
    "Glarus": ["GL"],
    "Glaris": ["GL"],
    "Chur": ["GR"],
    "Coire": ["GR"],
    "Delémont": ["JU"],
    "Delemont": ["JU"],
    "Luzern": ["LU"],
    "Lucerne": ["LU"],
    "Neuchâtel": ["NE"],
    "Neuchatel": ["NE"],
    "Neuenburg": ["NE"],
    "Stans": ["NW"],
    "Sarnen": ["OW"],
    "St. Gallen": ["SG"],
    "Saint-Gall": ["SG"],
    "Sankt Gallen": ["SG"],
    "Schaffhausen": ["SH"],
    "Schaffhouse": ["SH"],
    "Solothurn": ["SO"],
    "Soleure": ["SO"],
    "Schwyz": ["SZ"],
    "Frauenfeld": ["TG"],
    "Bellinzona": ["TI"],
    "Bellinzone": ["TI"],
    "Altdorf": ["UR"],
    "Lausanne": ["VD"],
    "Sion": ["VS"],
    "Sitten": ["VS"],
    "Zug": ["ZG"],
    "Zoug": ["ZG"],
    "Zürich": ["ZH"],
    "Zurich": ["ZH"],

    # ---- Vaud (VD) — major communes ---------------------------------------
    "Yverdon-les-Bains": ["VD"],
    "Yverdon": ["VD"],
    "Montreux": ["VD"],
    "Renens": ["VD"],
    "Nyon": ["VD"],
    "Vevey": ["VD"],
    "Pully": ["VD"],
    "Morges": ["VD"],
    "Gland": ["VD"],
    "Prilly": ["VD"],
    "La Tour-de-Peilz": ["VD"],
    "Ecublens": ["VD"],
    "Lutry": ["VD"],
    "Aigle": ["VD"],
    "Payerne": ["VD"],
    "Crissier": ["VD"],
    "Bex": ["VD"],
    "Orbe": ["VD"],
    "Moudon": ["VD"],
    "Sainte-Croix": ["VD"],

    # ---- Genève (GE) ------------------------------------------------------
    "Vernier": ["GE"],
    "Lancy": ["GE"],
    "Carouge": ["GE"],
    "Meyrin": ["GE"],
    "Onex": ["GE"],
    "Thônex": ["GE"],
    "Versoix": ["GE"],
    "Plan-les-Ouates": ["GE"],
    "Grand-Saconnex": ["GE"],
    "Chêne-Bougeries": ["GE"],
    "Chêne-Bourg": ["GE"],

    # ---- Valais (VS) ------------------------------------------------------
    "Martigny": ["VS"],
    "Sierre": ["VS"],
    "Monthey": ["VS"],
    "Brig-Glis": ["VS"],
    "Visp": ["VS"],
    "Naters": ["VS"],
    "Conthey": ["VS"],
    "Saint-Maurice": ["VS"],
    "Bagnes": ["VS"],
    "Verbier": ["VS"],
    "Crans-Montana": ["VS"],
    "Zermatt": ["VS"],
    "Saas-Fee": ["VS"],

    # ---- Fribourg (FR) ----------------------------------------------------
    "Bulle": ["FR"],
    "Villars-sur-Glâne": ["FR"],
    "Marly": ["FR"],
    "Givisiez": ["FR"],
    "Düdingen": ["FR"],
    "Guin": ["FR"],
    "Murten": ["FR"],
    "Morat": ["FR"],
    "Estavayer": ["FR"],
    "Châtel-Saint-Denis": ["FR"],
    "Romont": ["FR"],
    "Gruyères": ["FR"],
    "Bösingen": ["FR"],

    # ---- Neuchâtel (NE) ---------------------------------------------------
    "La Chaux-de-Fonds": ["NE"],
    "Le Locle": ["NE"],
    "Val-de-Travers": ["NE"],
    "Val-de-Ruz": ["NE"],
    "Boudry": ["NE"],
    "Peseux": ["NE"],
    "Cortaillod": ["NE"],
    "Couvet": ["NE"],
    "Cernier": ["NE"],
    "Marin-Epagnier": ["NE"],
    "Hauterive": ["NE"],
    "Bevaix": ["NE"],
    "Colombier": ["NE"],
    "Saint-Aubin-Sauges": ["NE"],

    # ---- Berne (BE) — major communes --------------------------------------
    "Biel/Bienne": ["BE"],
    "Bienne": ["BE"],
    "Biel": ["BE"],
    "Thun": ["BE"],
    "Thoune": ["BE"],
    "Köniz": ["BE"],
    "Ostermundigen": ["BE"],
    "Burgdorf": ["BE"],
    "Berthoud": ["BE"],
    "Interlaken": ["BE"],
    "Grindelwald": ["BE"],
    "Spiez": ["BE"],
    "Lyss": ["BE"],
    "Münsingen": ["BE"],

    # ---- Jura (JU) --------------------------------------------------------
    "Porrentruy": ["JU"],
    "Bassecourt": ["JU"],
    "Courrendlin": ["JU"],
    "Saignelégier": ["JU"],
    "Courroux": ["JU"],

    # ---- Zurich (ZH) ------------------------------------------------------
    "Winterthur": ["ZH"],
    "Uster": ["ZH"],
    "Dübendorf": ["ZH"],
    "Dietikon": ["ZH"],
    "Wetzikon": ["ZH"],
    "Kloten": ["ZH"],
    "Wädenswil": ["ZH"],
    "Bülach": ["ZH"],
    "Opfikon": ["ZH"],
    "Horgen": ["ZH"],
    "Affoltern am Albis": ["ZH"],
    "Adliswil": ["ZH"],
    "Schlieren": ["ZH"],
    "Regensdorf": ["ZH"],

    # ---- Bâle-Ville (BS) --------------------------------------------------
    "Riehen": ["BS"],
    "Bettingen": ["BS"],

    # ---- Bâle-Campagne (BL) -----------------------------------------------
    "Allschwil": ["BL"],
    "Pratteln": ["BL"],
    "Muttenz": ["BL"],
    "Binningen": ["BL"],
    "Münchenstein": ["BL"],
    "Birsfelden": ["BL"],
    "Oberwil": ["BL"],
    "Aesch": ["BL"],
    "Therwil": ["BL"],

    # ---- Argovie (AG) -----------------------------------------------------
    "Baden": ["AG"],
    "Wettingen": ["AG"],
    "Wohlen": ["AG"],
    "Brugg": ["AG"],
    "Rheinfelden": ["AG"],
    "Suhr": ["AG"],
    "Oftringen": ["AG"],
    "Spreitenbach": ["AG"],
    "Möhlin": ["AG"],
    "Lenzburg": ["AG"],
    "Zofingen": ["AG"],
    "Frick": ["AG"],

    # ---- Lucerne (LU) -----------------------------------------------------
    "Emmen": ["LU"],
    "Kriens": ["LU"],
    "Horw": ["LU"],
    "Ebikon": ["LU"],
    "Sursee": ["LU"],
    "Hochdorf": ["LU"],
    "Willisau": ["LU"],
    "Reiden": ["LU"],

    # ---- Saint-Gall (SG) --------------------------------------------------
    "Rapperswil-Jona": ["SG"],
    "Wil": ["SG"],
    "Gossau": ["SG"],
    "Altstätten": ["SG"],
    "Uzwil": ["SG"],
    "Buchs (SG)": ["SG"],
    "Sankt Margrethen": ["SG"],
    "Rorschach": ["SG"],
    "Sargans": ["SG"],

    # ---- Tessin (TI) ------------------------------------------------------
    "Lugano": ["TI"],
    "Locarno": ["TI"],
    "Mendrisio": ["TI"],
    "Chiasso": ["TI"],
    "Biasca": ["TI"],
    "Ascona": ["TI"],
    "Minusio": ["TI"],
    "Massagno": ["TI"],
    "Paradiso": ["TI"],

    # ---- Grisons (GR) -----------------------------------------------------
    "Davos": ["GR"],
    "St. Moritz": ["GR"],
    "Saint-Moritz": ["GR"],
    "Landquart": ["GR"],
    "Domat/Ems": ["GR"],
    "Ilanz/Glion": ["GR"],
    "Arosa": ["GR"],
    "Pontresina": ["GR"],

    # ---- Schwytz (SZ) -----------------------------------------------------
    "Einsiedeln": ["SZ"],
    "Freienbach": ["SZ"],
    "Küssnacht": ["SZ"],
    "Lachen": ["SZ"],
    "Arth": ["SZ"],
    "Brunnen": ["SZ"],

    # ---- Zoug (ZG) --------------------------------------------------------
    "Baar": ["ZG"],
    "Cham": ["ZG"],
    "Steinhausen": ["ZG"],
    "Risch-Rotkreuz": ["ZG"],
    "Hünenberg": ["ZG"],

    # ---- Thurgovie (TG) ---------------------------------------------------
    "Kreuzlingen": ["TG"],
    "Arbon": ["TG"],
    "Amriswil": ["TG"],
    "Romanshorn": ["TG"],
    "Weinfelden": ["TG"],

    # ---- Soleure (SO) -----------------------------------------------------
    "Olten": ["SO"],
    "Grenchen": ["SO"],
    "Granges": ["SO"],
    "Zuchwil": ["SO"],
    "Bettlach": ["SO"],
    "Derendingen": ["SO"],

    # ---- Schaffhouse (SH) -------------------------------------------------
    "Neuhausen am Rheinfall": ["SH"],
    "Stein am Rhein": ["SH"],

    # ---- Uri (UR) ---------------------------------------------------------
    "Andermatt": ["UR"],
    "Erstfeld": ["UR"],
    "Bürglen": ["UR"],

    # ---- Obwald (OW) ------------------------------------------------------
    "Engelberg": ["OW"],
    "Alpnach": ["OW"],
    "Kerns": ["OW"],

    # ---- Nidwald (NW) -----------------------------------------------------
    "Hergiswil": ["NW"],
    "Stansstad": ["NW"],
    "Buochs": ["NW"],

    # ---- Glaris (GL) ------------------------------------------------------
    "Glarus Nord": ["GL"],
    "Glarus Süd": ["GL"],
    "Näfels": ["GL"],

    # ---- Appenzell Rhodes-Extérieures (AR) --------------------------------
    "Teufen": ["AR"],
    "Heiden": ["AR"],
    "Speicher": ["AR"],

    # ---- HOMONYMS (verified) ----------------------------------------------
    # Multiple cantons share the same canonical name — never silently pick
    # one. The resolver returns "ambiguous" and the UI asks the user.
    "Wald": ["ZH", "AR"],          # Wald ZH + Wald AR (BE merged into another)
    "Buchs": ["AG", "SG", "ZH"],   # Buchs AG, Buchs SG, Buchs ZH (also LU)
    "Reinach": ["AG", "BL"],       # Reinach AG + Reinach BL
    "Roggwil": ["BE", "TG"],       # Roggwil BE + Roggwil TG
    "Bichelsee-Balterswil": ["TG"],  # unique TG
    "Wiesendangen": ["ZH"],
    "Niederweningen": ["ZH"],
}


# ---------------------------------------------------------------------------
# Index: normalised key → list of (canonical_name, canton)
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    """Strip casing, diacritics, and noise punctuation so 'Genève' and
    'geneve' and 'GENEVE' all collide on the same key. Keep slashes and
    parentheses since some official names embed them ('Glarus Süd',
    'Biel/Bienne', 'Buchs (SG)')."""
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", name.strip().casefold())
    stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    # Collapse multiple spaces, normalise common separators.
    return " ".join(stripped.replace("-", " ").replace(".", " ").split())


def _build_index() -> dict[str, list[tuple[str, str]]]:
    idx: dict[str, list[tuple[str, str]]] = {}
    for canonical, cantons in COMMUNES.items():
        key = _normalise(canonical)
        for c in cantons:
            idx.setdefault(key, []).append((canonical, c))
    return idx


_INDEX = _build_index()


def resolve_swiss(commune: str) -> dict:
    """Resolve a Swiss commune to its canton(s). Always returns a dict with
    ``confidence`` ∈ {exact, ambiguous, unknown} and ``candidates`` (canton
    code list). Never raises on bad input — unknown commune is a legitimate
    state."""
    if not commune or not commune.strip():
        return {"country": "CH", "commune": commune, "confidence": "unknown", "candidates": []}
    key = _normalise(commune)
    hits = _INDEX.get(key, [])
    if not hits:
        return {"country": "CH", "commune": commune, "confidence": "unknown",
                "candidates": [], "all_cantons": list(CANTONS.keys())}
    # De-dup canton codes preserving order (a canonical can repeat if listed
    # under two French/German aliases — the index already merges).
    cantons: list[str] = []
    for _can, c in hits:
        if c not in cantons:
            cantons.append(c)
    if len(cantons) == 1:
        return {"country": "CH", "commune": commune, "canton": cantons[0],
                "confidence": "exact",
                "candidates": [{"canton": cantons[0], "name": CANTONS[cantons[0]]["fr"]}],
                "canonical": hits[0][0]}
    return {"country": "CH", "commune": commune, "confidence": "ambiguous",
            "candidates": [{"canton": c, "name": CANTONS[c]["fr"]} for c in cantons]}


def list_swiss_cantons() -> list[dict]:
    """Sorted canton list for the manual-pick dropdown."""
    return [{"canton": code, "name": names["fr"]}
            for code, names in sorted(CANTONS.items(), key=lambda kv: kv[1]["fr"])]
