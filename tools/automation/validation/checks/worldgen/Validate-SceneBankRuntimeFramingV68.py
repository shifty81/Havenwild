#!/usr/bin/env python3
from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[5]
errors = []

def read(rel: str) -> str:
    path = root / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
editor_types = read("apps/haven_editor_native/src/app/editor_types.rs")
input_rs = read("apps/haven_editor_native/src/app/input.rs")
bank_rs = read("apps/haven_editor_native/src/app/scene_bank_workspace.rs")
controller = read("apps/haven_editor_native/src/app/canvas_controller.rs")
runtime_config = read("crates/haven_game/src/runtime_config.rs")
runtime_input = read("crates/haven_game/src/runtime_input.rs")
runtime_nav = read("crates/haven_game/src/runtime_scene_navigation.rs")
runtime_draw = read("crates/haven_game/src/runtime_draw.rs")
sim = read("crates/haven_sim/src/lib.rs")
game_main = read("crates/haven_game/src/main.rs")

checks = {
    "Game Canvas scene identities": all(marker in editor_types for marker in [
        '"Game Canvas — World"', '"Game Canvas — Scene Library"', '"Game Canvas — Scene"'
    ]),
    "scene library module": "mod scene_bank_workspace;" in mod_rs,
    "scene library keyboard/list routing": "EditorViewportMode::SceneBank" in input_rs and "cycle_scene_bank_selection" in input_rs,
    "scene library fixed collection drawing": "draw_scene_bank_workspace" in bank_rs and "scene_library_layout" in bank_rs and "scene_library_card_rect" in bank_rs,
    "scene library selection and opening": "handle_scene_bank_canvas_click" in bank_rs and "open_selected_scene_bank_scene" in bank_rs,
    "scene library owns no camera navigation": "EditorViewportMode::SceneBank => false" in controller,
    "scene library excluded from view controls": "EditorViewportMode::SceneBank" not in controller[controller.find('draw_canvas_view_controls_overlay'):controller.find('handle_canvas_view_controls_click')],
    "bounded runtime camera zoom": "RUNTIME_CAMERA_MIN_ZOOM" in runtime_config and "RUNTIME_CAMERA_MAX_ZOOM" in runtime_config and "RUNTIME_CAMERA_ZOOM_STEP" in runtime_config,
    "runtime zoom owns a bounded pixel-perfect path": "handle_client_camera_zoom_input" in runtime_input and "pixel_perfect_camera_zoom" in runtime_input and "client_camera_zoom_is_bounded" in runtime_input,
    "scene edge camera clamp": "clamp_camera_center_to_scene" in runtime_nav and "camera_stops_at_scene_edges" in runtime_nav,
    "dark night overlay": "night * 0.72" in runtime_draw,
    "lighting before ui": runtime_draw.find("self.draw_lighting_overlay();") < runtime_draw.find("self.draw_ui();"),
    "smooth night curve": "linear * linear * (3.0 - 2.0 * linear)" in sim,
}
for name, ok in checks.items():
    if not ok:
        errors.append(name)

if "scene_bank_canvas: CanvasCameraState" in mod_rs:
    errors.append("Scene Library still owns retired CanvasCameraState")

contract_path = root / "content/editor/world_canvas/world_canvas_scene_bank_contract_v0_1.json"
try:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    bank = contract["sceneBank"]
    if not bank.get("dedicatedWorkspace"):
        errors.append("scene library contract does not expose the dedicated collection workspace")
    if bank.get("infiniteCanvas"):
        errors.append("scene library contract incorrectly restores an infinite canvas")
    if bank.get("supportsZoomAndPan"):
        errors.append("scene library contract incorrectly restores zoom/pan")
    if bank.get("layout") != "adaptive_fixed_card_collection":
        errors.append("scene library contract lacks adaptive fixed-card authority")
except Exception as exc:
    errors.append(f"invalid scene library contract: {exc}")


if errors:
    print("Scene Library / runtime framing validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("Scene Library / runtime framing validation passed.")
print("- Scene Library is an adaptive screen-space collection with no hidden camera")
print("- opened scenes remain Game Canvas documents; runtime framing stays independent")
