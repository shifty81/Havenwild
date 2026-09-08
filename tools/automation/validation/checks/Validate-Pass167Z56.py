#!/usr/bin/env python3
"""Focused static validation for Pass 167Z56.

This validator checks the checked-in authoritative sources and generated title
hover asset. It never edits project source.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[4]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(rel: str) -> str:
    path = ROOT / rel
    require(path.is_file(), f"missing required file: {rel}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    hover_path = ROOT / "content/ui/havenwild_title_button_hover.png"
    require(hover_path.is_file(), "missing organic title hover overlay")
    with Image.open(hover_path) as image:
        require(image.size == (1672, 941), f"unexpected hover image size: {image.size}")
        require(image.mode == "RGBA", f"hover image must be RGBA, got {image.mode}")
        alpha = image.getchannel("A")
        extrema = alpha.getextrema()
        require(extrema[0] == 0 and extrema[1] >= 180, f"hover alpha must contain transparent and strongly visible pixels: {extrema}")
        occupied = alpha.getbbox()
        require(occupied is not None, "hover overlay is fully transparent")
        # Organic masks occupy a minority of the full title image and must not
        # become a full-screen or rectangular full-alpha overlay.
        opaque_pixels = sum(1 for value in alpha.get_flattened_data() if value > 0)
        require(40_000 < opaque_pixels < 450_000, f"implausible hover alpha coverage: {opaque_pixels}")

    draw_source = read("crates/haven_game/src/client_character_frontend_draw.rs")
    start = draw_source.index("pub(crate) fn draw_title_menu_hover(")
    end = draw_source.index("pub(crate) fn title_continue_visual_source()", start)
    hover_body = draw_source[start:end]
    require("draw_texture_ex(" in hover_body, "title hover does not draw the organic overlay texture")
    require("draw_rectangle(" not in hover_body, "title hover still contains a rectangular fill")
    require("draw_rectangle_lines(" not in hover_body, "title hover still contains a rectangular outline")
    require("destination.y += 2.0" in hover_body, "pressed-state offset is missing")

    frontend = read("crates/haven_game/src/client_frontend.rs")
    require("const FRONTEND_MUSIC_VOLUME: f32 = 0.40;" in frontend, "frontend music is not fixed at 40 percent")
    require("play_sound(" in frontend and "stop_sound(" in frontend, "frontend music lifecycle is not active")
    require("havenwild_title_button_hover.png" in frontend, "frontend does not load the organic hover overlay")
    require(frontend.count("draw_title_menu_hover(") >= 6, "all six title controls must use organic hover rendering")

    audio_script = read("tools/automation/audio/Ensure-FrontendMusicV167Z56.py")
    require("8b3ea6ecdc3af69847c20684dca5a5ad4921bb4b41cc2563811f1f7ac50af489" in audio_script,
            "frontend music bootstrap is not checksum locked")
    require("Repair-" not in audio_script, "audio bootstrap must not rewrite Rust")

    build_sh = read("tools/build/Build.sh")
    require("Active Rust sources are authoritative; legacy build-time source rewriters are disabled" in build_sh,
            "direct-source authority marker is missing")
    require("Ensure-FrontendMusicV167Z56.py" in build_sh, "Bash build does not verify frontend music")

    transition = read("crates/haven_game/src/terrain_transition_draw.rs")
    require("WaterRenderMask" in transition, "dedicated water render mask is not used")
    require("draw_full_depth_cell" in transition, "complete authored depth cells are not used")
    require("common_depth_masks_select_complete_authored_cells" in transition,
            "rounded depth full-cell regression coverage is missing")
    require("drew_any || drew_inner" in transition, "depth drawing result is not combined without bitwise boolean logic")

    terrain = read("crates/haven_game/src/terrain_render.rs")
    require("resolve_water_render_mask" in terrain, "terrain renderer does not resolve dedicated water masks")
    require("draw_direct_water_depth_rim(texture, px, py, water_mask)" in terrain,
            "terrain renderer does not submit the dedicated rounded depth rim")

    for rel in (
        "content/ui/havenwild_title_button_hover.png.provenance.json",
        "content/audio/music/frontend/Harp.ogg.provenance.json",
    ):
        data = json.loads(read(rel))
        require(isinstance(data, dict), f"invalid provenance object: {rel}")

    print("Pass 167Z56 organic title, frontend music, and rounded depth rendering validated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Pass 167Z56 validation FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
