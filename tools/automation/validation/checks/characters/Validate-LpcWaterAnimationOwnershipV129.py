#!/usr/bin/env python3
"""Guard terrain-v7 ownership and water animation phase policy."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V129: {path} is missing {missing}")


def require_any(paths: list[str], needles: list[str]) -> None:
    payloads = [(path, (ROOT / path).read_text(encoding="utf-8")) for path in paths]
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in payloads)
    ]
    if missing:
        joined = ", ".join(path for path, _ in payloads)
        raise SystemExit(f"V129: none of [{joined}] contain {missing}")


def forbid(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"V129: {path} contains forbidden stale text {present}")


def main() -> int:
    require(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "lpc_mapped_terrain_owns_map_cell",
            "animated_water_variant",
            "WaterShallowsSand",
            "WaterShallowsDirt",
            "if ((seed >> 4) % 100) >= 12",
            "let hold = 6 + ((seed >> 20) as usize % 5);",
        ],
    )
    require_any(
        [
            "crates/haven_assets/src/lpc_mapped_terrain.rs",
            "crates/haven_assets/src/lpc_mapped_terrain_tests.rs",
        ],
        [
            "pure_mapped_cells_are_owned_even_when_no_mixed_transition_is_present",
            "animated_water_variants_are_sparse_and_slow",
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
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "self.lpc_mapped_terrain_atlas.is_some()",
            "lpc_mapped_terrain_owns_map_cell(map, x, y)",
            "draw_tile_transition_overlays(map, x, y, px, py, cached, transition_atlas)",
        ],
    )
    forbid(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "lpc_mapped_terrain_transition_covers_map_cell(map, x, y)",
        ],
    )
    print(
        "V129 OK: terrain-v7 owns mapped water/coast cells and pure water variants animate with sparse per-tile offsets"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
