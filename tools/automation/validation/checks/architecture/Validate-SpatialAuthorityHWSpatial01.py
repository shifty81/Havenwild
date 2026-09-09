#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def source(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise AssertionError(f"missing required spatial authority source: {rel}")
    return path.read_text(encoding="utf-8", errors="strict")


def require(rel: str, *tokens: str) -> None:
    text = source(rel)
    for token in tokens:
        if token not in text:
            raise AssertionError(f"{rel} missing spatial authority token {token!r}")


def main() -> int:
    require(
        "crates/haven_spatial/src/lib.rs",
        "pub struct TileCoord",
        "TerrainTuplePresentationOrigin",
        "StructuralHost",
        "StructuralReceiver",
        "tile_rect_bottom_center_tiles",
    )
    for crate in ("haven_world", "haven_assets", "haven_render"):
        require(
            f"crates/{crate}/Cargo.toml",
            'haven_spatial = { path = "../haven_spatial" }',
        )

    require(
        "crates/haven_world/src/terrain_editor_bridge.rs",
        "TERRAIN_TUPLE_PRESENTATION_OFFSET_TILES",
        "TileAnchor::TerrainTuplePresentationOrigin",
        "assert_ne!(terrain_tuple_render_origin_tiles(7, 11), (7.0, 11.0))",
    )
    require(
        "apps/haven_editor_native/src/app/atlas_render.rs",
        "terrain_tuple_render_origin_tiles",
    )
    require(
        "apps/haven_editor_native/src/app/prepared_canvas_composition.rs",
        "terrain_tuple_render_origin_tiles",
    )
    require(
        "crates/haven_game/src/runtime_terrain_base_draw.rs",
        "TERRAIN_TUPLE_RENDER_OFFSET_TILES",
        "TILE_SIZE * TERRAIN_TUPLE_RENDER_OFFSET_TILES",
    )

    ramp = source("crates/haven_assets/src/lpc_cliff_ramp_provider.rs")
    for token in ("pub const fn stamp_origin", "(-1, 0)", "TileCoord::new(9, 20)"):
        if token not in ramp:
            raise AssertionError(f"ramp authority missing {token!r}")
    if "(-1, -1)" in ramp:
        raise AssertionError("retired directional-ramp one-row-up anchor reappeared")

    require(
        "crates/haven_game/src/runtime_structural_cliff_ramps.rs",
        "role.host_anchor_offset()",
        "global_y + i32::from(anchor_y)",
        "draw_cliff_source_rect",
    )

    require(
        "crates/haven_render/src/lib.rs",
        "tile_rect_bottom_center_tiles",
        "PLAYER_VISUAL_FOOT_OFFSET_Y: f32 = 18.0",
        "player_visual_foot_world(player).y",
    )
    runtime_draw = source("crates/haven_game/src/runtime_draw.rs")
    if "screen.y + 18.0" not in runtime_draw and "PLAYER_VISUAL_FOOT_OFFSET_Y" not in runtime_draw:
        raise AssertionError("runtime player composition drifted away from the 18px visual-foot authority")

    require(
        "crates/haven_game/src/runtime_scene_navigation.rs",
        "fn runtime_world_to_screen",
        "fn world_to_screen",
        "local_world_to_runtime_world",
    )
    require(
        "apps/haven_editor_native/src/app/canvas_camera.rs",
        "world_to_screen",
        "screen_to_world",
    )

    print("HW-SPATIAL-01 validation passed: shared anchors, dual-tile correction, ramp placement, feet, and transform parity are locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
