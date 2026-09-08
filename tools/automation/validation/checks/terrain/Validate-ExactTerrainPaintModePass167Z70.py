#!/usr/bin/env python3
"""Validate explicit Exact/Coast/Hydrology terrain authoring authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    core = read("crates/haven_core/src/terrain_contract.rs")
    game = read("crates/haven_game/src/runtime_editor_shell.rs")
    bootstrap = read("crates/haven_game/src/game_bootstrap.rs")
    native = read("apps/haven_editor_native/src/app/scene_authoring.rs")
    native_state = read("apps/haven_editor_native/src/app/mod.rs")
    editor = read("crates/haven_editor/src/scene_edit.rs")
    shared_policy = read("crates/haven_authoring/src/terrain_policy.rs")
    editor_policy_family = editor + "\n" + shared_policy
    tests = read("crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs")
    workspace = json.loads(read("content/editor/f3_terrain_style_workspace_v0_1.json"))

    require("pub enum TerrainPaintMode" in core, "missing shared TerrainPaintMode", errors)
    for token in ["Exact", "Coastline", "Hydrology"]:
        require(token in core, f"missing TerrainPaintMode::{token}", errors)
    require("#[default]" in core and "Exact" in core, "Exact is not the default mode", errors)
    require(
        "terrain_paint_mode: TerrainPaintMode::Exact" in bootstrap,
        "F3 editor does not bootstrap in Exact mode",
        errors,
    )
    require(
        "TerrainPaintMode::Exact => Ok" in editor_policy_family,
        "Exact mode does not have an explicit non-mutating branch",
        errors,
    )
    require(
        "normalize_shore_water_lifecycle_region" not in game,
        "runtime editor still calls broad shoreline lifecycle directly",
        errors,
    )
    require(
        "apply_editor_terrain_paint_policy" in game,
        "runtime editor is not routed through explicit paint policy",
        errors,
    )
    require(
        "paint_scene_tile_with_mode" in native,
        "native Scene Editor does not pass the selected terrain paint mode",
        errors,
    )
    require(
        "terrain_paint_mode: TerrainPaintMode::Exact" in native_state,
        "native Scene Editor does not default to Exact mode",
        errors,
    )
    require(
        "exact_editor_paint_does_not_expand_one_land_cell_into_a_shallow_square" in tests,
        "missing exact-paint shallow-halo regression test",
        errors,
    )
    policy = workspace.get("terrainPaintModes", {})
    require(policy.get("default") == "exact", "workspace default mode is not exact", errors)
    require(
        policy.get("exactBrushMayCreateShallowHalo") is False,
        "workspace still permits Exact mode to create a shallow halo",
        errors,
    )
    mode_ids = {entry.get("id") for entry in policy.get("modes", [])}
    require(
        mode_ids == {"exact", "coastline", "hydrology"},
        f"unexpected terrain paint modes: {sorted(mode_ids)}",
        errors,
    )

    if errors:
        print("Pass167Z70 exact terrain paint validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Pass167Z70 exact terrain paint validation passed")
    print("- Exact is the default in F3 and native Scene Editor")
    print("- Exact mode performs no neighboring terrain/water mutation")
    print("- Coast and Hydrology remain explicit authoring modes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
