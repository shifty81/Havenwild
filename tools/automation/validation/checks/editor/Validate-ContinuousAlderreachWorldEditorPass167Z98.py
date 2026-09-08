#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(
            f"FAILED Pass167Z98 continuous Alderreach World Editor: {message}"
        )


def main() -> None:
    contract = json.loads(
        read("content/editor/world_canvas/continuous_alderreach_world_editor_v0_1.json")
    )
    require(
        contract["schema"]
        == "havenwild.editor.continuous_alderreach_world_editor.v0_1",
        "contract schema",
    )
    require(
        contract["pass"] in {"167Z98", "167Z103"},
        "historical contract or discrete-level correction",
    )
    require(contract["landmass"] == "Alderreach", "Alderreach authority")
    require(
        contract["coordinateAuthority"]["partitionWidthTiles"] == 96
        and contract["coordinateAuthority"]["partitionHeightTiles"] == 64,
        "96x64 partition authority",
    )
    require(
        contract["coordinateAuthority"]["partitionBordersDefaultVisible"] is False,
        "partition diagnostics default off",
    )

    mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
    editor_types = read("apps/haven_editor_native/src/app/editor_types.rs")
    for token in [
        "world_show_partitions: bool",
        "world_show_objects: bool",
        "world_show_zones: bool",
        "world_show_structural_levels: bool",
        "world_cursor_x: i32",
        "world_cursor_y: i32",
        "world_show_partitions: false",
        "world_show_objects: true",
        "world_show_zones: false",
        "world_show_structural_levels: false",
    ]:
        require(token in mod_rs, token)
    require(
        'EditorViewportMode::SceneRectangles => "World Editor"' in editor_types,
        "World Editor label",
    )

    world_surface = read("apps/haven_editor_native/src/app/world_surface_editor.rs")
    for token in [
        "pub(crate) struct WorldSurfaceViewOptions",
        "const WORLD_SURFACE_PARTITION_W: f32 = MAP_W as f32;",
        "const WORLD_SURFACE_PARTITION_H: f32 = MAP_H as f32;",
        "rectangle.grid_x.unwrap_or(0) as f32 * WORLD_SURFACE_PARTITION_W",
        "rectangle.grid_y.unwrap_or(0) as f32 * WORLD_SURFACE_PARTITION_H",
        "draw_scene_zone_overlay",
        "draw_scene_structural_level_overlay",
        "draw_scene_object_overlay",
        "world_preview_step",
        "storage partitions are diagnostics only",
        "world_surface_partitions_use_true_tile_dimensions",
        "world_preview_lod_reaches_native_tiles_when_zoomed_in",
    ]:
        require(token in world_surface, token)
    require("WORLD_SCENE_GRID_CELL" not in world_surface, "old square card geometry removed")

    controller = read("apps/haven_editor_native/src/app/canvas_controller.rs")
    for token in [
        "pub(crate) fn select_world_cell",
        "self.world_cursor_x = global.x;",
        "self.world_cursor_y = global.y;",
        "SelectionItem::Tile(GridPos",
        "self.world_show_partitions = !self.world_show_partitions",
        "self.world_show_objects = !self.world_show_objects",
        "self.world_show_zones = !self.world_show_zones",
        "self.world_show_structural_levels = !self.world_show_structural_levels",
    ]:
        require(token in controller, token)

    authoring_ui = read("apps/haven_editor_native/src/app/world_surface_authoring_ui.rs")
    for token in [
        'Alderreach World Authoring',
        'format!("Partition: {partition}")',
        'format!("Terrain: {terrain}")',
        'format!("Structural: {structural_level}")',
        'format!("Zone: {zone}")',
        '"Open Partition"',
    ]:
        require(token in authoring_ui, token)

    input_rs = read("apps/haven_editor_native/src/app/input.rs")
    require("self.update_world_editor_input" in input_rs, "global canvas input routing")
    require("self.open_assigned_rectangle_scene();" in input_rs, "Enter drill-down")

    shell_contract = json.loads(
        read("content/editor/native_editor_workspace_shell_v0_1.json")
    )
    require("World Editor" in shell_contract["documentTabs"], "workspace tab contract")
    require("World Surface" not in shell_contract["documentTabs"], "old tab label retired")

    require(
        (ROOT / "docs/archive/pass_history/PASS167Z98_CONTINUOUS_ALDERREACH_WORLD_EDITOR_FOUNDATION.md").is_file(),
        "current pass documentation",
    )
    require(
        (ROOT / "docs/roadmaps/CONTINUOUS_ALDERREACH_WORLD_EDITOR_PASS167Z98.md").is_file(),
        "world editor roadmap",
    )

    print("Pass167Z98 continuous Alderreach World Editor validation passed")


if __name__ == "__main__":
    main()
