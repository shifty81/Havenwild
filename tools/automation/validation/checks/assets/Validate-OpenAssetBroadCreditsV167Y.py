#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def main() -> int:
    policy_path = ROOT / "content/legal/havenwild_open_asset_credit_policy_v0_1.json"
    acknowledgement = ROOT / "content/legal/HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt"
    contributors_csv = ROOT / "content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.csv"
    contributors_text = ROOT / "content/legal/open_assets/UNIVERSAL_LPC_MASTER_CONTRIBUTORS.txt"
    summary_path = ROOT / "content/legal/open_assets/UNIVERSAL_LPC_MASTER_CATALOG_SUMMARY.json"
    runtime = ROOT / "crates/haven_game/src/client_frontend.rs"
    for path in (
        policy_path,
        acknowledgement,
        contributors_csv,
        contributors_text,
        summary_path,
        runtime,
        ROOT / "tools/automation/characters/Build-UniversalLpcBroadCreditsV167Y.py",
        ROOT / "tools/automation/release/Build-HavenwildOpenAssetCreditsV167Y.py",
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("schema") != "havenwild.open_asset_credit_policy.v0_1":
        raise ValueError("unexpected open-asset credit policy schema")
    if policy.get("broadAcknowledgement", {}).get("enabled") is not True:
        raise ValueError("broad open-asset acknowledgment must be enabled")
    if policy.get("exactBuildAttribution", {}).get("required") is not True:
        raise ValueError("exact per-build attribution must remain required")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("approvedSourceRecordCount") != 13818:
        raise ValueError("broad credits must cover all 13,818 approved source records")
    if summary.get("conditionalShareAlikeRecordCount") != 2038:
        raise ValueError("broad credits must cover all 2,038 conditional ShareAlike records")
    if summary.get("uniqueContributorCount", 0) < 50:
        raise ValueError("broad contributor catalog is unexpectedly small")
    if summary.get("broadAcknowledgementReplacesExactAttribution") is not False:
        raise ValueError("broad credits must never replace exact attribution")

    with contributors_csv.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != summary["uniqueContributorCount"]:
        raise ValueError("contributor CSV count does not match summary")
    if any(not row.get("author") or not row.get("selected_licenses") for row in rows):
        raise ValueError("contributor CSV contains incomplete rows")

    runtime_text = runtime.read_text(encoding="utf-8")
    for marker in (
        "FrontendScreen::Credits",
        "Open Asset Credits [C]",
        "HAVENWILD_OPEN_ASSET_ACKNOWLEDGEMENT.txt",
    ):
        if marker not in runtime_text:
            raise ValueError(f"runtime credits screen is missing marker: {marker}")

    print(
        "Open-asset broad credits validated: "
        f"{summary['uniqueContributorCount']} contributors, "
        f"{summary['approvedSourceRecordCount']} approved records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
