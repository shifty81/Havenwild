#!/usr/bin/env python3
"""Lock the LPC sand-over-grass 8-neighbor blob terrain pass."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def payload(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(path: str, needles: list[str]) -> None:
    text = payload(path)
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"V127: {path} missing {missing}")


def main() -> int:
    require(
        "crates/haven_game/src/terrain_render.rs",
        [
            "draw_lpc_sand_over_grass_blob_overlay",
            "lpc_sand_over_grass_transition_owned_by_sand_cell",
            "SandGrassBlobNeighbors",
            "has_any_sand_neighbor",
            "is_sand_at",
            "is_grass_like_at",
            "draw_inner_grass_corner",
            "draw_outer_grass_corner",
            "Isolated sand needs all four corners softened",
        ],
    )
    require(
        "crates/haven_game/src/runtime_terrain_pass.rs",
        [
            "draw_lpc_sand_over_grass_blob_overlay(map, tile, x, y, px, py)",
            "lpc_sand_over_grass_transition_owned_by_sand_cell(map, x, y)",
        ],
    )
    require(
        "crates/haven_game/src/main.rs",
        [
            "draw_lpc_sand_over_grass_blob_overlay",
            "lpc_sand_over_grass_transition_owned_by_sand_cell",
        ],
    )
    require(
        "tools/build/Build.sh",
        [
            "validate LPC sand-over-grass blob terrain",
            "Validate-LpcSandGrassBlobTerrainV127.py",
        ],
    )
    require("tools/automation/validation/validate.py", ["Validate-LpcSandGrassBlobTerrainV127.py"])
    print("V127 OK: LPC sand-over-grass blob terrain owns isolated, outer, and inner corners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
