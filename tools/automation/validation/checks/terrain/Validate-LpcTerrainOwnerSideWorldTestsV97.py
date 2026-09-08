#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DEBUG = ROOT / "crates/haven_world/src/autotile/terrain_debug.rs"
PREVIEW = ROOT / "crates/haven_world/src/autotile/transition_rule_preview.rs"
COAST = ROOT / "crates/haven_world/src/island_coastline.rs"
ISLAND = ROOT / "crates/haven_world/src/island_pcg.rs"
REGISTRY = ROOT / "tools/automation/validation/validate.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V97 failed: {message}")


def main() -> int:
    debug = DEBUG.read_text(encoding="utf-8")
    preview = PREVIEW.read_text(encoding="utf-8")
    coast = COAST.read_text(encoding="utf-8")
    island = ISLAND.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    require(
        "debug_cell_reports_land_neighbor_on_water_owner_side" in debug,
        "terrain debug test does not follow owner-side shoreline resolution",
    )
    require(
        "debug_cell_reports_water_neighbor_and_edge_transition" not in debug,
        "stale land-owned shoreline debug test remains",
    )
    require(
        'rule.id == "shallow_water_touching_sand_bank"' in preview,
        "transition preview test does not use the Pass 90 shoreline rule id",
    )
    require(
        "sand_touching_water_wet_sand" not in preview,
        "removed pre-Pass-90 shoreline rule id remains in preview tests",
    )
    require(
        "fn enforce_open_water_boundary(" in coast
        and coast.count("enforce_open_water_boundary(width, height, &occupied, &mut land);") >= 3,
        "coast generation does not reassert open-water assembly boundaries",
    )
    require(
        "fn tile_touches_open_space(" in coast,
        "missing occupied-cell open-space boundary classifier",
    )
    require(
        "occupied_edge_next_to_missing_scene_stays_water_after_smoothing" in coast,
        "missing direct coastline smoothing regression test",
    )
    require(
        "moved_scene_cell_assemblies_grow_coast_against_empty_grid_slots" in island,
        "island assembly open-slot regression test was removed",
    )
    require(
        "Validate-LpcTerrainOwnerSideWorldTestsV97.py" in registry,
        "V97 is not registered in the editor validation domain",
    )

    print("V97 LPC terrain owner-side and open-boundary tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
