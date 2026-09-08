#!/usr/bin/env python3
"""Validate A14Z aspect-correct Palette previews and icon-first Tool Rail buttons."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")

def need(rel: str, *markers: str) -> str:
    text = read(rel)
    for marker in markers:
        if marker not in text:
            errors.append(f"{rel} missing marker {marker!r}")
    return text

browser = need(
    "apps/haven_editor_native/src/app/asset_browser_ui.rs",
    "fn fit_preview_rect",
    "square_atlas_cell_stays_square_in_wide_palette_card",
    "wide_atlas_slice_preserves_source_aspect_ratio",
)
atlas = need(
    "apps/haven_editor_native/src/app/atlas_render.rs",
    "fit_preview_rect(source.w, source.h, rect)",
)
if atlas.count("fit_preview_rect(source.w, source.h, rect)") < 2:
    errors.append("all atlas-backed Palette thumbnail paths must use aspect-fit preview geometry")

palette = need(
    "apps/haven_editor_native/src/app/brush_palette_drawer.rs",
    "BRUSH_PALETTE_TARGET_CARD_W",
    "brush_palette_columns",
    "brush_palette_card_rect",
    "brush_palette_visible_capacity",
    "wide_bottom_palette_uses_dense_horizontal_cards",
)
rail = need(
    "apps/haven_editor_native/src/app/canvas_tool_rack.rs",
    "centered_icon_rect",
    "draw_brush_mode_icon",
    "draw_brush_source_icon",
    "draw_palette_icon",
    "draw_chevron_icon",
    'draw_editor_widget_tone(button, "", active, tone)',
)
for stale in ["short_brush_mode_label", "short_source_label", '"Pal"']:
    if stale in rail:
        errors.append(f"Tool Rail still uses compressed text-button fallback: {stale}")

layers = need(
    "apps/haven_editor_native/src/app/canvas_layers.rs",
    "CANVAS_TOOL_RACK_WIDTH: f32 = 54.0",
    "draw_layer_chevron_icon",
    "draw_layer_scroll_icon",
)

build = read("tools/build/Build.sh")
if "Validate-PalettePreviewIconButtonsA14Z.py" not in build:
    errors.append("A14Z palette/icon validator is not registered in the Windows Full Quality Gate")

if errors:
    print("A14Z Palette Preview + Icon Buttons validation FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("PASS: A14Z Palette Preview + Icon Buttons")
print("- atlas-backed thumbnails preserve source aspect ratio instead of stretching into wide cards")
print("- bottom Palette uses denser horizontal production cards")
print("- Tool Rail actions/source/modes/palette are icon-first bounded buttons with tooltips")
print("- layer rail chrome uses vector chevrons instead of font-glyph arrows")
