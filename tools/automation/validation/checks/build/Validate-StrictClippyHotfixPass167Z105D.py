#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z105D strict Clippy hotfix: {message}")


def main() -> None:
    contract = json.loads(
        (ROOT / "content/build/editor_compile_hotfix_v167z105d.json").read_text(encoding="utf-8")
    )
    require(contract["schema"] == "havenwild.build.editor_compile_hotfix.v167z105d", "contract schema")
    require(contract["pass"] == "167Z105D", "contract pass")
    require(contract["deadCodeSuppressionsAdded"] is False, "no dead-code suppression")
    require(contract["clippySuppressionsAdded"] is False, "no Clippy suppression")
    require(contract["inputRoutingBehaviorChanged"] is False, "input behavior preserved")
    require(contract["cliffRuntimeBehaviorChanged"] is False, "cliff behavior unchanged")
    require(contract["continuousWorldAuthorityPreserved"] is True, "continuous world authority")

    controller = (ROOT / "apps/haven_editor_native/src/app/canvas_controller.rs").read_text(encoding="utf-8")
    require("handle_world_canvas_click" not in controller, "obsolete world click helper removed")

    island = (ROOT / "apps/haven_editor_native/src/app/island_workspace.rs").read_text(encoding="utf-8")
    require("cycle_selected_island_scene_cell" not in island, "obsolete storage-chunk cycle helper removed")

    types = (ROOT / "apps/haven_editor_native/src/app/editor_types.rs").read_text(encoding="utf-8")
    require("Debug, Default, PartialEq, Eq" in types, "enum defaults derived")
    require("impl Default for WorldEditTool" not in types, "manual WorldEditTool default removed")
    require("impl Default for WorldLayerMode" not in types, "manual WorldLayerMode default removed")
    world_tool = types.split("pub(crate) enum WorldEditTool", 1)[1].split("impl WorldEditTool", 1)[0]
    world_layer = types.split("pub(crate) enum WorldLayerMode", 1)[1].split("impl WorldLayerMode", 1)[0]
    require("#[default]\n    Select," in world_tool, "Select remains WorldEditTool default")
    require("#[default]\n    Terrain," in world_layer, "Terrain remains WorldLayerMode default")

    input_source = (ROOT / "apps/haven_editor_native/src/app/input.rs").read_text(encoding="utf-8")
    expected = """if self.viewport_mode == EditorViewportMode::SceneRectangles
            && self.workspace_shell.right_panel_visible
            && self.workspace_shell.right_dock_tab == RightDockTab::Properties
            && self.handle_world_properties_click(mx, my, self.inspector_content_rect())"""
    require(expected in input_source, "SceneRectangles Properties routing collapsed")
    require("handle_scene_rectangle_inspector_click" not in input_source, "retired duplicate SceneRectangles inspector handler returned")

    edited = "\n".join([controller, island, types, input_source])
    require("#[allow(dead_code)]" not in edited, "no dead-code allow in repaired files")
    require("#[expect(dead_code)]" not in edited, "no dead-code expect in repaired files")
    require("#[allow(clippy::derivable_impls)]" not in edited, "no derivable-default suppression in repaired files")
    require("#[allow(clippy::collapsible_if)]" not in edited, "no collapsible-if suppression in repaired files")

    print("Pass167Z105D strict Clippy hotfix validation passed")


if __name__ == "__main__":
    main()
