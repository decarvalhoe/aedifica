"""Shared Datum HTML styling for pilot renderers.

The canonical visual reference is docs/design-system/aedifica-brand-book.html.
These helpers keep generated reports aligned with the same paper, ink, mono
annotation and hairline system without requiring a frontend build step.
"""

import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _asset_url(relative_path):
    return (ROOT / relative_path).as_uri()


def head(title):
    title = html.escape("" if title is None else str(title))
    space_grotesk = _asset_url("docs/design-system/fonts/SpaceGrotesk-Variable.ttf")
    plex_mono = _asset_url("docs/design-system/fonts/IBMPlexMono-Regular.ttf")
    return f"""<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    @font-face {{ font-family: "Space Grotesk"; src: url("{space_grotesk}") format("truetype"); font-weight: 300 700; }}
    @font-face {{ font-family: "IBM Plex Mono"; src: url("{plex_mono}") format("truetype"); font-weight: 400; }}
    :root {{
      --paper:#F3F1EC; --sheet:#FFFFFF; --ink:#16171A; --accent:#C0392B;
      --mut:#87867D; --line:rgba(22,23,26,.12); --line-2:rgba(22,23,26,.24);
      --sourced:#1F7A44; --computed:#475569; --assume:#9A6A10; --unknown:#84847A; --conflict:#C1122C;
      --font-ui:"Space Grotesk","Helvetica Neue",sans-serif; --font-mono:"IBM Plex Mono",ui-monospace,monospace;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font-family:var(--font-ui); line-height:1.45; }}
    .page {{ width:min(1120px,calc(100vw - 40px)); margin:24px auto; background:var(--sheet); border:1px solid var(--ink); padding:34px; }}
    .top {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:24px; padding-bottom:18px; border-bottom:1px solid var(--ink); color:var(--mut); font-family:var(--font-mono); font-size:10px; letter-spacing:.16em; text-transform:uppercase; }}
    .top span:nth-child(2) {{ text-align:center; }} .top span:nth-child(3) {{ text-align:right; }}
    h1 {{ margin:26px 0 10px; font-size:42px; line-height:1.03; letter-spacing:-.025em; font-weight:300; }}
    h2 {{ margin:0 0 12px; color:var(--mut); font-family:var(--font-mono); font-size:11px; letter-spacing:.16em; text-transform:uppercase; font-weight:400; }}
    h3 {{ margin:16px 0 8px; font-size:15px; font-weight:500; }}
    p {{ max-width:76ch; }}
    section {{ margin-top:22px; padding-top:18px; border-top:1px solid var(--ink); }}
    ul {{ margin:0; padding-left:18px; }}
    li {{ margin:7px 0; }}
    table {{ width:100%; border-collapse:collapse; border:1px solid var(--line-2); }}
    th, td {{ padding:10px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
    th {{ color:var(--mut); font-family:var(--font-mono); font-size:10px; letter-spacing:.12em; text-transform:uppercase; font-weight:400; }}
    small, footer {{ color:var(--mut); font-family:var(--font-mono); font-size:10px; letter-spacing:.06em; }}
    footer {{ margin-top:28px; padding-top:14px; border-top:1px solid var(--ink); white-space:pre-line; text-transform:uppercase; }}
    .chip, .state {{ display:inline-flex; align-items:center; gap:6px; border:1px solid currentColor; padding:3px 7px; font-family:var(--font-mono); font-size:10px; letter-spacing:.1em; text-transform:uppercase; line-height:1; }}
    .chip::before, .state::before {{ content:""; width:7px; height:7px; background:currentColor; }}
    .sourced,.present,.ready,.low {{ color:var(--sourced); }} .computed,.conditional,.medium {{ color:var(--computed); }}
    .assumption,.missing,.blocked,.high {{ color:var(--assume); }} .unknown,.out_of_scope {{ color:var(--unknown); }}
    .conflict,.élevé {{ color:var(--conflict); }} .modéré {{ color:var(--assume); }} .faible {{ color:var(--sourced); }}
    .claim {{ list-style:none; border:1px solid var(--line-2); padding:10px 12px; margin:8px 0; }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
    @media (max-width:760px) {{ .page {{ width:100%; margin:0; border:0; padding:22px; }} .top,.grid {{ grid-template-columns:1fr; }} .top span {{ text-align:left !important; }} h1 {{ font-size:32px; }} }}
    @media print {{ body {{ background:#fff; }} .page {{ width:auto; margin:0; border:0; padding:0; }} @page {{ size:A4; margin:12mm; }} }}
  </style>
</head>"""


def shell(title, label, body, footer="Préparation sourcée par AEDIFICA. Pas une autorité."):
    label = html.escape("" if label is None else str(label))
    return f"""<!doctype html>
<html lang="fr">
{head(title)}
<body>
  <main class="page">
    <div class="top"><span>AEDIFICA</span><span>{label}</span><span>DATUM +13.50</span></div>
    {body}
    <footer>{footer}</footer>
  </main>
</body>
</html>
"""
