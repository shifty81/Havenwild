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

studio = read("apps/haven_editor_native/src/app/pixel_studio.rs")
for marker in [
    "pub brush_size: u8",
    "pub symmetry_horizontal: bool",
    "pub symmetry_vertical: bool",
    "brush_size: 1",
    "pub(crate) fn reset_authoring_defaults",
    "self.brush_size = 1;",
    "self.selection_mode = PixelSelectionMode::Pixels;",
    "pub(crate) fn adjust_brush_size",
    "pub(crate) fn symmetry_label",
]:
    if marker not in studio:
        errors.append(f"Pixel Studio authoring default/symmetry authority missing: {marker}")
if "PixelAssetRole::Character | PixelAssetRole::RepeatTexture => PixelSelectionMode::Frame" in studio:
    errors.append("asset role still silently forces Frame selection instead of marquee Pixels")

layout = read("apps/haven_editor_native/src/app/pixel_studio_layout.rs")
if "draw_marquee_rect" not in layout:
    errors.append("marquee geometry missing")

# W60E13 legitimately moves brush and symmetry options off the Pixel top row
# and into the shared CanvasWorkspace Tool Rail. Accept either the original
# W60E6 placement or the normalized later authority.
rack = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
render = read("apps/haven_editor_native/src/app/pixel_studio_render.rs")
legacy_options = all(marker in layout for marker in ["pixel_brush_size_rect", "pixel_symmetry_h_rect", "pixel_symmetry_v_rect"])
normalized_options = all(marker in rack for marker in ["pixel_symmetry_tool_rect", "draw_contextual_brush_slider", "draw_pixel_symmetry_popup"])
if not (legacy_options or normalized_options):
    errors.append("Pixel brush/symmetry controls have no authoritative UI placement")
for marker in ["draw_pixel_symmetry_axes", "symmetry_horizontal", "symmetry_vertical"]:
    if marker not in render:
        errors.append(f"Pixel Studio symmetry rendering missing: {marker}")

input_rs = read("apps/haven_editor_native/src/app/pixel_studio_input.rs")
for marker in [
    "flip_selection_horizontal",
    "flip_selection_vertical",
    "symmetry_horizontal = !self.pixel_studio.symmetry_horizontal",
    "symmetry_vertical = !self.pixel_studio.symmetry_vertical",
    "adjust_brush_size(-1)",
    "adjust_brush_size(1)",
    "apply_pixel_brush_segment",
    "pixel_line_points",
    "mirrored_pixel_points",
    "stamp_pixel_brush",
]:
    if marker not in input_rs:
        errors.append(f"Pixel interaction implementation missing: {marker}")

world_bridge = read("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
if world_bridge.count("self.pixel_studio.reset_authoring_defaults();") < 3:
    errors.append("world/scene/building Pixel Studio handoffs do not reset to 1px marquee authoring defaults")

animation_bridge = read("apps/haven_editor_native/src/app/pixel_animation_bridge.rs")
if "self.pixel_studio.reset_authoring_defaults();" not in animation_bridge:
    errors.append("animation Pixel Studio handoff does not reset authoring defaults")

if errors:
    print("FAIL: W60E6 Pixel interaction + symmetry workflow")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W60E6 Pixel interaction + symmetry workflow")
