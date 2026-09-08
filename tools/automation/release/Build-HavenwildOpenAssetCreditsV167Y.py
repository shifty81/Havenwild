#!/usr/bin/env python3
"""Build Havenwild's broad and exact open-asset credit bundle."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / "content/assets/lpc/universal_lpc_commercial_catalog_v0_1.json.gz"
USAGE = ROOT / "WORKSPACE/generated/universal_lpc_usage_manifest.json"
USAGE_BUILDER = ROOT / "tools/automation/characters/Build-UniversalLpcUsageManifestV167X.py"
BROAD_BUILDER = ROOT / "tools/automation/characters/Build-UniversalLpcBroadCreditsV167Y.py"
LEGAL_ROOT = ROOT / "content/legal"
DEFAULT_OUTPUT = ROOT / "DIST/open-assets/credits"


def load_catalog() -> dict:
    with gzip.open(CATALOG, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--usage-manifest", type=Path, default=USAGE)
    parser.add_argument("--skip-usage-refresh", action="store_true")
    args = parser.parse_args()

    subprocess.run([sys.executable, str(BROAD_BUILDER)], check=True)
    if not args.skip_usage_refresh:
        authority = ROOT / "WORKSPACE/generated/universal_lpc_character_authority_v167w.json"
        if authority.is_file():
            subprocess.run(
                [
                    sys.executable,
                    str(USAGE_BUILDER),
                    "--authority",
                    str(authority),
                    "--output",
                    str(args.usage_manifest),
                ],
                check=True,
            )

    catalog = load_catalog()
    by_source = {record["source"]: record for record in catalog.get("records", [])}
    usage = {"sources": [], "generatedComposites": []}
    if args.usage_manifest.is_file():
        usage = json.loads(args.usage_manifest.read_text(encoding="utf-8"))

    exact_rows = []
    exact_records = []
    for usage_item in usage.get("sources", []):
        source = usage_item.get("source")
        record = by_source.get(source)
        if record is None:
            raise SystemExit(f"Usage manifest references unknown Universal LPC source: {source}")
        selected_license = record.get("selectedLicense") or record.get("selected_license")
        item = {
            "source": source,
            "authors": record.get("authors", []),
            "selectedLicense": selected_license,
            "sourceUrls": record.get("urls", []),
            "modified": bool(usage_item.get("modified", False) or usage_item.get("overridePath")),
            "modificationNote": usage_item.get("modificationNote", ""),
            "overridePath": usage_item.get("overridePath"),
        }
        exact_records.append(item)
        exact_rows.append(
            {
                "source": source,
                "authors": "; ".join(item["authors"]),
                "selected_license": selected_license,
                "source_urls": "; ".join(item["sourceUrls"]),
                "modified": str(item["modified"]).lower(),
                "modification_note": item["modificationNote"],
            }
        )

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        LEGAL_ROOT / "HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt",
        output / "HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt",
    )
    shutil.copy2(
        LEGAL_ROOT / "open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.txt",
        output / "LPC_MASTER_CONTRIBUTORS.txt",
    )
    shutil.copy2(
        LEGAL_ROOT / "open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv",
        output / "LPC_MASTER_CONTRIBUTORS.csv",
    )
    shutil.copy2(
        LEGAL_ROOT / "open_assets/UNIVERSAL_LPC_MASTER_CATALOG_SUMMARY.json",
        output / "LPC_MASTER_CATALOG_SUMMARY.json",
    )
    notice = ROOT / "content/assets/lpc/licenses/CC-BY-SA-3.0-NOTICE.txt"
    if notice.is_file():
        shutil.copy2(notice, output / notice.name)

    payload = {
        "schema": "havenwild.open_asset_credits.v0_1",
        "generatedBy": "Build-HavenwildOpenAssetCreditsV167Y.py",
        "broadAcknowledgementIncluded": True,
        "exactUsedSourceCount": len(exact_records),
        "records": exact_records,
        "generatedComposites": usage.get("generatedComposites", []),
        "parseErrors": usage.get("parseErrors", []),
    }
    (output / "OPEN_ASSET_CREDITS.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "OPEN_ASSET_CREDITS.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "source",
                "authors",
                "selected_license",
                "source_urls",
                "modified",
                "modification_note",
            ],
        )
        writer.writeheader()
        writer.writerows(exact_rows)

    lines = [
        "HAVENWILD OPEN ASSET CREDITS",
        "",
        "BROAD ACKNOWLEDGMENT",
        "--------------------",
        (LEGAL_ROOT / "HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt").read_text(encoding="utf-8").strip(),
        "",
        "USED IN THIS BUILD",
        "------------------",
    ]
    if exact_records:
        for record in exact_records:
            lines.extend(
                [
                    str(record["source"]),
                    f"  Authors: {'; '.join(record['authors'])}",
                    f"  License: {record['selectedLicense']}",
                    f"  Source: {'; '.join(record['sourceUrls'])}",
                    f"  Modified: {record['modified']}",
                    f"  Changes: {record['modificationNote'] or 'None recorded'}",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "No Universal LPC ShareAlike sources were detected in the current usage manifest.",
                "The broad contributor acknowledgment remains included.",
                "",
            ]
        )
    lines.extend(
        [
            "APPROVED / AVAILABLE TO DEVELOPMENT",
            "-----------------------------------",
            "See LPC_MASTER_CONTRIBUTORS.txt and LPC_MASTER_CONTRIBUTORS.csv.",
            "These broader files acknowledge approved contributors whether or not their",
            "work appears in this specific build.",
        ]
    )
    (output / "OPEN_ASSET_CREDITS.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(
        f"Wrote Havenwild open-asset credits with {len(exact_records):,} exact used "
        f"source record(s) plus the broad master acknowledgment to {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
