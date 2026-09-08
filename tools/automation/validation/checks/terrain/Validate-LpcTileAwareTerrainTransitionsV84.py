#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


resolver = read("crates/haven_world/src/autotile/transition_resolver.rs")
editor_atlas = read("apps/haven_editor_native/src/app/atlas_render.rs")
runtime_terrain = read("crates/haven_game/src/terrain_render.rs")

checks = [
    (
        "use haven_core::{TavernMap, TileKind};",
        resolver,
        "transition resolver must keep exact TileKind identity available",
    ),
    (
        "let Some(center_tile) = tile_at(map, x, y)",
        resolver,
        "resolve_terrain_transitions must start from exact center TileKind",
    ),
    (
        "tiles_share_transition_surface(center_tile, neighbor_tile)",
        resolver,
        "cardinal transition checks must use exact tile-surface equivalence",
    ),
    (
        "edge_material_for_tiles(center_tile, neighbor_tile)",
        resolver,
        "cardinal transition material must be tile-aware before family fallback",
    ),
    (
        "corner_material_for_tiles(center_tile, diagonal_tile)",
        resolver,
        "inner-corner transition material must be tile-aware before family fallback",
    ),
    (
        "fn water_depth_class(tile: TileKind) -> Option<u8>",
        resolver,
        "water depth classification is required for shallow/deep edge transitions",
    ),
    (
        "fn wet_sand_painted_in_grass_resolves_grass_fringe_on_all_edges()",
        resolver,
        "wet-sand-in-grass regression test is missing",
    ),
    (
        "fn single_shallow_water_strip_resolves_land_and_deep_water_edges()",
        resolver,
        "single-row shallow/deep water regression test is missing",
    ),
    (
        "Color::new(1.0, 1.0, 1.0, opacity),",
        editor_atlas,
        "native editor must draw transition atlas replacement tiles at full layer opacity",
    ),
    (
        "TransitionMaterial::RockShadow => Color::new(1.0, 1.0, 1.0, 1.0)",
        runtime_terrain,
        "runtime transition atlas tint must be full opacity for replacement tiles",
    ),
]

for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for forbidden in [
    "opacity * 0.72",
    "TransitionMaterial::WetSand | TransitionMaterial::SandBlend =>",
    "TransitionMaterial::GrassFringe => Color::new(0.92, 1.0, 0.88, 0.82)",
]:
    if forbidden in editor_atlas or forbidden in runtime_terrain:
        errors.append(f"translucent terrain replacement regression remains: {forbidden}")

if errors:
    print("LPC tile-aware terrain transition validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(
    "V84 OK: terrain transitions preserve exact tile identity and atlas replacements draw opaque"
)
