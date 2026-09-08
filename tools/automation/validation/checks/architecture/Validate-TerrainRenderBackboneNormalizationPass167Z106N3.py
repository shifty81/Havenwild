#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def lines(path: str) -> int:
    return len(text(path).splitlines())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    frontend = text("crates/haven_game/src/client_frontend.rs")
    require("Credits [C]" in frontend, "title credits accessory label missing")
    require("credits_button_rect_for_viewport" in frontend, "credits viewport anchor missing")
    require("FrontendScreen::Credits" in frontend, "credits surface is not routed")

    mapped = text("crates/haven_assets/src/lpc_mapped_terrain.rs")
    sampling = text("crates/haven_assets/src/lpc_mapped_terrain/sampling.rs")
    require(lines("crates/haven_assets/src/lpc_mapped_terrain.rs") <= 750, "mapped-terrain facade exceeds 750 lines")
    require("mod sampling;" in mapped, "mapped-terrain sampling module missing")
    require("lpc_mapped_terrain_runtime_entry_for_tile_sampler" in sampling, "global sampler moved incorrectly")
    require("compatible_edge_bridge_entry_for_corners" not in sampling, "retired proxy terrain bridge returned")
    require("entry_for_corners(corners, seed)" in sampling, "exact-only mixed tuple resolver moved incorrectly")

    shore = text("crates/haven_world/src/autotile/shoreline_resolver.rs")
    lifecycle = text("crates/haven_world/src/autotile/shore_water_lifecycle.rs")
    require(lines("crates/haven_world/src/autotile/shoreline_resolver.rs") <= 750, "shoreline resolver exceeds 750 lines")
    require("shore_water_lifecycle" in shore, "shoreline resolver does not delegate lifecycle authority")
    require("normalize_shore_water_lifecycle_region" in lifecycle, "water lifecycle authority missing")

    terrain_pass = text("crates/haven_game/src/runtime_terrain_pass.rs")
    terrain_plan = text("crates/haven_game/src/runtime_terrain_plan.rs")
    require(lines("crates/haven_game/src/runtime_terrain_pass.rs") <= 750, "runtime terrain pass exceeds 750 lines")
    require("runtime_terrain_plan" in terrain_pass, "runtime terrain plan is not delegated")
    require("VisibleTerrainPlanCache" in terrain_plan and "TerrainWaterSpan" in terrain_plan, "retained terrain-plan authority missing")

    require(lines("crates/haven_game/src/runtime_draw.rs") <= 750, "runtime draw exceeds 750 lines")
    require(lines("crates/haven_game/src/runtime_editor_draw.rs") <= 750, "runtime editor draw exceeds 750 lines")
    require("fn draw_editor_cursor" not in text("crates/haven_game/src/runtime_draw.rs"), "editor cursor implementation still lives in player-world draw module")
    require("draw_editor_cursor" in text("crates/haven_game/src/runtime_editor_draw.rs"), "editor draw module missing authoring overlays")

    require(lines("apps/haven_editor_native/src/app/render_helpers.rs") <= 750, "native render helpers exceed 750 lines")
    require(lines("apps/haven_editor_native/src/app/scene_render_helpers.rs") <= 750, "native scene render helpers exceed 750 lines")
    require("SceneTilemapDraw" in text("apps/haven_editor_native/src/app/scene_render_helpers.rs"), "scene tilemap authority missing")

    require(lines("crates/haven_core/src/foundation/tile_object_catalog.rs") <= 750, "tile/object catalog exceeds 750 lines")
    require((ROOT / "crates/haven_core/src/foundation/tile_object_catalog_tests.rs").is_file(), "catalog tests were not separated")

    integrity = subprocess.run(
        [sys.executable, str(ROOT / "tools/automation/validation/validate_content_integrity.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    require(integrity.returncode == 0, f"content integrity is not clean:\n{integrity.stdout}")

    architecture = subprocess.run(
        [sys.executable, str(ROOT / "tools/automation/validation/validate_architecture.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    remaining = [line for line in architecture.stdout.splitlines() if " has " in line and "lines; limit" in line]
    permitted_remaining = {
        "- crates/haven_core/src/foundation.rs",
        "- crates/haven_game/src/player_inventory_ui.rs",
        "- crates/haven_game/src/runtime_editor_shell.rs",
    }
    require(
        all(any(line.startswith(prefix) for prefix in permitted_remaining) for line in remaining),
        f"N3-resolved architecture debt regressed: {remaining}",
    )
    require(len(remaining) <= 3, f"N3 may only leave its three declared N4 targets, found {remaining}")

    print("Terrain/render backbone normalization validated")
    print("- content integrity: clean")
    print("- mapped terrain facade <= 750 lines")
    print("- shoreline resolver <= 750 lines")
    print("- runtime terrain pass <= 750 lines")
    print("- runtime/world draw and editor draw separated")
    print("- native scene rendering separated")
    print(f"- remaining architecture debt: {len(remaining)} of the 3 declared N4 targets")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
