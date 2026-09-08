#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def require(path: str, needles: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"{path} missing required editor-stability markers: {missing}")


def main() -> int:
    require(
        "apps/haven_editor_native/src/app/mod.rs",
        [
            "new_without_textures",
            "load_editor_assets",
            "--safe-mode",
            "catch_unwind",
            "draw_fault_screen",
            "HAVENWILD_EDITOR_HIGH_DPI",
        ],
    )
    require(
        "apps/haven_editor_native/src/app/canvas_view.rs",
        [
            "preview_grid_dimensions",
            "Downsample the preview",
            "scene_preview_grid_is_bounded_for_large_scene_cards",
        ],
    )
    require(
        "apps/haven_editor_native/src/app/world_surface_editor.rs",
        ["rects_intersect", "world_preview_step", "draw_scene_surface_into_rect"],
    )
    require(
        "apps/haven_editor_native/src/app/draw.rs",
        ["gl_use_default_material", "Keep all overlay chrome on the default screen pipeline"],
    )
    require(
        "apps/haven_editor_native/src/app/pixel_studio.rs",
        ["library_loaded", "Do not recursively scan", "library: Vec::new()"],
    )
    require(
        "apps/haven_editor_native/src/app/animation_studio.rs",
        ["library_loaded", "startup independent", "library: Vec::new()"],
    )
    require(
        "crates/haven_pixel/src/library.rs",
        ["HAVENWILD_PIXEL_SCAN_EXTERNAL", "scan_external"],
    )
    require(
        "apps/haven_editor_native/src/main.rs",
        ["Backtrace::force_capture", "haven_editor_native_crash.log", "working directory"],
    )
    require("tools/build/Build.sh", ["editor-safe", "cargo run native editor safe mode"])
    require("tools/build/dev.sh", ["editor-safe", "Run native editor in safe mode"])
    require("tools/automation/packaging/Create-SourceOnlyRollup.py", ["EXCLUDED_DIRS", '"assets"'])
    print("Native editor startup/render stability V105 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
