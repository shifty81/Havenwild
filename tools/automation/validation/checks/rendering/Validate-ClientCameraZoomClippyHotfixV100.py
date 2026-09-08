#!/usr/bin/env python3
"""Prevent constant-only camera zoom assertions from failing strict Clippy."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V100 failed: {message}")


def main() -> int:
    runtime_input = (ROOT / "crates/haven_game/src/runtime_input.rs").read_text(encoding="utf-8")
    registry = (ROOT / "tools/automation/validation/validate.py").read_text(encoding="utf-8")

    require(
        "assert!(RUNTIME_CAMERA_DEFAULT_ZOOM > 1.15);" not in runtime_input,
        "constant-only runtime zoom assertion still triggers clippy::assertions_on_constants",
    )
    require(
        "let zoomed = camera_zoom_after_wheel(RUNTIME_CAMERA_DEFAULT_ZOOM, 1.0);" in runtime_input,
        "camera zoom regression test no longer evaluates the production zoom function",
    )
    require(
        "assert!(zoomed > RUNTIME_CAMERA_DEFAULT_ZOOM);" in runtime_input,
        "camera zoom regression test does not verify wheel-up zoom behavior",
    )
    require(
        "assert!(zoomed > 1.15);" in runtime_input,
        "closer-than-legacy default zoom regression check is missing",
    )
    require(
        "Validate-ClientCameraZoomClippyHotfixV100.py" in registry,
        "V100 is not registered",
    )
    print("V100 client camera zoom Clippy hotfix passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
