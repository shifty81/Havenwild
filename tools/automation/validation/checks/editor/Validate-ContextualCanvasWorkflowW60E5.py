#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

layers = read("apps/haven_editor_native/src/app/canvas_layers.rs")
for marker in [
    "pub(crate) enum CanvasLayerGroup",
    'Self::Visual => "VISUAL"',
    'Self::Gameplay => "GAMEPLAY"',
    'Self::Animation => "ANIMATION"',
    'Self::Guides => "GUIDES"',
    'label: "Frame Events"',
    "select_canvas_layer_by_shortcut",
    "canvas_layer_row_layout",
    "GROUP_HEADER_H",
]:
    if marker not in layers:
        errors.append(f"grouped layer authority missing: {marker}")

tools = read("apps/haven_editor_native/src/app/tool_registry.rs")
for marker in [
    "Anchor,",
    'Self::Anchor => "Anchor / Pivot"',
    'shortcut: "1 / S"',
    'shortcut: "2 / P"',
    'shortcut: "9 / Space-drag"',
    'shortcut: "Ctrl+E"',
    "Some(L::AnimationAnchors)",
    "Some(L::AnimationSockets)",
    "Some(L::AnimationEvents)",
]:
    if marker not in tools:
        errors.append(f"contextual tool registry missing: {marker}")

rack = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
for marker in [
    "handle_contextual_canvas_shortcuts",
    "select_canvas_layer_by_shortcut(index)",
    "KeyCode::Key1, UniversalTool::Select",
    "KeyCode::Key2, UniversalTool::Paint",
    "KeyCode::Key3, UniversalTool::Rectangle",
    "KeyCode::Key4, UniversalTool::Fill",
    "KeyCode::Key6, UniversalTool::Pick",
    "KeyCode::Key8, UniversalTool::Erase",
    "KeyCode::Key9, UniversalTool::Pan",
    "W60E5: selection is a marquee",
]:
    if marker not in rack:
        errors.append(f"contextual shortcut/tool-rack authority missing: {marker}")

input_rs = read("apps/haven_editor_native/src/app/input.rs")
if "self.handle_contextual_canvas_shortcuts();" not in input_rs:
    errors.append("main editor input path does not invoke contextual CanvasWorkspace shortcuts")

scene = read("apps/haven_editor_native/src/app/production_tools.rs")
if "(KeyCode::Key1, SceneEditTool::Select)" in scene:
    errors.append("Scene Editor still owns a duplicate numeric tool-key authority")
if "shift_down && is_key_pressed(KeyCode::P)" not in scene:
    errors.append("Scene autotile preview did not move off the universal P tool shortcut")

world = read("apps/haven_editor_native/src/app/world_surface_authoring.rs")
if "(KeyCode::Key1, WorldEditTool::Select)" in world:
    errors.append("World Editor still owns a duplicate numeric tool-key authority")

pixel = read("apps/haven_editor_native/src/app/pixel_studio_input.rs")
if "shift_down && is_key_pressed(KeyCode::F)" not in pixel:
    errors.append("Pixel frame-document shortcut still collides with universal Fill")

animation = read("apps/haven_editor_native/src/app/animation_studio_input.rs")
if "shift && is_key_pressed(KeyCode::A)" not in animation:
    errors.append("Animation add-frame shortcut still collides with universal Anchor")

if errors:
    print("FAIL: W60E5 contextual CanvasWorkspace workflow")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W60E5 contextual CanvasWorkspace workflow")
