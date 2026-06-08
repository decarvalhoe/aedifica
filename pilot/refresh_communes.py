"""Refresh the Swiss commune register from the official OFS/BFS source.

Source: AGVCH (Anwendung Gemeindeverzeichnis der Schweiz / Application du
répertoire officiel des communes de Suisse), the public REST API of the
Federal Statistical Office. The snapshot endpoint returns a CSV listing of
every administrative entity (cantons, districts, communes) valid on a given
date.

This script:
  1. Calls the snapshot endpoint for "today" (or a supplied date).
  2. Walks the hierarchy (Level=1 canton → Level=2 district → Level=3
     commune) to assign every active commune to its canton.
  3. Writes a stable JSON snapshot to
     aedifica/jurisdictions/data/ch_communes.json with metadata
     (source URL, snapshot date, fetch timestamp, counts).

The JSON is committed to the repo so a fresh clone works offline. A GitHub
Actions workflow re-runs this script monthly and opens a PR when the OFS
register has moved (commune mergers happen every January 1st).

Usage:
  python pilot/refresh_communes.py                # today's snapshot
  python pilot/refresh_communes.py --date 1-1-2025
  python pilot/refresh_communes.py --out /tmp/x.json  # custom output path
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import sys
import urllib.request
from pathlib import Path

API = "https://www.agvchapp.bfs.admin.ch/api/communes/snapshot"

DEFAULT_OUT = Path(__file__).parent.parent / "aedifica" / "jurisdictions" / "data" / "ch_communes.json"


def fetch_csv(date: str) -> str:
    """date format: D-M-YYYY (single-digit allowed by the API)."""
    url = f"{API}?date={date}"
    req = urllib.request.Request(url, headers={"User-Agent": "aedifica-refresh/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def parse(snapshot_csv: str) -> dict:
    """Walk the hierarchy and produce the canonical map.

    The CSV columns are:
        HistoricalCode, BfsCode, ValidFrom, ValidTo, Level, Parent,
        Name, ShortName, Inscription, Radiation, Rec_Type_fr, Rec_Type_de

    Active row = empty ValidTo. Level 1 = canton, 2 = district, 3 = commune.
    For cantons, ShortName is the 2-letter code (ZH, BE, NE, …). The
    commune → canton walk is: commune.Parent → district.HistoricalCode,
    district.Parent → canton.HistoricalCode.
    """
    reader = csv.DictReader(io.StringIO(snapshot_csv))
    cantons: dict[str, dict] = {}             # hcode → {"code": "ZH", "name": "Zürich"}
    district_to_canton: dict[str, str] = {}   # district hcode → canton hcode
    communes: dict[str, list[dict]] = {}      # canonical name → [{bfs, canton, name}]
    canton_counts: dict[str, int] = {}

    rows = list(reader)
    # First pass: cantons
    for row in rows:
        if row.get("ValidTo"):
            continue  # historic
        if row.get("Level") != "1":
            continue
        hcode = row["HistoricalCode"]
        short = (row.get("ShortName") or "").strip().upper()
        if not short:
            continue
        cantons[hcode] = {"code": short, "name": row["Name"]}

    # Second pass: districts → canton link
    for row in rows:
        if row.get("ValidTo"):
            continue
        if row.get("Level") != "2":
            continue
        hcode = row["HistoricalCode"]
        parent = row.get("Parent")
        if parent in cantons:
            district_to_canton[hcode] = parent

    # Third pass: communes
    for row in rows:
        if row.get("ValidTo"):
            continue
        if row.get("Level") != "3":
            continue
        parent = row.get("Parent")
        canton_hcode = district_to_canton.get(parent)
        # Some cantons (e.g., GL, BS, UR, OW, NW, AI, GE, ZG, SH, SZ) have
        # communes directly under the canton (no district level). The CSV
        # uses the canton's HistoricalCode as parent in that case.
        if canton_hcode is None and parent in cantons:
            canton_hcode = parent
        if canton_hcode is None:
            continue  # orphan row — skip safely (never happens on a clean snapshot)
        canton_code = cantons[canton_hcode]["code"]
        name = (row.get("Name") or "").strip()
        if not name:
            continue
        bfs = int(row["BfsCode"])
        entry = {"bfs": bfs, "name": name, "canton": canton_code}
        communes.setdefault(name, []).append(entry)
        canton_counts[canton_code] = canton_counts.get(canton_code, 0) + 1

    return {
        "cantons": sorted(
            [{"code": c["code"], "name": c["name"], "hcode": int(h)} for h, c in cantons.items()],
            key=lambda x: x["code"],
        ),
        "communes": communes,
        "canton_counts": canton_counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None,
                        help="snapshot date (D-M-YYYY, defaults to today)")
    parser.add_argument("--out", default=str(DEFAULT_OUT), type=Path,
                        help=f"output JSON path (default: {DEFAULT_OUT})")
    args = parser.parse_args()

    today = dt.date.today()
    date = args.date or f"{today.day}-{today.month}-{today.year}"
    print(f"[refresh-communes] fetching OFS/BFS snapshot for {date}…", file=sys.stderr)
    try:
        body = fetch_csv(date)
    except urllib.error.HTTPError as e:
        print(f"[refresh-communes] HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[refresh-communes] fetch failed: {e}", file=sys.stderr)
        return 2

    parsed = parse(body)
    n_communes = sum(len(v) for v in parsed["communes"].values())
    n_homonyms = sum(1 for v in parsed["communes"].values() if len(v) > 1)
    print(f"[refresh-communes] parsed {n_communes} communes across "
          f"{len(parsed['cantons'])} cantons ({n_homonyms} homonyms)", file=sys.stderr)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "$schema": "aedifica.jurisdictions.ch_communes.v1",
        "source": API,
        "snapshot_date": date,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "n_cantons": len(parsed["cantons"]),
        "n_communes": n_communes,
        "n_homonym_names": n_homonyms,
        "canton_counts": parsed["canton_counts"],
        "cantons": parsed["cantons"],
        "communes": parsed["communes"],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[refresh-communes] wrote {out_path} ({out_path.stat().st_size // 1024} KB)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
