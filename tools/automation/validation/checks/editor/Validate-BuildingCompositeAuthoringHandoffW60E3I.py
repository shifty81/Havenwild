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

prepared = read("apps/haven_editor_native/src/app/prepared_canvas_composition.rs")
bridge = read("apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs")
pixel = read("apps/haven_editor_native/src/app/pixel_studio.rs")
render = read("apps/haven_editor_native/src/app/pixel_studio_render.rs")
input_rs = read("apps/haven_editor_native/src/app/pixel_studio_input.rs")
color = read("apps/haven_editor_native/src/app/pixel_color_panel.rs")
shared = read("apps/haven_editor_native/src/app/shared_palette.rs")
sprite = read("apps/haven_editor_native/src/app/sprite_workspace.rs")

for marker in [
    "prepare_building_canvas_composition",
    "resolved_published_source_path",
    "definition.source_path.clone()",
    "Building Composite authoring is reconstructed from published",
    "Clean composite authority is independent of Scene Editor cutaway/inside",
    "BuildingInstanceViewState::for_definition(instance)",
]:
    if marker not in prepared:
        errors.append(f"clean building composition authority missing: {marker}")

# Frame rectangles must address the resolved published/runtime sheet, not provenance-only source art.
if "definition.provenance.source_path.as_ref()" in prepared:
    errors.append("prepared canvas still reads provenance.source_path directly")

for marker in [
    'scope_kind == "building_composite"',
    "prepare_building_canvas_composition",
    '"Authored Building Composite Draft"',
    '"clean_authoring_composite"',
    "rgba_fingerprint_v1",
    '"authoring_handoff_rgba_fingerprint_v1:',
    "building_composites/drafts",
    "building_composite_publish",
]:
    if marker not in bridge:
        errors.append(f"building authoring handoff contract missing: {marker}")

# Building composite must branch before the generic collision/reference authoring stack.
building_branch = bridge.find('if scope_kind == "building_composite"')
collision_stack = bridge.find('document.add_layer("Physical Collision Reference")')
if building_branch < 0 or collision_stack < 0 or building_branch > collision_stack:
    errors.append("building composite does not isolate itself before scene collision/reference layers")

for marker in [
    "active_palette",
    "add_color_to_palette",
    "maximum 24 colors",
]:
    if marker not in pixel:
        errors.append(f"document palette authority missing: {marker}")

for text, marker in [
    (shared, "+ = add color"),
    (shared, "sprite_bottom_add_swatch_rect"),
    (shared, "open_pixel_color_add_tray"),
    (color, '"Add Color to Palette"'),
    (color, "add_color_to_palette"),
    (sprite, 'draw_editor_text("+"'),
]:
    if marker not in text:
        errors.append(f"shared palette add-color workflow missing: {marker}")

if errors:
    print("FAIL: W60E3I Building Composite authoring handoff")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W60E3I Building Composite authoring handoff")
