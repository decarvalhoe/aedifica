#!/usr/bin/env python3
"""Offline smoke test for the pilot — pure logic, no network.

Run:  python pilot/selfcheck.py   (exit 0 = all pass)
Covers: OEREB parser on an inline fixture, envelope math from the ingested rulesets,
zone signal-matching, winter-shadow calc, and the selector composition.
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oereb              # noqa: E402
import selector          # noqa: E402
import opposition_radar as radar  # noqa: E402
import mvp1_demo as demo  # noqa: E402

_n = _fail = 0


def check(name, cond):
    global _n, _fail
    _n += 1
    ok = bool(cond)
    if not ok:
        _fail += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")


def load(*parts):
    with open(os.path.join(HERE, *parts), encoding="utf-8") as f:
        return json.load(f)


print("OEREB parser (inline fixture)")
fixture = {"Item": {
    "ConcernedTheme": [{"Code": "ch.Nutzungsplanung", "Text": [{"Language": 1, "Text": "Plans d'affectation"}]}],
    "NotConcernedTheme": [{"Code": "ch.BelasteteStandorte", "Text": [{"Language": 1, "Text": "Sites pollués"}]}],
    "RealEstate": {
        "Number": "99", "EGRID": "CH000000000000", "MunicipalityName": "TestVille", "LandRegistryArea": "500",
        "Type": {"Text": [{"Language": 1, "Text": "Bien-fonds"}]},
        "RestrictionOnLandownership": [
            {"Theme": {"Code": "ch.Nutzungsplanung"}, "LegendText": [{"Language": 1, "Text": "Zone test 15 LAT"}],
             "PartInPercent": 100, "LegalProvisions": [
                {"Title": "Loi test", "OfficialNumber": [{"Language": 1, "Text": "RS 700"}], "TextAtWeb": [{"Language": 1, "Text": "http://x"}]},
                {"Title": "Plan communal", "OfficialNumber": [{"Language": 1, "Text": "12345"}], "TextAtWeb": [{"Language": 1, "Text": "http://p"}]}]},
            {"Theme": {"Code": "ch.Laermempfindlichkeitsstufen"}, "LegendText": [{"Language": 1, "Text": "Degré de sensibilité II"}], "PartInPercent": 100},
        ]}}}
p = oereb.parse(fixture)
check("zone", p["zone"] == "Zone test 15 LAT")
check("noise DS", p["noise_ds"] == "Degré de sensibilité II")
check("area", p["area_m2"] == "500")
check("commune", p["commune"] == "TestVille")
check("law (RS 700) detected", any(law["number"] == "RS 700" for law in p["laws"]))
check("plan (numeric) not counted as law", all(law["number"] != "12345" for law in p["laws"]))
check("not-concerned label", "Sites pollués" in p["not_concerned"])
check("_text handles int Language & plain str", oereb._text([{"Language": 1, "Text": "x"}]) == "x" and oereb._text("y") == "y")

print("Envelope math (ingested rulesets)")
laus = load("lausanne", "rpga_zones.json")
pully = load("pully", "rpga_zones.json")
check("Lausanne faible densité IUS = 0.5", laus["zones"]["Zone mixte de faible densité"]["ius"] == 0.5)
check("Lausanne utilité publique IUS = 2.0", laus["zones"]["Zone d'utilité publique"]["ius"] == 2.0)
check("Lausanne Centre historique has no index", laus["zones"]["Centre historique"]["ius"] is None)
check("Pully moyenne densité IOS = 0.2", pully["zones"]["Zone d'habitation à moyenne densité"]["ios"] == 0.2)
check("SBP calc 1000 m² × IUS 0.5 = 500", round(1000 * laus["zones"]["Zone mixte de faible densité"]["ius"]) == 500)
check("emprise calc 1673 m² × IOS 0.2 = 335", round(1673 * pully["zones"]["Zone d'habitation à moyenne densité"]["ios"]) == 335)

print("Zone signal-matching (harmonized OEREB label -> communal zone)")
nm, zp, how = demo.match_zone(pully, {"zone": "Zone d'habitation de moyenne densité 15 LAT", "parcel": "x"})
check("Pully moyenne matched (not faible)", nm == "Zone d'habitation à moyenne densité")
check("match flagged keyword", how == "keyword")
nm2, _, _ = demo.match_zone(laus, {"zone": "Zone d'habitation de forte densité 15 LAT", "parcel": "x"})
check("Lausanne forte matched", nm2 == "Zone mixte de forte densité")

print("Shadow + selector")
s = radar.winter_shadow_len(15)
check("winter shadow ~41 m for 15 m", 38 < s < 45)
communes = selector.list_communes()
check("selector discovers Lausanne + Pully", "Lausanne" in communes and "Pully" in communes)
r = selector.route("CH", "VD", "Lausanne")
check("route = 3 active layers", len(r["active"]) == 3)

print("-" * 48)
print(f"{_n - _fail}/{_n} checks passed" + ("" if not _fail else f"  ({_fail} FAILED)"))
sys.exit(1 if _fail else 0)
