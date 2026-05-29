"""OEREB / RDPPF (Canton de Vaud) extract parser.

Robust over the standard Swiss federal OEREB "reduced extract" JSON (VD `Item` envelope).
Works for ANY VD parcel given an EGRID — no credentials. Used by the MVP1 demo.

Returns the *binding public-law layer* a parcel carries:
parcel id, official area, zone designation, noise DS, alignments, applicable laws, plan documents,
and the presence/absence of every federal RDPPF theme.

Schema (verified 2026-05-29 against EGRID CH915772367853):
  Item.RealEstate.{Number, EGRID, MunicipalityName, LandRegistryArea, Type.Text,
                   RestrictionOnLandownership[]{LegendText, Theme.Code, PartInPercent,
                     LegalProvisions[]{Title, OfficialNumber, TextAtWeb}}}
  Item.{ConcernedTheme[], NotConcernedTheme[]}{Code, Text[]{Language, Text}}
Multilingual fields are lists of {Language, Text}; Language may be "fr" or the int 1.
"""
import json
import re
import ssl
import urllib.request

VD_OEREB = "https://www.rdppf.vd.ch/ws/RdppfSVC.svc"
_CTX = ssl.create_default_context()
_LAW_RE = re.compile(r"^(BLV|RS)\b", re.I)  # legal acts carry BLV/RS official numbers; plans carry numeric ids


def _text(x):
    """Normalize an OEREB multilingual field to a French (or first) string."""
    if x is None or isinstance(x, str):
        return x
    if isinstance(x, dict):
        return _text(x.get("Text"))
    if isinstance(x, list):
        for e in x:
            if isinstance(e, dict) and str(e.get("Language")).lower() in ("fr", "1"):
                return _text(e.get("Text"))
        return _text(x[0]) if x else None
    return str(x)


def fetch(egrid, lang="fr", timeout=30):
    """Fetch the raw OEREB extract for an EGRID. Returns (json, n_bytes)."""
    url = f"{VD_OEREB}/extract/json/?EGRID={egrid}&LANG={lang}"
    req = urllib.request.Request(url, headers={"User-Agent": "Aedifica/0.1 (pilot)"})
    raw = urllib.request.urlopen(req, timeout=timeout, context=_CTX).read()
    return json.loads(raw), len(raw)


def parse(extract):
    """Parse an OEREB extract dict into Aedifica's constraint record."""
    it = extract.get("Item", extract)
    re_ = it.get("RealEstate", {}) or {}
    restr = re_.get("RestrictionOnLandownership", []) or []

    def legends(code):
        out = []
        for r in restr:
            th = r.get("Theme") or {}
            if (th.get("Code") if isinstance(th, dict) else th) == code:
                lt = _text(r.get("LegendText"))
                if lt and lt not in out:
                    out.append(lt)
        return out

    nutz = legends("ch.Nutzungsplanung")
    zone = next((z for z in nutz if re.search(r"zone|LAT", z, re.I) and "périm" not in z.lower()),
                (nutz[0] if nutz else None))

    laws, plans = {}, {}
    for r in restr:
        for p in (r.get("LegalProvisions") or []):
            if not isinstance(p, dict):
                continue
            title, num, url = _text(p.get("Title")), _text(p.get("OfficialNumber")), _text(p.get("TextAtWeb"))
            if not title:
                continue
            if num and _LAW_RE.match(num.strip()):
                laws[num.strip()] = {"title": title, "number": num.strip(), "url": url}
            else:
                plans.setdefault(title, {"title": title, "number": num, "url": url})

    return {
        "parcel": re_.get("Number"),
        "egrid": re_.get("EGRID"),
        "commune": _text(re_.get("MunicipalityName")),
        "area_m2": re_.get("LandRegistryArea"),
        "type": _text((re_.get("Type") or {}).get("Text") if isinstance(re_.get("Type"), dict) else None),
        "zone": zone,
        "zone_all": nutz,
        "noise_ds": (legends("ch.Laermempfindlichkeitsstufen") or [None])[0],
        "alignments": legends("ch.VD.BaulinienCantonalstrassen"),
        "concerned_themes": [t for t in (_text(x.get("Text")) for x in it.get("ConcernedTheme", [])) if t],
        "not_concerned": [t for t in (_text(x.get("Text")) for x in it.get("NotConcernedTheme", [])) if t],
        "laws": list(laws.values()),
        "plans": list(plans.values()),
    }


def get(egrid, lang="fr", timeout=30):
    """Fetch + parse in one call; adds _bytes and _source."""
    extract, n = fetch(egrid, lang, timeout)
    out = parse(extract)
    out["_bytes"], out["_source"] = n, "VD OEREB extract (live)"
    return out


if __name__ == "__main__":  # quick check: python pilot/oereb.py [EGRID]
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    o = get(sys.argv[1] if len(sys.argv) > 1 else "CH915772367853")
    print(json.dumps({k: v for k, v in o.items() if not k.startswith("_")}, ensure_ascii=False, indent=2))
