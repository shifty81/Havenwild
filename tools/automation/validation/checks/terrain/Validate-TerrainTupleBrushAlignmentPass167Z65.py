#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"Terrain tuple brush alignment: missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def fail(message: str) -> None:
    raise SystemExit(f"Terrain tuple brush alignment: {message}")


def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        fail(f"{label} is missing: {needle}")


def main() -> int:
    bridge = text("crates/haven_world/src/terrain_editor_bridge.rs")
    mapped = text("crates/haven_assets/src/lpc_mapped_terrain.rs")
    mapped_tests = text("crates/haven_assets/src/lpc_mapped_terrain/tests.rs")
    mapped_family = mapped + "\n" + mapped_tests
    cache = text("crates/haven_game/src/base_terrain_cache.rs")
    runtime_base = text("crates/haven_game/src/runtime_terrain_base_draw.rs")
    runtime_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")
    runtime_plan = text("crates/haven_game/src/runtime_terrain_plan.rs")
    runtime_terrain_family = runtime_pass + "\n" + runtime_plan
    retained = text("crates/haven_game/src/terrain_scene_surface.rs")
    editor_atlas = text("apps/haven_editor_native/src/app/atlas_render.rs")
    editor_draw = text("apps/haven_editor_native/src/app/render_helpers.rs")
    editor_scene_draw = text("apps/haven_editor_native/src/app/scene_render_helpers.rs")
    editor_draw_family = editor_draw + "\n" + editor_scene_draw
    shoreline = text("crates/haven_world/src/autotile/shoreline_resolver.rs")
    shore_lifecycle = text("crates/haven_world/src/autotile/shore_water_lifecycle.rs")
    shore_tests = text("crates/haven_world/src/autotile/shoreline_regression_tests.rs")
    shoreline_family = shoreline + "\n" + shore_lifecycle + "\n" + shore_tests

    for needle in [
        "pub const TERRAIN_TUPLE_RENDER_OFFSET_TILES: f32 = 0.5",
        "x as f32 + TERRAIN_TUPLE_RENDER_OFFSET_TILES",
        "y as f32 + TERRAIN_TUPLE_RENDER_OFFSET_TILES",
        "corner_tuple_render_origin_is_half_a_tile_down_and_right",
    ]:
        require(bridge, needle, "shared tuple origin contract")
    if "x as f32 - TERRAIN_TUPLE_RENDER_OFFSET_TILES" in bridge:
        fail("tuple origin moves left instead of correcting the upper-left shift")
    if "y as f32 - TERRAIN_TUPLE_RENDER_OFFSET_TILES" in bridge:
        fail("tuple origin moves up instead of correcting the upper-left shift")

    for needle in [
        "lpc_mapped_terrain_owner_fill_entry_for_map",
        "lpc_mapped_terrain_transition_entry_for_map",
        ".filter(|entry| entry.is_mixed)",
        "land_transition_keeps_pure_base_and_separate_authored_overlay",
    ]:
        require(mapped_family, needle, "owner-fill/tuple separation")

    for needle in [
        "pub mapped_transition_entry: Option<LpcMappedTerrainEntry>",
        "resolve_authored_v7_surface_for_map(map, x, y)",
        "mapped_transition_entry: authored.transition",
    ]:
        require(cache, needle, "base terrain cache tuple authority")

    for needle in [
        "draw_mapped_terrain_tuple_overlay",
        "screen.x + offset",
        "screen.y + offset",
        "TERRAIN_TUPLE_RENDER_OFFSET_TILES",
    ]:
        require(runtime_base, needle, "runtime tuple draw origin")
    if "screen.x - offset" in runtime_base or "screen.y - offset" in runtime_base:
        fail("runtime tuple overlay still shifts toward the upper-left")

    for needle in [
        "mapped_tuple_indices",
        "cell.mapped_transition_entry.is_some()",
        "self.draw_mapped_terrain_tuple_overlay(entry, screen)",
    ]:
        require(runtime_terrain_family, needle, "runtime two-pass terrain draw")

    base_loop = retained.find("self.draw_tile_base(TerrainBaseDrawRequest")
    overlay_loop = retained.find("self.draw_mapped_terrain_tuple_overlay")
    if base_loop < 0 or overlay_loop < 0 or overlay_loop <= base_loop:
        fail("retained terrain surface does not draw tuple overlays after owner fills")

    for needle in [
        "lpc_mapped_terrain_owner_fill_entry_for_map",
        "lpc_mapped_terrain_transition_entry_for_map",
        "terrain_tuple_render_origin_tiles(x, y)",
        "draw_terrain_tuple_overlay",
    ]:
        require(editor_atlas, needle, "native editor tuple alignment")
    require(editor_draw_family, "textures.draw_terrain_tuple_overlay", "native editor overlay pass")

    if "for _ in 0..8" in shoreline_family:
        fail("water topology repair still cascades through repeated in-call erosion")
    for needle in [
        "let snapshot = map.tiles.clone();",
        "let changed = replacements.len();",
        "opposite_depth_edges_normalize_to_authored_shallow_topology",
        "marine_depth_topology_repair_preserves_ocean_identity",
    ]:
        require(shoreline_family, needle, "single-snapshot water normalization")

    print(
        "Terrain tuple brush alignment validated: pure owner fills remain cell-aligned, "
        "authored mixed tuples render +0.5 tile in both runtime and native editor, "
        "and depth topology normalization no longer cascades within one call"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
