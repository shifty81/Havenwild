#!/usr/bin/env python3
"""Validate W41A Asset Truth normalization without mutating project sources."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
SCANNER = ROOT / "tools/automation/assets/Build-PublishedWorldAssetInventoryV1.py"
CONTRACT = ROOT / "content/assets/intake/published_world_asset_truth_contract_v1.json"

VALID_STATUSES = {
    "CERTIFIED",
    "CANDIDATE",
    "PROVISIONAL",
    "PLACEHOLDER",
    "MISSING",
    "LEGACY_ALIAS",
    "REJECTED",
}


def req(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def load_scanner():
    spec = importlib.util.spec_from_file_location("havenwild_w41a_asset_truth", SCANNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load W41A scanner")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    req(SCANNER.is_file(), "W41A scanner missing")
    req(CONTRACT.is_file(), "W41A source contract missing")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    req(contract.get("schema") == "havenwild.published_world_asset_truth_contract.v1", "W41A contract schema mismatch")

    scanner = load_scanner()
    report = scanner.build(ROOT)

    req(report.get("schema") == "havenwild.world_asset_inventory.v1", "W41A inventory schema mismatch")
    req(report.get("milestone") == "Pass167Z109W41A", "W41A milestone marker mismatch")
    assets = report.get("assets")
    req(isinstance(assets, list) and assets, "W41A inventory is empty")

    statuses = {item.get("status") for item in assets}
    req(statuses <= VALID_STATUSES, f"W41A contains invalid statuses: {sorted(statuses - VALID_STATUSES)}")

    authority = report["authorityState"]
    req(authority["canonicalPlaceables"]["count"] > 0, "canonical placeable catalog not discovered")
    req(authority["generatedLpcObjects"]["count"] > 0, "generated LPC object manifest not discovered")
    req(authority["legacyWorldgenObjects"]["count"] > 0, "legacy worldgen object lookup not discovered")
    req(authority["authoredScenes"]["distinctAssetIds"] > 0, "authored scene asset IDs not discovered")

    rust = report["rustAuthorityState"]
    req(rust["canonicalObjectKindCatalog"].endswith("tile_object_catalog.rs"), "scanner is not using the active ObjectKind catalog")
    req(rust["objectKindCount"] == 26, f"expected 26 active ObjectKinds, found {rust['objectKindCount']}")
    req(not rust["unexpectedExposureIssues"], "unexpected ObjectKind palette/runtime exposure drift exists")

    exposure = {row["objectKind"]: row for row in rust["objectKindExposure"]}
    req(exposure["well"]["policyState"] == "REJECTED", "Well quarantine is not explicit")
    req(exposure["well"]["runtimeBinding"]["binding"] == "none", "Well must remain unbound until real well art is certified")
    req(exposure["greenhouse_marker"]["policyState"] == "PLACEHOLDER", "Greenhouse marker placeholder state is not explicit")
    req(exposure["cave_entrance"]["runtimeBinding"]["binding"] == "none", "Cave entrance must remain outside object-atlas binding")

    by_id = {item["id"]: item for item in assets}
    for asset_id in ("stairs_up", "bench", "signboard", "well_pump"):
        req(by_id.get(asset_id, {}).get("status") == "REJECTED", f"{asset_id} semantic substitution is not rejected")
    req(by_id.get("construction_tape", {}).get("status") == "PLACEHOLDER", "construction_tape is not marked placeholder")

    # Regression numbers are deliberately lower-bound/exact where the current
    # W40 baseline is already known. If content expands, W41 should not fail
    # simply because more assets exist.
    cross = report["crossAuthority"]
    req(cross["canonicalPlaceableIds"] >= 6, "canonical placeable inventory regressed")
    req(cross["generatedLpcIds"] >= 48, "generated LPC object inventory regressed")
    req(cross["legacyWorldgenIds"] >= 78, "legacy worldgen inventory regressed")
    req(cross["sceneIds"] >= 41, "authored scene asset inventory regressed")

    print("PASS W41A world asset normalization + Asset Truth inventory")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL W41A Asset Truth: {exc}")
        raise SystemExit(1)
