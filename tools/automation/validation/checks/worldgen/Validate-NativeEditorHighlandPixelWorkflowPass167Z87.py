#!/usr/bin/env python3
from __future__ import annotations

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


def validate_build_repair() -> None:
    require(
        "crates/haven_world/src/mainland_features/alderreach_layout.rs",
        ["(49..=256).contains(&stone_count)"],
    )


def validate_highland_authority() -> None:
    authority = load("content/worldgen/alderreach_mountain_authority_v0_1.json")
    assert authority["revision"] in {
        "167Z87-global-highland-boundaries-v1",
        "167Z88-oga-structural-cliff-runtime-and-traversal-v2",
        "167Z93-tiered-structural-collision-and-complete-face-assembly-v1",
    }
    assert authority["terminology"]["MountainRock"].startswith("Rock Ground")
    assert authority["currentPass"]["globalHeightSupportAcrossPartitions"] is True
    assert isinstance(authority["currentPass"]["runtimeStructuralCliffArtwork"], bool)
    assert authority["productionMountainRequirements"]["elevationTiers"] >= 4
    require(
        "crates/haven_world/src/highland_generation.rs",
        [
            "promote_global_highland_materials",
            "materialize_highland_shoulders",
            "scene_by_chunk",
            "TileKind::MountainPath",
            "highland_support_crosses_storage_partition_boundaries",
        ],
    )
    require(
        "crates/haven_world/src/island_pcg.rs",
        ["promote_global_highland_materials(", "&chunks"],
    )
    save = read("crates/haven_save/src/lib.rs")
    generation = re.search(
        r"CURRENT_CLIENT_GENERATION_VERSION:\s*u32\s*=\s*(\d+)", save
    )
    assert generation is not None and int(generation.group(1)) >= 16


def validate_asset_tree() -> None:
    require(
        "crates/haven_assets/src/asset_palette.rs",
        [
            "pub enum AssetPaletteTreeGroup",
            "Paths & Roads",
            "Elevation & Cliffs",
            "Trees & Flora",
            "Rocks & Resources",
            "Furniture & Props",
            "category_for_object",
        ],
    )
    require(
        "apps/haven_editor_native/src/app/asset_palette_panel.rs",
        [
            "asset_tree_rows",
            "AssetTreeRow::Group",
            "AssetTreeRow::Category",
            "Browse the folder tree by semantic role",
            "const ASSET_PAGE_SIZE: usize = 4;",
        ],
    )


def validate_pixel_workflow() -> None:
    queue = load("content/editor/terrain_shape_repair_queue_v0_1.json")
    assert queue["revision"] in {
        "167Z87-native-editor-highland-and-pixel-workflow-v1",
        "167Z88-structural-cliff-runtime-and-pixel-workflow-v2",
    }
    ids = {item["id"] for item in queue["repairItems"]}
    required = {
        "terrain.rock_ground.native_boundaries",
        "terrain.stone_path.lowland_boundaries",
        "terrain.gravel.native_boundaries",
        "terrain.mud.native_boundaries",
        "terrain.mountain_path.highland_boundaries",
        "terrain.cave_floor.boundaries",
        "terrain.constructed_floor_wall_sets",
        "terrain.elizawy_structural_cliffs",
    }
    assert required <= ids
    assert queue["authority"]["rawThirdPartySourcesAreReadOnly"] is True
    assert queue["authority"]["crossStylePixelMixingForbidden"] is True
    require(
        "docs/roadmaps/TERRAIN_AUTOTILE_PIXEL_STUDIO_WORKFLOW_PASS167Z87.md",
        [
            "16-corner tuple template",
            "47-tile blob template",
            "structural cliff recipe",
            "Cross-partition seam preview",
            "Publish atomically",
        ],
    )


def main() -> int:
    quarantine = ROOT / "content/build/runtime_asset_integrity_cliff_quarantine_v167z96.json"
    if quarantine.is_file():
        contract = json.loads(quarantine.read_text(encoding="utf-8"))
        assert contract["pass"] == "167Z96"
        assert contract["runtimePolicy"]["proceduralCliffDrawing"] is False
        assert contract["runtimePolicy"]["proceduralCliffCollision"] == "fail_open"
        print("Historical cliff validator superseded by Pass167Z96 source-bounds quarantine")
        return 0
    validate_build_repair()
    validate_highland_authority()
    validate_asset_tree()
    validate_pixel_workflow()
    print("Pass167Z87 native editor, highland, and Pixel Studio workflow validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
