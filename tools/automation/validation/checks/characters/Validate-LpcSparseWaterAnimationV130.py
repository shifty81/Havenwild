#!/usr/bin/env python3
"""Guard sparse randomized water detail and terrain-v7 overlay ownership."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V130: {path} is missing {missing}")


def require_any(paths: list[str], needles: list[str]) -> None:
    payloads = [
        (path, (ROOT / path).read_text(encoding="utf-8"))
        for path in paths
        if (ROOT / path).is_file()
    ]
    if not payloads:
        raise SystemExit(f"V130: none of these files exist: {paths}")
    missing = [
        needle
        for needle in needles
        if not any(needle in payload for _, payload in payloads)
    ]
    if missing:
        raise SystemExit(
            f"V130: {', '.join(path for path, _ in payloads)} is missing {missing}"
        )


def forbid(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"V130: {path} contains forbidden stale text {present}")


def main() -> int:
    require(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "fn animated_water_variant(seed: u32, water_frame: u32, variant_count: usize) -> usize",
            "if ((seed >> 4) % 100) >= 12",
            "let detail_variant_count = variant_count - 1;",
            "let hold = 6 + ((seed >> 20) as usize % 5);",
        ],
    )
    require_any(
        [
            "crates/haven_assets/src/lpc_mapped_terrain_tests.rs",
            "crates/haven_assets/src/lpc_mapped_terrain.rs",
        ],
        [
            "animated_water_variants_are_sparse_and_slow",
            "assert_eq!(animated_water_variant(0x800, 0, 4), 0);",
        ],
    )
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "lpc_mapped_terrain_owns_map_cell(map, x, y)",
            "draw_tile_transition_overlays(map, x, y, px, py, cached, transition_atlas)",
        ],
    )
    forbid(
        "crates/haven_assets/src/lpc_mapped_terrain.rs",
        [
            "((variant_seed as usize) + water_frame as usize) % variant_count",
            "let hold = 1 + ((seed >> 20) as usize % 2);",
        ],
    )
    print("V130 OK: pure water detail is sparse, slow, deterministic, and terrain-v7-owned cells suppress legacy overlays")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
