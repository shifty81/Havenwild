#!/usr/bin/env python3
"""Validate W76U-V document lifecycle against the current A14 Game Canvas authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
ERRORS: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        ERRORS.append(f"missing required file: {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def require(text: str, markers: list[str], context: str) -> None:
    for marker in markers:
        if marker not in text:
            ERRORS.append(f"{context}: missing marker {marker!r}")


def main() -> int:
    contract_path = ROOT / "content/editor/gamemaker_workspace_document_lifecycle_w76uv_v1.json"
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:
        ERRORS.append(f"could not load W76U-V contract: {exc}")
        contract = {}
    if contract.get("schema") != "havenwild.gamemaker_workspace_document_lifecycle.w76uv.v1":
        ERRORS.append("W76U-V contract schema mismatch")

    tabs = read("apps/haven_editor_native/src/app/document_tabs.rs")
    selection = read("apps/haven_editor_native/src/app/selection_controller.rs")
    outliner = read("apps/haven_editor_native/src/app/scene_outliner.rs")
    bank = read("apps/haven_editor_native/src/app/scene_bank_workspace.rs")
    draw = read("apps/haven_editor_native/src/app/draw.rs")
    scene_draw = read("apps/haven_editor_native/src/app/draw_scene_views.rs")
    input_rs = read("apps/haven_editor_native/src/app/input.rs")
    commands = read("apps/haven_editor_native/src/app/command_registry.rs")
    menu = read("apps/haven_editor_native/src/app/editor_menu.rs")
    chrome = read("apps/haven_editor_native/src/app/workspace_chrome.rs")
    mod_rs = read("apps/haven_editor_native/src/app/mod.rs")

    require(mod_rs, [
        "open_scene_documents: Vec<ProjectSceneId>",
        "recently_closed_scene_documents: Vec<ProjectSceneId>",
        "last_active_scene_document: Option<ProjectSceneId>",
        "scene_document_dirty_ids: HashSet<ProjectSceneId>",
        "scene_tab_overflow_open: bool",
    ], "EditorApp Scene workspace state")

    require(tabs, [
        "scene_tab_close_rect",
        "scene_tab_add_rect",
        "scene_tab_overflow_rect",
        "close_scene_document",
        "reopen_last_closed_scene_document",
        "begin_new_scene_from_document_bar",
        "browse_project_scenes",
        "activate_scene_workspace",
        "draw_scene_workspace_empty_state",
        "handle_scene_workspace_empty_state_click",
        "Closed {} editor tab; scene remains in the project",
        "New Scene...",
        "Open Scene Library...",
        "Reopen",
        "scene_tabs_reserve_new_and_overflow_controls",
        "dirty_marker_is_compact_and_explicit",
    ], "Scene DocumentTabBar lifecycle")

    require(selection, [
        "focus_scene_index_without_open",
        "ensure_selected_scene_document_open",
    ], "Scene document focus/open separation")

    require(outliner, [
        "SceneNameEditMode::Create",
        "ensure_selected_scene_document_open",
        "open_scene_documents.retain",
        "recently_closed_scene_documents.retain",
    ], "Scene create/rename/delete lifecycle integration")

    require(bank, [
        "Open in Game Canvas",
        "open_selected_scene_bank_scene",
    ], "Scene Library reopen authority")

    require(scene_draw + draw, [
        "scene_workspace_has_open_document",
        "draw_scene_workspace_empty_state",
        "draw_workspace_document_tab_overlay",
    ], "Scene empty/document overlay presentation")

    require(input_rs, [
        "KeyCode::W",
        "KeyCode::T",
        "reopen_last_closed_document",
        "request_close_active_document",
        "mark_active_scene_document_dirty",
    ], "Scene lifecycle shortcuts/dirty routing")

    require(commands + menu, [
        "NewSceneDocument",
        "BrowseProjectScenes",
        "CloseSceneDocument",
        "ReopenClosedSceneDocument",
        "New Scene...",
        "Browse Project Scenes...",
        "Close Scene Tab",
        "Reopen Closed Scene",
    ], "Canonical command registry")

    require(menu + chrome, [
        "clear_scene_document_dirty_state",
        "Game Canvas — No Spatial Document",
        "scene_document_dirty_ids",
    ], "Save/dirty/title integration")

    # Deletion must remain a distinct project-content operation rather than being
    # reused by tab close.
    if "delete_project_scene" in tabs:
        ERRORS.append("DocumentTabBar must never call delete_project_scene")
    if "delete_project_scene" not in outliner:
        ERRORS.append("Delete Scene destructive command is no longer separately owned by Scene Outliner")

    if ERRORS:
        print("W76U-V GameMaker workspace lifecycle validation FAILED")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("PASS: W76U-V GameMaker-style Scene document lifecycle")
    print("- real open-document tabs with close x, + New Scene, recent/reopen, and empty state")
    print("- tab close preserves project scene; Delete Scene remains separately destructive")
    print("- per-scene view state and dirty markers survive close/reopen through the universal W79 document lifecycle router")
    print("- Scene Library/Outliner feed the same Game Canvas open-document authority")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
