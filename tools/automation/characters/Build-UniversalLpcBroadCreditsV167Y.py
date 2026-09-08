#!/usr/bin/env python3
"""Build Havenwild's broad Universal LPC contributor acknowledgment.

This catalog intentionally credits every commercially approved Universal LPC source
record available to development. It does not replace the exact used-in-build ledger.
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz"
SHAREALIKE = ROOT / "content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz"
OUT_DIR = ROOT / "content/legal/open_assets"
OUT_TEXT = OUT_DIR / "UNIVERSAL_LPC_MASTER_CONTRIBUTORS.txt"
OUT_CSV = OUT_DIR / "UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv"
OUT_SUMMARY = OUT_DIR / "UNIVERSAL_LPC_MASTER_CATALOG_SUMMARY.json"
ACKNOWLEDGEMENT = ROOT / "content/legal/HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt"


def load_gzip_json(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def selected_license(record: dict) -> str:
    return str(record.get("selectedLicense") or record.get("selected_license") or "UNKNOWN")


def main() -> int:
    if not CATALOG.is_file() or not SHAREALIKE.is_file():
        raise SystemExit("Universal LPC commercial catalogs are missing")

    catalog = load_gzip_json(CATALOG)
    sharealike_catalog = load_gzip_json(SHAREALIKE)
    records = catalog.get("records", [])
    sharealike_sources = {record["source"] for record in sharealike_catalog.get("records", [])}

    contributors: dict[str, dict[str, set[str] | int]] = defaultdict(
        lambda: {"licenses": set(), "urls": set(), "categories": set(), "source_count": 0}
    )
    license_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    all_urls: set[str] = set()

    for record in records:
        license_name = selected_license(record)
        license_counts[license_name] += 1
        category = str(record.get("category", "unknown"))
        category_counts[category] += 1
        urls = {str(value).strip() for value in record.get("urls", []) if str(value).strip()}
        all_urls.update(urls)
        for author in record.get("authors", []):
            name = str(author).strip()
            if not name:
                continue
            entry = contributors[name]
            entry["source_count"] = int(entry["source_count"]) + 1
            entry["licenses"].add(license_name)  # type: ignore[union-attr]
            entry["urls"].update(urls)  # type: ignore[union-attr]
            entry["categories"].add(category)  # type: ignore[union-attr]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for author in sorted(contributors, key=str.casefold):
        entry = contributors[author]
        rows.append(
            {
                "author": author,
                "approved_source_count": int(entry["source_count"]),
                "selected_licenses": "; ".join(sorted(entry["licenses"])),
                "categories": "; ".join(sorted(entry["categories"])),
                "source_urls": "; ".join(sorted(entry["urls"])),
            }
        )

    with OUT_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "author",
                "approved_source_count",
                "selected_licenses",
                "categories",
                "source_urls",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "HAVENWILD UNIVERSAL LPC MASTER CONTRIBUTOR ACKNOWLEDGMENT",
        "",
        "This master catalog acknowledges every contributor attached to the",
        "commercially approved Universal LPC source records available to Havenwild",
        "development. It is intentionally broader than the exact used-in-build credits.",
        "",
        f"Approved source records: {len(records):,}",
        f"Conditional CC-BY-SA records: {len(sharealike_sources):,}",
        f"Unique acknowledged contributors: {len(rows):,}",
        "",
        "The exact source file, title/path, author list, source URLs, selected license,",
        "and modification state for shipped assets are generated separately for each",
        "release. This master list does not weaken or replace those exact records.",
        "",
        "CONTRIBUTORS",
        "------------",
    ]
    for row in rows:
        lines.append(
            f"{row['author']} — {row['approved_source_count']} approved source record(s) — "
            f"{row['selected_licenses']}"
        )
    lines.extend(
        [
            "",
            "SOURCE CATALOGS",
            "---------------",
            "content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz",
            "content/assets/lpc/universal_lpc_sharealike_catalog_v0_1.json.gz",
            "",
            "See UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv for grouped source URLs and",
            "categories. See the per-build OPEN_ASSET_CREDITS files for exact usage.",
        ]
    )
    OUT_TEXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "schema": "havenwild.universal_lpc_master_catalog_summary.v0_1",
        "generatedBy": "Build-UniversalLpcBroadCreditsV167Y.py",
        "sourceCommit": catalog.get("sourceCommit"),
        "approvedSourceRecordCount": len(records),
        "conditionalShareAlikeRecordCount": len(sharealike_sources),
        "uniqueContributorCount": len(rows),
        "uniqueSourceUrlCount": len(all_urls),
        "selectedLicenseCounts": dict(sorted(license_counts.items())),
        "categoryCounts": dict(sorted(category_counts.items())),
        "exactUsageLedgerRequiredForRelease": True,
        "broadAcknowledgementReplacesExactAttribution": False,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    acknowledgement = """HAVENWILD OPEN ASSET CREDITS

Havenwild uses artwork and animation contributed by the Liberated Pixel Cup
(LPC), Universal LPC Spritesheet Character Generator, and selected OpenGameArt
creators.

The project broadly acknowledges every creator in its approved commercial LPC
catalog, including creators whose approved work is available to development but
may not appear in the current build.

Commercial-use assets remain governed by their individual licenses. These may
include CC0, OGA-BY, CC-BY, and CC-BY-SA. ShareAlike artwork and adaptations
remain available under the applicable CC-BY-SA terms.

Every distributed build also includes an exact used-asset ledger containing the
source asset, creators, source locations, selected license, and modification
notes for artwork actually shipped in that build.

Broad acknowledgment is additive. It does not replace exact attribution,
license notices, modification records, or ShareAlike distribution requirements.

Full development acknowledgment:
  content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.txt

Machine-readable contributor catalog:
  content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv

Release-specific exact credits:
  OPEN_ASSET_CREDITS.txt
  OPEN_ASSET_CREDITS.csv
  OPEN_ASSET_CREDITS.json

Press Escape, Enter, or Backspace to return to the title menu.
"""
    ACKNOWLEDGEMENT.write_text(acknowledgement, encoding="utf-8")

    print(
        f"Wrote broad Universal LPC credits for {len(rows):,} contributors "
        f"across {len(records):,} approved source records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
