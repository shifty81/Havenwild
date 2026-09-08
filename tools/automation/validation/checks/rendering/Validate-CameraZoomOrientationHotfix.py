#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


canvas_camera = read("apps/haven_editor_native/src/app/canvas_camera.rs")
canvas_controller = read("apps/haven_editor_native/src/app/canvas_controller.rs")
runtime_input = read("crates/haven_game/src/runtime_input.rs")
runtime_camera = read("crates/haven_game/src/runtime_scene_navigation.rs")
contract_text = read("content/editor/canvas/camera_zoom_orientation_hotfix_contract_v0_1.json")

checks = [
    ("zoom_target: f32", canvas_camera, "editor canvas has no smoothed zoom target"),
    ("normalize_wheel_delta(raw_wheel)", canvas_camera, "editor wheel input is not normalized proportionally"),
    ("raw.clamp(-1.0, 1.0)", canvas_camera, "editor wheel input is not bounded"),
    ("CANVAS_MIN_ZOOM: f32 = 0.25", canvas_camera, "editor minimum zoom guard is missing"),
    ("CANVAS_MAX_ZOOM: f32 = 3.0", canvas_camera, "editor maximum zoom guard is missing"),
    ("zoom_out_step()", canvas_controller, "editor toolbar bypasses the zoom target"),
    ("zoom: editor_camera_zoom(display_rect)", canvas_camera, "editor camera does not use the explicit orientation-safe zoom"),
    ("editor_camera_matches_runtime_positive_y_orientation", canvas_camera, "editor positive-Y orientation regression test is missing"),
    ("zoom_in_step()", canvas_controller, "editor toolbar bypasses the zoom target"),
    ("RUNTIME_CAMERA_ZOOM", runtime_camera, "runtime camera does not use the fixed gameplay zoom"),
    ("2.0 * RUNTIME_CAMERA_ZOOM / visible.y", runtime_camera, "runtime camera does not preserve screen-style +Y-down orientation"),
    ("clamp_camera_center_to_scene", runtime_camera, "runtime camera is not clamped to scene bounds"),
]
for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

if "Camera2D::from_display_rect" in canvas_camera:
    errors.append("editor camera still uses the orientation-flipping from_display_rect helper")

for rel, text in [
    ("canvas_camera.rs", canvas_camera),
    ("runtime_input.rs", runtime_input),
]:
    if ".signum()" in text:
        errors.append(f"{rel} still expands residual wheel input with signum()")


if "camera_zoom_target" in runtime_input or "normalize_runtime_wheel" in runtime_input:
    errors.append("runtime still exposes player-controlled zoom input")

if contract_text:
    try:
        contract = json.loads(contract_text)
    except Exception as exc:
        errors.append(f"invalid camera hotfix contract: {exc}")
    else:
        if contract.get("schema") != "havenwild.camera_zoom_orientation_hotfix.v0_1":
            errors.append("camera hotfix contract schema mismatch")
        for key in (
            "fractionalWheelInput",
            "boundedEditorZoom",
            "smoothedEditorZoom",
            "fixedRuntimeZoom",
            "runtimeYDownOrientation",
            "editorRuntimeOrientationParity",
            "runtimeSceneEdgeClamp",
        ):
            if contract.get("requirements", {}).get(key) is not True:
                errors.append(f"camera hotfix contract does not require {key}")

if errors:
    print("Camera zoom/orientation hotfix validation failed:")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("Camera zoom/orientation hotfix validation passed.")
