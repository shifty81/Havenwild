#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def load(path: str):
    return json.loads(read(path))


def require(path: str, tokens: list[str]) -> None:
    text = read(path)
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError(f"{path} missing: {missing}")


def reject(path: str, tokens: list[str]) -> None:
    text = read(path)
    found = [token for token in tokens if token in text]
    if found:
        raise AssertionError(f"{path} contains forbidden token(s): {found}")


def validate_manifest() -> None:
    manifest = load("content/worldgen/scene_rectangle_manifest_v0_8.json")
    standard = manifest["scene_rectangles"]
    assert manifest["scene_count"] == 63
    assert len(standard) == 63
    ids = [entry["scene_id"] for entry in standard]
    assert len(ids) == len(set(ids))
    mainland = [entry for entry in standard if entry["landmass_id"] == 0]
    assert len(mainland) == 40
    assert all(entry["landmass_name"] == "Alderreach" for entry in mainland)
    assert all(entry["tile_size"] == [96, 64] for entry in standard)
    coords = {(entry["grid_x"], entry["grid_y"]) for entry in mainland}
    assert coords == {(x, y) for y in range(5) for x in range(8)}
    authority = manifest["mainland_authority"]
    assert authority["display_name"] == "Alderreach"
    assert authority["legacy_region_id"] == "havenwild_mainland"
    assert authority["new_world_partition_grid"] == [8, 5]
    assert authority["partition_tile_size"] == [96, 64]
    assert authority["continuous_surface_tiles"] == [768, 320]
    assert authority["area_comparison"]["areaMultiplier"] == 2.0

    with (ROOT / "content/worldgen/scene_rectangles_v0_8.csv").open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        rows = list(csv.DictReader(stream))
    standard_rows = [row for row in rows if row["grid_x"] and row["grid_y"]]
    assert len(standard_rows) == 63
    assert all(row["tile_w"] == "96" and row["tile_h"] == "64" for row in standard_rows)


def validate_world_authority() -> None:
    authority = load("content/worldgen/mainland_surface_features_authority_v0_1.json")
    assert authority["schema"] == "havenwild.mainland_surface_features.v0_2"
    assert authority["pass"] == "Pass167Z84"
    assert authority["generationVersion"] == 14
    assert authority["regionalIdentity"]["mainIslandDisplayName"] == "Alderreach"
    assert authority["newWorldScale"]["partitionGrid"] == [8, 5]
    assert authority["newWorldScale"]["partitionTiles"] == [96, 64]
    assert authority["newWorldScale"]["continuousSurfaceTiles"] == [768, 320]
    assert authority["newWorldScale"]["areaMultiplier"] == 2.0
    assert authority["willowmere"]["lotVisualPolicy"].startswith("Reserved lots are metadata")
    assert authority["willowmere"]["civicPlaza"]["maximumTiles"] == 121
    assert "Water Cooler.png" in authority["willowmere"]["quarantinedMisclassification"]
    assert authority["harbor"]["implementedStage"].startswith("dry coastal landfall")
    assert authority["migration"]["doNotResizeOccupiedWorld"] is True

    capital = load("content/worldgen/alderreach_capital_harbor_authority_v0_1.json")
    assert capital["identity"]["mainIsland"] == "Alderreach"
    assert capital["scale"]["newWorldPartitionGrid"] == [8, 5]
    assert capital["scale"]["continuousTileSize"] == [768, 320]
    assert capital["saveNamespace"]["regionId"] == "havenwild_mainland"
    assert capital["harbor"]["roadEndsOnDryLand"] is True


def validate_source() -> None:
    require(
        "crates/haven_core/src/scene_types.rs",
        [
            "CivicLot",
            "MarketLot",
            "ResidentialLot",
            "ArtisanLot",
            "HarborLot",
            "AgriculturalLot",
            '"civic_lot"',
            '"harbor_lot"',
        ],
    )
    require(
        "crates/haven_world/src/mainland_features.rs",
        [
            '"havenwild.mainland_surface_features.v0_2"',
            "city_plot_reservations",
            "harbor_reserved_tiles",
            "clear_legacy_plot_foundation",
            "repair_harbor_road_intrusions",
            "reserve_harbor_district",
            "paint_civic_plaza",
        ],
    )
    require(
        "crates/haven_world/src/mainland_features/tests.rs",
        [
            "city_lots_are_metadata_not_giant_stone_path_rectangles",
            "one_player_road_does_not_suppress_missing_capital_generation",
        ],
    )
    require(
        "crates/haven_world/src/mainland_features/alderreach_layout.rs",
        [
            "find_harbor_landfall",
            "is_coastal_land",
            "reserve_city_plot",
            "ZoneKind::HarborLot",
            "stone_cells * 100 < area * 70",
        ],
    )
    reject(
        "crates/haven_world/src/mainland_features.rs",
        ["surface.place_object(town, ObjectKind::Well)"],
    )
    require(
        "crates/haven_assets/src/asset_registry.rs",
        [
            "ObjectKind::Well => return None",
            "Water Cooler.png",
        ],
    )
    require(
        "crates/haven_world/src/island_pcg.rs",
        [
            'let region = if rectangle.landmass_id == 0',
            '"havenwild_mainland".to_string()',
            'assert_eq!(generated.scenes.len(), 40);',
            'assert_eq!(generated.landmass_name, "Alderreach");',
        ],
    )
    require(
        "crates/haven_game/src/runtime_world_map.rs",
        ['matches!(region, "mainland" | "havenwild_mainland")'],
    )
    save_text = read("crates/haven_save/src/lib.rs")
    generation = re.search(
        r"CURRENT_CLIENT_GENERATION_VERSION:\s*u32\s*=\s*(\d+)", save_text
    )
    assert generation is not None
    assert int(generation.group(1)) >= 14
    require(
        "crates/haven_game/src/runtime_diagnostics.rs",
        ["Alderreach global surface"],
    )


def validate_asset_intake() -> None:
    authority = load("content/assets/intake/havenwild_asset_promotion_closeout_v0_1.json")
    assert authority["pass"] == "Pass167Z84"
    assert [provider["id"] for provider in authority["providers"]] == [
        "elizawy_lpc_revised",
        "universal_lpc_character_generator",
        "curated_open_game_art_lpc",
    ]
    assert authority["providers"][0]["rawFilesExpected"] == 64365
    assert authority["providers"][1]["spritesheetPngFilesExpected"] == 88235
    assert len(authority["priorityLanes"]) == 6
    assert authority["knownQuarantine"][0]["sourceRelativePath"] == "Objects/Furniture/Water Cooler.png"

    matrix = load("WORKSPACE/generated/lpc/promotion/havenwild_asset_promotion_matrix_v167z84.json")
    assert matrix["providers"]["elizawy"]["fileCount"] == 64365
    assert matrix["providers"]["universalLpc"]["counts"]["spritesheetPngFiles"] == 88235
    assert len(matrix["providers"]["elizawy"]["domains"]) == 10
    assert matrix["runtimeEvidence"]["objectAtlas"]["waterCoolerRuntimeBindingAllowed"] is False

    require(
        "tools/automation/assets/Build-HavenwildAssetPromotionCloseoutV167Z84.py",
        [
            "source_mount_state",
            "elizawy_domains",
            "generated_character_counts",
            "oga_entries",
            "Water Cooler.png",
        ],
    )
    require(
        "tools/build/Build.ps1",
        ["asset-sources", "asset-promotion-audit", "Build-AssetPromotionCloseout"],
    )
    require(
        "tools/build/Build.sh",
        ["asset-sources)", "asset-promotion-audit)", "build_asset_promotion_closeout"],
    )
    require(
        "tools/control/ProjectCommandRegistry.ps1",
        ["Sync and audit all LPC sources", "Rebuild asset promotion matrix"],
    )


def main() -> int:
    validate_manifest()
    validate_world_authority()
    validate_source()
    validate_asset_intake()
    print("Pass167Z84 Alderreach scale, capital/harbor repair, and asset intake authority validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
