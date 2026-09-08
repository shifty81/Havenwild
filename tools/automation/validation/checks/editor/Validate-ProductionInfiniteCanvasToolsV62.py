#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
production = read("apps/haven_editor_native/src/app/production_tools.rs")
clipboard_tools = read("apps/haven_editor_native/src/app/clipboard_tools.rs")
production_surface = production + "\n" + clipboard_tools
toolrail = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
tool_registry = read("apps/haven_editor_native/src/app/tool_registry.rs")
layers_ui = read("apps/haven_editor_native/src/app/canvas_layers.rs") + "\n" + read("apps/haven_editor_native/src/app/pixel_layer_rail.rs")
draw = read("apps/haven_editor_native/src/app/draw_scene_views.rs")
render = read("apps/haven_editor_native/src/app/scene_render_helpers.rs")
controller = read("apps/haven_editor_native/src/app/canvas_controller.rs")
camera = read("apps/haven_editor_native/src/app/canvas_camera.rs")
bulk = read("crates/haven_editor/src/bulk_edit.rs")
clipboard = read("crates/haven_editor/src/scene_clipboard.rs")
selection = read("crates/haven_authoring/src/selection.rs")
registry = read("crates/haven_editor/src/validation_registry.rs")
contract_text = read("content/editor/canvas/production_infinite_canvas_contract_v0_1.json")
read("docs/editor/PRODUCTION_INFINITE_CANVAS_TOOLS_PASS49.md")

checks = [
    ("mod production_tools;", mod_rs, "production tool controller is not registered"),
    ("mod clipboard_tools;", mod_rs, "clipboard tool controller is not registered"),
    ("mod canvas_tool_rack;", mod_rs, "canonical Canvas tool rack is not registered"),
    ("UniversalTool::Rectangle", tool_registry + toolrail, "rectangle tool missing from canonical tool registry/rack"),
    ("UniversalTool::Fill", tool_registry + toolrail, "fill tool missing from canonical tool registry/rack"),
    ("UniversalTool::Replace", tool_registry + toolrail, "replace tool missing from canonical tool registry/rack"),
    ("UniversalTool::Pick", tool_registry + toolrail, "eyedropper/pick tool missing from canonical tool registry/rack"),
    ("SceneCanvasDragKind::Marquee", production, "marquee selection lifecycle missing"),
    ("SceneCanvasDragKind::MoveSelection", production, "drag-move lifecycle missing"),
    ("selection_items_in_rect", production, "marquee does not use headless selection query"),
    ("paint_scene_rectangle", production, "rectangle authoring command missing"),
    ("flood_fill_scene", production, "flood-fill authoring command missing"),
    ("replace_scene_value", production, "replace authoring command missing"),
    ("copy_scene_selection", production_surface, "copy command missing"),
    ("paste_scene_clipboard", production_surface, "paste command missing"),
    ("move_scene_selection", production_surface, "selection movement command missing"),
    ("KeyCode::C", production_surface, "Ctrl+C shortcut missing"),
    ("KeyCode::X", production_surface, "Ctrl+X shortcut missing"),
    ("KeyCode::V", production_surface, "Ctrl+V shortcut missing"),
    ("KeyCode::D", production_surface, "Ctrl+D shortcut missing"),
    ("KeyCode::Delete", production_surface, "Delete shortcut missing"),
    ("frame_current_selection", production_surface, "frame-selection command missing"),
    ("scene_canvas_states", mod_rs, "per-scene canvas camera storage missing"),
    ("frame_rect", camera, "camera cannot frame selection"),
    ("toggle_layer_visibility", layers_ui, "canonical layer visibility controls missing"),
    ("toggle_layer_lock", layers_ui, "canonical layer lock controls missing"),
    ("adjust_active_layer_opacity", layers_ui, "canonical Pixel layer opacity controls missing"),
    ("draw_scene_tilemap", draw, "scene map is not rendered through the permanent canvas"),
    ("object.visual_rect()", render, "objects are not rendered on their snapped visual footprint"),
    ("pub fn selection_bounds_for_items", bulk, "canonical multi-selection bounds missing"),
    ("pub fn paint_scene_rectangle", bulk, "headless rectangle tool missing"),
    ("pub fn flood_fill_scene", bulk, "headless flood-fill tool missing"),
    ("pub fn replace_scene_value", bulk, "headless replace tool missing"),
    ("pub struct SceneClipboard", clipboard, "scene clipboard contract missing"),
    ("object.id = scene.map.next_object_id()", clipboard, "pasted objects do not receive new IDs"),
    ("transition.id = scene.next_transition_id()", clipboard, "pasted transitions do not receive new IDs"),
    ("let backup = world.clone()", clipboard, "clipboard operations lack atomic recovery"),
    ("pub fn add_many", selection, "additive selection support missing"),
    ("pub fn toggle", selection, "toggle selection support missing"),
    ("id: \"production_infinite_canvas\"", registry, "validation registry omits Pass 49"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for rel, text in [
    ("production_tools.rs", production),
    ("clipboard_tools.rs", clipboard_tools),
    
    ("bulk_edit.rs", bulk),
    ("scene_clipboard.rs", clipboard),
]:
    if len(text.splitlines()) > 750:
        errors.append(f"{rel} exceeds the 750-line module ceiling")

if "selected_scene_object: Option<usize>" in mod_rs + production_surface + draw:
    errors.append("native scene selection regressed to an unstable object vector index")
if "serialize_lines()" in bulk + clipboard:
    errors.append("bulk editor tools regressed to full-world serialization")
if "SceneId::ALL.iter().position" in production_surface:
    errors.append("transition eyedropper is still limited to the legacy scene enum")

try:
    contract = json.loads(contract_text)
    if contract.get("pass") != "49":
        errors.append("production canvas contract pass mismatch")
    if len(contract.get("tools", [])) != 9:
        errors.append("production canvas contract must expose nine explicit tools")
    if contract.get("canvas", {}).get("perSceneCameraState") is not True:
        errors.append("per-scene camera state is not contractually required")
    if contract.get("selection", {}).get("marquee") is not True:
        errors.append("marquee selection is not contractually required")
    if contract.get("clipboard", {}).get("relativeCoordinates") is not True:
        errors.append("relative clipboard coordinates are not contractually required")
    if contract.get("layers", {}).get("locking") is not True:
        errors.append("layer locking is not contractually required")
    if contract.get("bulkEdits", {}).get("oneTypedUndoEntryPerAction") is not True:
        errors.append("bulk actions are not contractually one typed undo entry")
except Exception as exc:
    errors.append(f"invalid production canvas contract json: {exc}")

if errors:
    print("Production infinite-canvas tools validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Production infinite-canvas tools validation passed.")
