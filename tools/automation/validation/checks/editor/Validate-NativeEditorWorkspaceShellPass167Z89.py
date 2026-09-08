#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAILED Pass167Z89 native editor workspace shell: {message}")


def main() -> None:
    contract_path = ROOT / "content/editor/native_editor_workspace_shell_v0_1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    require(contract["schema"] == "havenwild.native_editor.workspace_shell.v0_1", "schema")
    require(contract["pass"] == "167Z89", "pass")
    require(contract["offlineRequired"] is True, "offline editor requirement")
    require(contract["shell"]["bottomDock"]["behavior"].startswith("overlay"), "overlay bottom dock")
    require(len(contract["shell"]["bottomDock"]["tabs"]) == 5, "five bottom dock tabs")

    cargo = read("apps/haven_editor_native/Cargo.toml")
    require("serde.workspace = true" in cargo, "serde dependency")
    require("serde_json.workspace = true" in cargo, "serde_json dependency")

    mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
    for token in [
        "mod workspace_chrome;",
        "mod workspace_shell;",
        "workspace_shell: EditorWorkspaceShellState",
        "workspace_resize_drag: Option<WorkspaceResizeDrag>",
        "saved_undo_depth: usize",
        "EditorWorkspaceShellState::load_default()",
    ]:
        require(token in mod_rs, token)

    shell = read("apps/haven_editor_native/src/app/workspace_shell.rs")
    for token in [
        "native_workspace_layout_v0_1.json",
        "BottomDockTab",
        "left_panel_visible",
        "right_panel_visible",
        "bottom_dock_open",
        "WorkspaceResizeDrag",
        "normalize_in_place",
        "save_default",
        "load_default",
    ]:
        require(token in shell, token)

    geometry = read("apps/haven_editor_native/src/app/ui_shell.rs")
    for token in [
        "MENU_BAR_H",
        "DOCUMENT_BAR_H",
        "bottom_dock",
        "bottom_tab_bar",
        "bottom_dock_toggle_rect",
        "left_splitter",
        "right_splitter",
        "bottom_splitter",
        "center_panel.y + center_panel.h - dock_h",
    ]:
        require(token in geometry, token)
    require("validation_has_issues" not in geometry, "validation must not resize the shell")

    chrome = read("apps/haven_editor_native/src/app/workspace_chrome.rs")
    for token in [
        "draw_workspace_status_bar",
        "draw_workspace_bottom_dock",
        "draw_workspace_splitters",
        "update_workspace_resize_input",
        "handle_workspace_chrome_click",
        "handle_workspace_shell_shortcuts",
        "KeyCode::J",
        "recent_commands",
        "asset_browser.summary()",
    ]:
        require(token in chrome, token)

    draw = read("apps/haven_editor_native/src/app/draw.rs")
    for token in [
        "self.shell_layout()",
        "self.active_document_dirty()",
        "self.workspace_shell.left_panel_visible",
        "self.workspace_shell.right_panel_visible",
        "self.draw_workspace_bottom_dock",
        "self.draw_workspace_splitters",
        "self.draw_workspace_status_bar",
    ]:
        require(token in draw, token)

    input_rs = read("apps/haven_editor_native/src/app/input.rs")
    require("self.update_workspace_resize_input()" in input_rs, "splitter input integration")

    menu = read("apps/haven_editor_native/src/app/editor_menu.rs")
    for token in [
        "Toggle Project Panel",
        "Toggle Inspector",
        "Toggle Bottom Panels",
        "Open Validation Panel",
        "Reset Workspace Layout",
        "self.saved_undo_depth = self.command_bus.undo_len();",
    ]:
        require(token in menu, token)

    pixel_input = read("apps/haven_editor_native/src/app/pixel_studio_input.rs")
    animation_input = read("apps/haven_editor_native/src/app/animation_studio_input.rs")
    legacy_rect = "Rect::new(22.0, 92.0, 226.0, screen_height() - 116.0)"
    require(legacy_rect not in pixel_input, "Pixel Studio must use shared shell geometry")
    require(legacy_rect not in animation_input, "Animation Studio must use shared shell geometry")

    streaming = read("crates/haven_game/src/runtime_surface_streaming.rs")
    test_index = streaming.index("mod surface_maintenance_tests")
    last_impl_index = streaming.rindex("impl Game")
    require(test_index > last_impl_index, "test module must follow production impl items")
    require("allow(clippy::items_after_test_module)" not in streaming, "no lint suppression")

    print("Pass167Z89 native editor workspace shell validation passed")


if __name__ == "__main__":
    main()
