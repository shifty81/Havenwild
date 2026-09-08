#!/usr/bin/env python3
from __future__ import annotations

import json
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


def validate_test_contract_repair() -> None:
    plaza = read("crates/haven_world/src/mainland_features/tests.rs")
    assert "stone_cells.len() <= 121" in plaza
    assert "TileKind::StonePath | TileKind::Road" in plaza
    assert "assert_eq!(stone_cells.len(), 121)" not in plaza
    require(
        "crates/haven_world/src/island_pcg.rs",
        ["TileKind::MountainRock", "TileKind::MountainPath"],
    )


def validate_oga_provider() -> None:
    pack = load("content/asset_packs/oga_lpc_cliffs/pack.json")
    assert pack["production_enabled"] is True
    assert pack["license"]["license_id"] == "CC-BY-SA-3.0"
    assert pack["license"]["production_approved"] is True
    sources = {source["id"]: source for source in pack["sources"]}
    assert sources["cliff_grass_sheet"]["kind"] == "raw_sheet"
    recipe = load(
        "content/assets/oga_lpc/manifests/oga_lpc_cliff_recipe_catalog_v0_2.json"
    )
    assert recipe["revision"] in {
        "167Z88-structural-cliff-provider-v1",
        "167Z93-tiered-structural-collision-and-complete-face-assembly-v1",
    }
    assert recipe["sourceSha256"] == (
        "1a0c25904aaacf373c54311eecca9933a9b122e4c3cb2e4cfe8e19ab06feb82a"
    )
    runtime_roles = recipe["runtimeTileRoles"]
    if "southFaceModule" in runtime_roles:
        assert runtime_roles["southFaceModule"]["topRowCells"] == [[6, 2], [7, 2]]
        assert runtime_roles["southFaceModule"]["verticalRepeatRowCells"] == [[6, 3], [7, 3]]
        assert runtime_roles["southFaceModule"]["exposedBaseRowCells"] == [[6, 4], [7, 4]]
    else:
        assert runtime_roles["southFaceTop"] == [6, 2]
    rows = {row["id"]: row for row in recipe["recipes"]}
    assert rows["oga_lpc.cliff.ramp_left"]["sourceRect"] == [96, 160, 96, 128]
    assert rows["oga_lpc.cliff.ramp_right"]["sourceRect"] == [192, 160, 96, 128]
    assert rows["oga_lpc.cliff.ladder"]["sourceRect"] == [288, 128, 32, 96]


def validate_runtime_structures() -> None:
    require(
        "crates/haven_world/src/full_world_structural_bake.rs",
        [
            "PartitionedSurfaceStructuralBakeV2",
            "bake_partitioned_surface_structural_terrain_v2",
            "partitioned_bake_derives_structure_across_signed_chunk_boundary",
        ],
    )
    require(
        "crates/haven_game/src/runtime_surface_streaming.rs",
        [
            "rebuild_active_surface_structures",
            "structural_surface_move_allowed",
            "stamp.stamp_key",
            '"oga_lpc.cliff.ramp_left"',
            '"oga_lpc.cliff.ladder"',
        ],
    )
    require(
        "crates/haven_game/src/runtime_structural_cliff_draw.rs",
        [
            "draw_structural_cliffs",
            "draw_south_face_module",
            "draw_cliff_row_pair",
            "south_face_module_anchors",
            "(6 + column_offset) as f32 * 32.0",
        ],
    )
    require(
        "crates/haven_game/src/runtime_scene_navigation.rs",
        ["structural_surface_move_allowed(from_x_tile", "structural_surface_move_allowed(from_y_tile"],
    )
    require("crates/haven_game/src/runtime_draw.rs", ["self.draw_structural_cliffs();"])
    require(
        "crates/haven_game/src/client_entry.rs",
        ["game.rebuild_active_surface_structures();"],
    )


def validate_editor_and_workflow() -> None:
    require(
        "crates/haven_assets/src/asset_palette.rs",
        ["category_for_stamp", 'category.starts_with("terrain/cliffs")'],
    )
    workflow = load("content/editor/pixel_studio_cliff_workflow_v0_2.json")
    assert workflow["sourcePolicy"]["thirdPartySheetsReadOnly"] is True
    assert workflow["sourcePolicy"]["quadrantSynthesisForbidden"] is True
    fixtures = set(workflow["requiredPreviewFixtures"])
    assert {
        "left_ramp_and_right_ramp",
        "ladder_north_south_crossing",
        "cross_partition_seam",
    } <= fixtures
    authority = load("content/worldgen/alderreach_mountain_authority_v0_1.json")
    assert authority["revision"] in {
        "167Z88-oga-structural-cliff-runtime-and-traversal-v2",
        "167Z93-tiered-structural-collision-and-complete-face-assembly-v1",
    }
    assert authority["currentPass"]["runtimeStructuralCliffArtwork"] is True
    assert authority["currentPass"]["automaticRampAndLadderPlacement"] is False


def main() -> int:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        assert contract["pass"] == "167Z96"
        assert contract["runtimePolicy"]["proceduralCliffDrawing"] is False
        assert contract["runtimePolicy"]["proceduralCliffCollision"] == "fail_open"
        print("Historical cliff validator superseded by Pass167Z96 source-bounds quarantine")
        return 0
    validate_test_contract_repair()
    validate_oga_provider()
    validate_runtime_structures()
    validate_editor_and_workflow()
    print("Pass167Z88 structural cliffs, traversal, and test repair validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
