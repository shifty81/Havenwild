#!/usr/bin/env python3
"""Guard canonical LPC water animation and shore-depth semantics."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V128: {path} is missing {missing}")


def require_any(paths: list[str], needles: list[str]) -> None:
    existing_payloads = []
    missing_paths = []
    for path in paths:
        source = ROOT / path
        if source.is_file():
            existing_payloads.append((path, source.read_text(encoding="utf-8")))
        else:
            missing_paths.append(path)
    if not existing_payloads:
        raise SystemExit(f"V128: none of these files exist: {paths}")
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in existing_payloads)
    ]
    if missing:
        present_paths = [path for path, _ in existing_payloads]
        raise SystemExit(
            f"V128: {present_paths} are missing {missing}; absent optional paths {missing_paths}"
        )


def forbid(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"V128: {path} contains forbidden stale text {present}")


def main() -> int:
    require(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "lpc_mapped_terrain_entry_for_map_with_water_frame",
            "entry_for_corners_with_water_frame",
            "is_animated_water_fill",
            "LpcMappedTerrainMaterial::Water",
            "LpcMappedTerrainMaterial::WaterDeep",
            "LpcMappedTerrainMaterial::WaterShallowsSand",
            "LpcMappedTerrainMaterial::WaterShallowsDirt",
        ],
    )
    require_any(
        [
            "crates/haven_assets/src/lpc_mapped_terrain_tests.rs",
            "crates/haven_assets/src/lpc_mapped_terrain.rs",
        ],
        ["pure_water_fills_can_cycle_authored_variants_without_animating_mixed_edges"],
    )
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "let water_animation_frame = (get_time() * 3.0).floor() as u32;",
            "self.draw_tile_base(map, tile, x, y, vec2(px, py), water_animation_frame)",
            "screen: Vec2",
            "lpc_mapped_terrain_entry_for_map_with_water_frame(map, x, y, water_animation_frame)",
        ],
    )
    require(
        "crates/haven_game/src/main.rs",
        [
            "lpc_mapped_terrain_entry_for_map_with_water_frame",
            "lpc_mapped_terrain_owns_map_cell",
        ],
    )
    require(
        "crates/haven_game/src/runtime_editor_shell.rs",
        [
            "normalize_editor_shore_water_band",
            "normalize_shore_water_lifecycle_region",
            "SHORE_WATER_NORMALIZE_PAD",
            "SHORE_WATER_NORMALIZE_PASSES",
            "land_or_shore_neighbors",
            "tile == TileKind::DeepWater && land_or_shore_neighbors > 0",
        ],
    )
    require_any(
        [
            "crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs",
            "crates/haven_game/src/runtime_editor_shell.rs",
        ],
        [
            "editor_deep_water_diagonal_to_shore_becomes_shallow_for_corner_mapping",
        ],
    )
    forbid(
        "crates/haven_game/src/runtime_editor_shell.rs",
        ["tile == TileKind::DeepWater && land_or_shore_cardinal > 0"],
    )
    forbid(
        "crates/haven_game/src/main.rs",
        [
            "lpc_mapped_terrain_entry_for_map, lpc_mapped_terrain_entry_for_map_with_water_frame"
        ],
    )
    forbid(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        ["px: f32,\n        py: f32,\n        water_animation_frame"],
    )
    print(
        "V128 OK: pure water fills animate while shore/depth mixed edges stay stable and deep water keeps a shallow shore buffer"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
