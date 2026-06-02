# Demo cockpit — presentation guide

> An interactive, Datum-branded local web app to demo Aedifica to a partner
> architect. Live Swiss address lookup with a frozen Lausanne/Pully fallback.
> Implemented in `pilot/demo_cockpit.py`. Stdlib-only, local, no auth.

## Launch (interactive, recommended)

```bash
python pilot/demo_cockpit.py            # -> http://127.0.0.1:8090
```

Open the URL. You get one cockpit with five tabs and a search bar.

## Single-file fallback (no install, no server)

```bash
python pilot/demo_cockpit.py --export aedifica-cockpit.html          # frozen Lausanne
python pilot/demo_cockpit.py --export demo.html --query "Pully" --live
```

Double-click the produced `.html` (works offline; the search buttons need the
server, but every panel is pre-rendered).

## Suggested demo script (5 minutes)

1. **The hook** — type a real Vaud address → **Analyser**. In seconds: zone,
   degré de sensibilité au bruit, alignements — each a green `sourced` chip with
   its source. *"No BIM model. Just the address. Every number traceable."*
   The badge shows **● LIVE** when it hit the registries.
2. **Enveloppe** tab — buildable envelope. Point out the **`unknown`** chips:
   *"When the numeric index isn't in open data, we say so — we never invent a
   number. That's your liability protection."*
3. **Opposition** tab — heritage / noise / neighbour / shadow / visibility
   signals, overall risk. *"Indicative, not a prediction — and it tells you what
   evidence is missing."*
4. **Permis** tab — ACTIS-CAMAC completeness: *"Dossier NOT ready — 3 required
   blockers"*, with the non-authority disclaimers. *"It prepares the dossier; the
   authority decides."*
5. **Modèle Archicad** tab — the agent loop: missing metadata detected →
   mutation **blocked without approval**, **allowed only with a ledger-tracked
   execution approval**. *"An AI that can act in your software — but never
   without your logged consent."*

## Talking points (for the architect)

- Anchored on **binding Swiss registries** (swisstopo, RDPPF/OEREB), 3 levels
  (federal / cantonal / communal) + parcel — the federal complexity is the moat.
- **Trust contract**: `sourced` / `computed` / `unknown`, never an authority.
- **Generalizable**: neutral engine + jurisdiction packs; Archicad is the first
  bridge, not the product identity.

## Network note

Live lookup uses the free public Swiss APIs. If the venue Wi-Fi is flaky, the
cockpit falls back to the frozen Lausanne/Pully fixtures automatically and shows
a `fixture` badge — the demo never breaks. For a guaranteed-offline run, present
the exported single file.
