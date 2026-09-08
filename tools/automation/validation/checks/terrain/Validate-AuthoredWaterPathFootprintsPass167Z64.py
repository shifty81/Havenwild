#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def load(rel: str) -> dict:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Authored water/path/footprints: missing {rel}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Authored water/path/footprints: missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def fail(message: str) -> None:
    raise SystemExit(f"Authored water/path/footprints: {message}")


def main() -> int:
    direct = text("crates/haven_game/src/terrain_transition_draw.rs")
    terrain_render = text("crates/haven_game/src/terrain_render.rs")
    shoreline = text("crates/haven_world/src/autotile/shoreline_resolver.rs")
    shore_lifecycle = text("crates/haven_world/src/autotile/shore_water_lifecycle.rs")
    shore_tests = text("crates/haven_world/src/autotile/shoreline_regression_tests.rs")
    shoreline_family = shoreline + "\n" + shore_lifecycle + "\n" + shore_tests
    contacts = text("crates/haven_assets/src/authored_terrain_contacts.rs")
    assets = text("crates/haven_assets/src/asset_registry.rs")
    runtime_draw = text("crates/haven_game/src/runtime_draw.rs")
    runtime_editor_draw = text("crates/haven_game/src/runtime_editor_draw.rs")
    runtime_draw_family = runtime_draw + "\n" + runtime_editor_draw
    editor_shell = text("crates/haven_game/src/runtime_editor_shell.rs")
    editor_policy = text("crates/haven_editor/src/scene_edit.rs")
    shared_terrain_policy = text("crates/haven_authoring/src/terrain_policy.rs")
    editor_policy_family = editor_policy + "\n" + shared_terrain_policy
    startup = text("crates/haven_game/src/runtime_startup.rs")
    save_lib = text("crates/haven_save/src/lib.rs")
    editor_state = text("crates/haven_game/src/editor_state.rs")
    f3 = load("content/editor/f3_terrain_style_workspace_v0_1.json")
    object_manifest = load("assets/generated/havenwild_lpc_objects_160x192_v2.json")
    placeables = load("content/asset_packs/havenwild_objects/published_world_assets_v1.json")

    for forbidden in ["DirectLpcQuadrant", "QuadrantSource", "draw_quadrant_source"]:
        if forbidden in direct:
            fail(f"water renderer still synthesizes cropped quadrants: {forbidden}")
    for required in [
        "draw_full_depth_cell",
        "draw_full_depth_inner_cell",
        "mask.depth_corners.count_ones() > 1",
        "mask.depth_edges != 0 && mask.depth_corners != 0",
        "unsupported_depth_masks_are_not_synthesized",
        'outer_col: 0,\n            outer_row: 23',
        'inner: Some((3, 23))',
    ]:
        if required not in direct:
            fail(f"exact authored water-cell contract is missing: {required}")

    if "draw_direct_water_depth_rim" in terrain_render:
        fail("active terrain renderer still layers the superseded ElizaWy depth rim")
    if "draw_tile_transition_overlays" in terrain_render:
        fail("active terrain renderer still exposes a generic compatibility overlay")

    for required in [
        "normalize_authored_depth_topology_region",
        "inner_corner_count <= 1",
        "SUPPORTED.contains(&edge_mask) && inner_corner_count == 0",
        "multiple_diagonal_inner_corners_normalize_instead_of_overdrawing_full_cells",
        "outer_edge_plus_unrelated_inner_corner_normalizes_to_one_authored_cell",
    ]:
        if required not in shoreline_family:
            fail(f"semantic water topology normalization is missing: {required}")

    for required in [
        "normalize_lpc_authored_material_contacts_region",
        "mountain_path_shore_shoulders",
        "TileKind::MountainPath",
        "TileKind::Road",
        "mountain_path_touching_sand_is_repaired_with_an_authored_road_shoulder",
    ]:
        if required not in contacts:
            fail(f"MountainPath/Sand authored-contact policy is missing: {required}")
    if "apply_editor_terrain_paint_policy" not in editor_shell:
        fail("F3 explicit terrain-paint policy is missing")
    for required in [
        "TerrainPaintMode::Exact",
        "TerrainPaintMode::Coastline",
        "TerrainPaintMode::Hydrology",
        "normalize_lpc_authored_material_contacts_region",
    ]:
        if required not in editor_policy_family:
            fail(f"shared explicit terrain-paint policy is missing: {required}")
    if "normalize_lpc_authored_material_contacts_region" not in startup:
        fail("world startup does not apply authored material-contact repair")

    for required in [
        "OBJECT_ATLAS_MANIFEST_PATH",
        "audited_object_footprint_for_cell",
        "is_manifest_backed_natural_object",
        "audited_boulder_footprint_matches_the_same_deterministic_visual_variant",
    ]:
        if required not in assets:
            fail(f"manifest-backed natural object footprint authority is missing: {required}")
    if "audited_object_footprint_for_cell(kind, tx, ty)" not in runtime_draw_family:
        fail("F3 cursor preview still uses a generic prop footprint")
    if "footprint_for_legacy_object(kind)" in runtime_draw_family:
        fail("F3 cursor preview still calls the oversized legacy footprint fallback")
    for required in [
        "migrate_legacy_natural_object_footprints",
        "object_asset_refs",
        "audited_object_footprint_for_cell",
    ]:
        if required not in startup:
            fail(f"existing-save natural footprint migration is missing: {required}")

    objects = {entry.get("id"): entry for entry in object_manifest.get("objects", [])}
    expected = {
        "oak_tree": ([3, 4], [1, 1]),
        "berry_bush": ([1, 1], [1, 1]),
        "boulder": ([1, 1], [1, 1]),
        "boulder_variant_02": ([2, 1], [2, 1]),
        "boulder_variant_03": ([2, 2], [2, 1]),
        "boulder_variant_04": ([2, 2], [2, 1]),
        "forage_mushroom": ([1, 1], [0, 0]),
        "wild_herb": ([1, 1], [0, 0]),
    }
    for object_id, (visual, collision) in expected.items():
        entry = objects.get(object_id)
        if entry is None:
            fail(f"object atlas manifest is missing {object_id}")
        if entry.get("visualFootprintTiles") != visual:
            fail(f"{object_id} visual footprint changed: {entry.get('visualFootprintTiles')}")
        if entry.get("collisionFootprintTiles") != collision:
            fail(f"{object_id} collision footprint changed: {entry.get('collisionFootprintTiles')}")

    tree = next((entry for entry in placeables.get("entries", []) if entry.get("id") == "tree_default"), None)
    if tree is None:
        fail("tree_default placeable is missing")
    if tree.get("footprint", {}).get("visual_offset") != [-1, -3]:
        fail("tree_default visual offset is not aligned to the audited 3x4 atlas footprint")
    if tree.get("footprint", {}).get("visual_size") != [3, 4]:
        fail("tree_default visual size is not the audited 3x4 footprint")

    version_marker = "CURRENT_CLIENT_GENERATION_VERSION: u32 = "
    if version_marker not in save_lib:
        fail("client generation version marker is missing")
    version = int(save_lib.split(version_marker, 1)[1].split(";", 1)[0].strip())
    if version < 10:
        fail("client generation version predates migration 10")
    if f3.get("runtimeMigration", {}).get("generationVersion") != 10:
        fail("F3 contract does not declare generation migration 10")
    if f3.get("waterDepthPolicy", {}).get("generatedPixelsAllowed") is not False:
        fail("F3 contract permits generated water pixels")
    if f3.get("authoredContactPolicy", {}).get("generatedPixelsAllowed") is not False:
        fail("F3 contract permits generated terrain-contact pixels")
    if not (
        "exact authored V7 corner tuples" in editor_state
        or ("exact authored tuples" in editor_state and "V7" in editor_state)
    ):
        fail("F3 topology help does not explain source-pure authored V7 water tuples")

    print(
        "Authored water/path/footprint authority validated: exact full water cells, "
        "no quadrant synthesis or generated depth fallback, explicit Coast/Hydrology V7 Road "
        "shoulder repair for MountainPath/Sand, Exact mode isolation, and manifest-backed natural "
        "prop footprints with generation 10 migration"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
