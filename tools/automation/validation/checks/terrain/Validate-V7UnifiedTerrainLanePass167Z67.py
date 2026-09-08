#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"V7 unified terrain lane: missing {rel}")
    return path.read_text(encoding="utf-8-sig")


def load(rel: str) -> dict:
    return json.loads(text(rel))


def fail(message: str) -> None:
    raise SystemExit(f"V7 unified terrain lane: {message}")


def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        fail(f"{label} is missing: {needle}")


def main() -> int:
    authority = load("content/worldgen/terrain_visual_family_authority_v0_1.json")
    f3 = load("content/editor/f3_terrain_style_workspace_v0_1.json")
    atlas = load("assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json")
    scene = load("content/worldgen/scenes/open_world/willowmere_outskirts_region_v0_1.json")
    bindings = load("content/assets/terrain_material_bindings_v0_2.json")

    mapped = text("crates/haven_assets/src/lpc_mapped_terrain.rs")
    terrain = text("crates/haven_game/src/terrain_render.rs")
    base = text("crates/haven_game/src/runtime_terrain_base_draw.rs")
    runtime_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")
    retained = text("crates/haven_game/src/terrain_scene_surface.rs")
    main_rs = text("crates/haven_game/src/main.rs")
    native = text("apps/haven_editor_native/src/app/atlas_render.rs")
    palette = text("crates/haven_editor/src/palette_defaults.rs")
    asset_palette = text("crates/haven_assets/src/asset_palette.rs")
    bridge = text("crates/haven_game/src/bridge_render.rs")
    save = text("crates/haven_save/src/lib.rs")

    if authority.get("activeOpenWorldFamily") != "lpc_terrain_v7_island_v1":
        fail("active certification family is not the isolated V7 lane")
    if authority.get("runtimeMode") != "v7_source_pure_certification":
        fail("runtime mode is not V7 source-pure certification")
    if f3.get("activeCertificationLane") != "lpc_terrain_v7":
        fail("F3 is not filtered to the active V7 lane")
    if f3.get("waterDepthPolicy", {}).get("crossFamilyOverlayAllowed") is not False:
        fail("F3 water policy permits cross-family overlays")
    if f3.get("normalizedAtlasPolicy", {}).get("globalMixedAtlasAllowed") is not False:
        fail("F3 permits a blended global terrain atlas")

    if atlas.get("stylePackLane") != "lpc_terrain_v7":
        fail("normalized terrain atlas is not marked V7")
    if atlas.get("sourcePurity", {}).get("status") != "isolated":
        fail("normalized V7 atlas is not source-purity certified")
    if len(atlas.get("entries", [])) < 3000:
        fail(f"normalized V7 atlas coverage unexpectedly small: {len(atlas.get('entries', []))}")
    exact_map = atlas.get("tileKindTerrainMap", {})
    for tile_kind, material in {"stone_path":"Stone_Tan","pebble_shore":"Gravel_1","road":"Dirt_Tan","mountain_path":"Dirt_Roots","mud_bank":"Mud_Brown"}.items():
        if exact_map.get(tile_kind) != material:
            fail(f"exact W77 mapping {tile_kind} must remain {material}")
    if "cliff" in exact_map:
        fail("structural Cliff must not be part of the ground tuple material map")

    for needle in [
        "lpc_mapped_terrain_quiet_entry",
        'if material != "Grass"',
        "atomic objects/stamps",
        ".filter(|entry| entry.is_mixed)",
    ]:
        require(mapped, needle, "quiet fill and exact tuple authority")
    for forbidden in [
        "draw_direct_water_depth_rim",
        "draw_tile_transition_overlays",
        "mod terrain_transition_draw;",
        "resolve_transition_atlas_requests",
        "resolve_transition_inner_corner_requests",
    ]:
        if forbidden in runtime_pass + retained + main_rs + native:
            fail(f"active renderer still contains superseded overlay path: {forbidden}")
    if "direct_lpc_base_rect" in base:
        fail("V7 base renderer can still call the ElizaWy terrain mapper")
    require(base, "self.lpc_mapped_terrain_atlas.as_ref()", "normalized V7 runtime base")
    require(runtime_pass, "self.draw_mapped_terrain_tuple_overlay(entry, screen)", "runtime tuple pass")
    require(retained, "self.draw_mapped_terrain_tuple_overlay", "retained tuple pass")
    require(native, "terrain_tuple_render_origin_tiles(x, y)", "native tuple origin")
    require(native, "self.lpc_mapped_terrain.as_ref()", "native normalized atlas")
    require(asset_palette, "SourcePureNormalized", "native palette provenance")
    require(asset_palette, "lpc_mapped_terrain_preview_entry(tile)", "source-pure palette thumbnail")
    require(bridge, "lpc_mapped_terrain_quiet_entry(underlay)", "V7 bridge underlay")

    if "BuildTool::Floor(TileKind::WetSand)" in palette:
        fail("WetSand remains in the default editor palette")
    version_marker = "CURRENT_CLIENT_GENERATION_VERSION: u32 = "
    if version_marker not in save:
        fail("generation version marker is missing")
    version = int(save.split(version_marker, 1)[1].split(";", 1)[0].strip())
    if version < 10:
        fail("generation version predates the V7 migration baseline 10")
    if "WetSand" in json.dumps(scene):
        fail("active generated V7 scene still emits WetSand")

    wet = next((b for b in bindings.get("bindings", []) if b.get("tileKind") == "WetSand"), None)
    if wet is None or wet.get("material") != "Sand" or wet.get("directPaintAllowed") is not False:
        fail("legacy WetSand binding is not a hidden Sand alias")

    for needle in [
        "TileKind::Grass | TileKind::TallGrass",
        "TileKind::Sand | TileKind::WetSand",
        "TileKind::PebbleShore",
        "TileKind::MountainPath",
        "TileKind::MountainRock",
        "TileKind::CaveFloor",
        "TileKind::OceanShallow | TileKind::ShoreFoam",
        "TileKind::DeepWater | TileKind::OceanDeep",
    ]:
        require(terrain, needle, "source-pure V7 direct fallback")

    print(
        "V7 unified terrain lane validated: one source-pure normalized atlas, exact "
        "corner tuples for land and water, no ElizaWy/generic overlays, WetSand retired, "
        "quiet non-grass fills, and atomic detail placement policy"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
