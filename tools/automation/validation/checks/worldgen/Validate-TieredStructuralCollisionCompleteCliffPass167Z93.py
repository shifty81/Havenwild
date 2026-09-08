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

def main() -> int:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        assert contract["pass"] == "167Z96"
        assert contract["runtimePolicy"]["proceduralCliffDrawing"] is False
        assert contract["runtimePolicy"]["proceduralCliffCollision"] == "fail_open"
        print("Historical cliff validator superseded by Pass167Z96 source-bounds quarantine")
        return 0
    bridge = read("crates/haven_world/src/terrain_cliff_bridge.rs")
    for token in [
        "STRUCTURAL_ELEVATION_TIER_HEIGHT_V2: u8 = 32",
        "tavern_map_to_structural_surface_cells_v2",
        "tavern_map_to_surface_cells_v1(map)",
        "raw_height_noise_inside_one_tier_does_not_block_grass",
        "ordinary_coastline_is_not_promoted_to_a_structural_cliff",
    ]:
        assert token in bridge, token
    assert "let mut cells = tavern_map_to_structural_surface_cells_v2(map);" not in bridge.split("pub fn tavern_map_to_structural_surface_cells_v2",1)[1].split("}",1)[0]

    require("crates/haven_world/src/full_world_structural_bake.rs", [
        "tavern_map_to_structural_surface_cells_v2",
        "left.heights.fill(112)",
        "right.heights.fill(48)",
    ])
    draw = read("crates/haven_game/src/runtime_structural_cliff_draw.rs")
    for token in [
        "draw_south_face_module",
        "draw_cliff_row_pair",
        "south_face_module_anchors",
        "(6 + column_offset) as f32 * 32.0",
        "authored_south_face_modules_never_emit_single_cell_fragments",
    ]:
        assert token in draw, token
    assert "draw_side_lip" not in draw

    require("crates/haven_game/src/runtime_surface_streaming.rs", [
        "provider can render as a complete reviewed assembly",
        "certified_south_cliff_face_pair_at",
        "let certified_visible = match direction",
        "!certified_visible",
    ])

    recipe = load("content/assets/oga_lpc/manifests/oga_lpc_cliff_recipe_catalog_v0_2.json")
    assert recipe["revision"] == "167Z93-tiered-structural-collision-and-complete-face-assembly-v1"
    module = recipe["runtimeTileRoles"]["southFaceModule"]
    assert module["topRowCells"] == [[6,2],[7,2]]
    assert module["minimumRunTiles"] == 2

    authority = load("content/worldgen/alderreach_mountain_authority_v0_1.json")
    assert authority["currentPass"]["rawHeightQuantizedIntoStructuralTiers"] is True
    assert authority["currentPass"]["providerCertifiedCollisionOnly"] is True
    contract = load("content/worldgen/structural_collision_cliff_assembly_authority_v0_1.json")
    assert contract["structuralHeightAuthority"]["tierHeightRawUnits"] == 32
    assert contract["activeVisualProvider"]["moduleWidthTiles"] == 2
    assert contract["collisionPolicy"]["incompleteOrientationsFailOpen"] is True

    require("README.md", ["Pass167Z93", "32-unit tiers", "two-cell-wide authored assembly"])
    require("docs/archive/pass_history/PASS167Z93_TIERED_STRUCTURAL_COLLISION_AND_COMPLETE_CLIFF_ASSEMBLY.md", [
        "Grass traversal repair", "Cliff rendering repair", "Collision visibility authority"
    ])
    print("Pass167Z93 tiered structural collision and complete cliff assembly validated")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
