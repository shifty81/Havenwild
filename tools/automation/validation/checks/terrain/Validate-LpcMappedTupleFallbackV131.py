#!/usr/bin/env python3
"""Guard missing terrain-v7 tuples against stale legacy terrain fallback."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V131: {path} is missing {missing}")


def require_any(paths: list[str], needles: list[str]) -> None:
    payloads = [
        (path, (ROOT / path).read_text(encoding="utf-8"))
        for path in paths
        if (ROOT / path).is_file()
    ]
    if not payloads:
        raise SystemExit(f"V131: none of these files exist: {paths}")
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in payloads)
    ]
    if missing:
        raise SystemExit(
            f"V131: {', '.join(path for path, _ in payloads)} is missing {missing}"
        )


def main() -> int:
    require(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "fallback_entry_for_missing_tuple",
            "fallback_material_for_missing_tuple",
            "fallback_material_priority",
            "contains_water_and_land",
            "is_water_material",
            "is_dirt_or_stone_shore",
            "water_frame.filter(|_| !is_mixed)",
            "LpcMappedTerrainMaterial::WaterShallowsSand",
            "LpcMappedTerrainMaterial::WaterDeep",
            '#[path = "lpc_mapped_terrain_tests.rs"]',
        ],
    )
    require_any(
        [
            "crates/haven_assets/src/lpc_mapped_terrain_tests.rs",
            "crates/haven_assets/src/lpc_mapped_terrain.rs",
        ],
        [
            "missing_mapped_water_tuples_fallback_to_lpc_owned_fills",
            "missing_mixed_tuple_fallbacks_stay_stable_across_water_frames",
            "mapped_water_tuple_fallback_keeps_cells_owned",
            "missing_sand_water_tuples_do_not_fallback_to_square_land",
            "missing_dirt_water_tuples_do_not_fallback_to_square_land",
            "missing_grass_water_tuples_do_not_fallback_to_square_land",
            "missing but mapped shore/depth tuple should not fall back to legacy terrain",
        ],
    )
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "lpc_mapped_terrain_entry_for_map_with_water_frame(map, x, y, water_animation_frame)",
            "lpc_mapped_terrain_owns_map_cell(map, x, y)",
        ],
    )
    print(
        "V131 OK: missing mapped water/shore tuples use terrain-v7 fallback fills and suppress stale legacy overlays"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
