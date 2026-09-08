#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5]
errors = []


def require(rel: str) -> str:
    path = root / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


app_mod = require("apps/haven_editor_native/src/app/mod.rs")
input_view = require("apps/haven_editor_native/src/app/input.rs")
canvas_controller = require("apps/haven_editor_native/src/app/canvas_controller.rs")
draw_view = require("apps/haven_editor_native/src/app/draw.rs")
render_helpers = require("apps/haven_editor_native/src/app/render_helpers.rs")
scene_authoring = require("apps/haven_editor_native/src/app/scene_authoring.rs")
camera = require("apps/haven_editor_native/src/app/canvas_camera.rs")
canvas_view = require("apps/haven_editor_native/src/app/canvas_view.rs")
world_surface = require("apps/haven_editor_native/src/app/world_surface_editor.rs")
editor_types = require("apps/haven_editor_native/src/app/editor_types.rs")
readme = require("README.md")
doc = require("docs/editor/PERMANENT_CANVAS_TOOLING_PASS47.md")
main = "\n".join(
    (app_mod, editor_types, input_view, canvas_controller, draw_view, render_helpers, scene_authoring)
)
combined_editor = "\n".join((main, camera, canvas_view, world_surface))

checks = [
    ("mod canvas_camera;", main, "native editor does not load the canvas camera module"),
    ("mod canvas_view;", main, "native editor does not load the canvas view module"),
    ("scene_canvas: CanvasCameraState", main, "Scene Map does not own persistent canvas state"),
    ("world_canvas: CanvasCameraState", main, "Overworld Layout does not own persistent canvas state"),
    ("scene_bank_canvas: CanvasCameraState", main, "Scene Bank does not own persistent canvas state"),
    ("SceneEditTool::Select", main, "Select tool missing"),
    ("SceneEditTool::Paint", main, "Paint tool missing"),
    ("SceneEditTool::Place", main, "Place tool missing"),
    ("SceneEditTool::Erase", main, "Erase tool missing"),
    ("SceneEditTool::Pan", main, "Pan tool missing"),
    ("self.set_scene_edit_tool(SceneEditTool::Place);", main, "object/transition content does not activate Place"),
    ("self.set_scene_edit_tool(SceneEditTool::Paint);", main, "terrain/zone content does not activate Paint"),
    ("draw_scene_grid_overlay", main, "visible Scene Map tile grid missing"),
    (
        "const WORLD_SURFACE_PARTITION_W: f32 = MAP_W as f32;",
        world_surface,
        "runtime-width world partition geometry missing",
    ),
    (
        "const WORLD_SURFACE_PARTITION_H: f32 = MAP_H as f32;",
        world_surface,
        "runtime-height world partition geometry missing",
    ),
    ("world_scene_grid_rect", world_surface, "global world snapped geometry missing"),
    ("CanvasToolbarKind::SceneBank", canvas_view, "dedicated Scene Bank canvas toolbar missing"),
    ("mod scene_bank_workspace;", main, "dedicated Scene Bank workspace module missing"),
    ("zoom: editor_camera_zoom(display_rect)", camera, "orientation-safe canvas camera zoom missing"),
    ("camera.viewport = Some", camera, "camera viewport clipping missing"),
    ("screen_to_world", camera, "camera-derived hit testing missing"),
    ("self.pan += before - after", camera, "cursor-centered zoom correction missing"),
    ("MouseButton::Middle", camera, "middle-button pan missing"),
    ("KeyCode::Space", camera, "temporary Space-drag pan missing"),
    ("set_camera(&camera);", world_surface, "world canvas does not activate its clipped camera"),
    ("set_default_camera();", world_surface, "world canvas does not restore screen-space UI rendering"),
    ("Native Editor Canvas Controls", readme, "README canvas controls missing"),
    ("Permanent Canvas Tooling", doc, "Pass 47 documentation title missing"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

for forbidden, message in [
    ("world_canvas_zoom", "legacy raw world zoom field remains"),
    ("struct WorldCanvasLayout", "legacy screen-space world canvas layout remains"),
    ("SceneEditTool::Tile", "legacy ambiguous Tile tool remains"),
    ("SceneEditTool::Object", "legacy ambiguous Object tool remains"),
    ("Enter or Space to apply", "Space still conflicts with temporary canvas pan"),
]:
    if forbidden in combined_editor:
        errors.append(message)

if "let column = index % 3;" not in canvas_view:
    errors.append("content palette is not normalized to a uniform three-column grid")

if errors:
    print("Permanent canvas tooling validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Permanent canvas tooling validation passed.")
