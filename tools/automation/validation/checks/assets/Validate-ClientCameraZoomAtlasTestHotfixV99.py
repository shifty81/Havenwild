#!/usr/bin/env python3
"""Lock Pass 91B atlas test coordinates and client-only Alt+wheel camera zoom."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V99 failed: {message}")


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    assets = text("crates/haven_assets/src/autotile.rs")
    config = text("crates/haven_game/src/runtime_config.rs")
    main_rs = text("crates/haven_game/src/main.rs")
    input_rs = text("crates/haven_game/src/runtime_input.rs")
    nav = text("crates/haven_game/src/runtime_scene_navigation.rs")
    draw = text("crates/haven_game/src/runtime_draw.rs")
    terrain = text("crates/haven_game/src/runtime_terrain_pass.rs")
    registry = text("tools/automation/validation/validate.py")

    require("assert_eq!(entry.rect.y, 410.0);" in assets,
            "Pass 91 padded atlas test still expects the pre-inner-corner Y coordinate")
    require("RUNTIME_CAMERA_DEFAULT_ZOOM: f32 = 1.35" in config,
            "closer runtime camera default is missing")
    require("RUNTIME_CAMERA_MIN_ZOOM" in config and "RUNTIME_CAMERA_MAX_ZOOM" in config,
            "runtime camera zoom bounds are missing")
    require("camera_zoom: f32" in main_rs and "camera_zoom: RUNTIME_CAMERA_DEFAULT_ZOOM" in main_rs,
            "per-client camera zoom state is missing")
    require("handle_client_camera_zoom_input" in input_rs,
            "client camera zoom input handler is missing")
    require("KeyCode::LeftAlt" in input_rs and "KeyCode::RightAlt" in input_rs,
            "Alt modifier gate is missing")
    require("mouse_wheel().1" in input_rs,
            "client zoom does not read the wheel")
    require("reserved for the client camera" in input_rs,
            "hotbar isolation contract is missing")
    require("self.camera_zoom" in nav and "RUNTIME_CAMERA_ZOOM" not in nav,
            "scene navigation does not use the per-client zoom")
    require("self.camera_zoom" in draw and "self.camera_zoom" in terrain,
            "render culling does not use the per-client zoom")
    require("Alt+Wheel zoom" in draw, "HUD does not expose the client zoom control")
    require("Validate-ClientCameraZoomAtlasTestHotfixV99.py" in registry,
            "V99 is not registered")
    print("V99 client camera zoom and atlas test hotfix passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
