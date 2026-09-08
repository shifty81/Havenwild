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

def need(rel, *markers):
    text = read(rel)
    for marker in markers:
        if marker not in text:
            errors.append(f"{rel} missing marker: {marker}")

# A14Y one palette authority: the shell owns a reserved bottom Canvas panel;
# Pixel Studio supplies its active document palette but does not draw a second tray.
need(
    "apps/haven_editor_native/src/app/shared_palette.rs",
    "shared_palette_height",
    "draw_sprite_bottom_dock(",
    '"Palette"',
    "active_palette",
    "shared_palette_hide_rect",
)
render = read("apps/haven_editor_native/src/app/pixel_studio_render.rs")
if "draw_sprite_bottom_dock(" in render or "draw_pixel_properties_palette" in render or "draw_workspace_dock_palette" in render:
    errors.append("Pixel Studio must not restore a duplicate palette renderer outside shared_palette.rs")

# A14X restores the locked Tool Rail | Layers | Canvas sibling geometry.
# Layers reserves its own opaque panel width; the old drag-resize grip remains retired.
need(
    "apps/haven_editor_native/src/app/workspace_shell.rs",
    "canvas_layer_rail_width: 174.0",
    "clamp(132.0, 480.0)",
)
layers = read("apps/haven_editor_native/src/app/canvas_layers.rs")
for marker in ["Layers is a dedicated panel, not text painted over the world", "+ self.canvas_layer_rail_width()", "draw_canvas_layer_rail", "update_canvas_layer_resize_input"]:
    if marker not in layers:
        errors.append(f"apps/haven_editor_native/src/app/canvas_layers.rs missing marker: {marker}")
for retired in ["canvas_layer_resize_grip_rect", "draw_layer_resize_grip"]:
    if retired in layers:
        errors.append(f"retired boxed Layers resize authority restored: {retired}")

# A14 supersedes the old rectangle-manifest overview reconstruction. Complete-world
# mode must consume the same SemanticWorldBakeV1 authority as runtime, then overlay
# exact materialized exterior scenes at canonical coordinates.
need(
    "apps/haven_editor_native/src/app/world_surface_editor.rs",
    "SemanticWorldBakeV1",
    "world_archipelago_overview_bounds(bake)",
    "world_overview_landmass_at_point",
    "draw_archipelago_overview",
    "draw_semantic_world_bake",
    "materialized surface overlays",
    "Runtime semantic bake + materialized surface overlays",
)
need(
    "apps/haven_editor_native/src/app/canvas_controller.rs",
    "development_world_semantic_bake.as_ref()?",
    "world_archipelago_overview_bounds",
)
need(
    "apps/haven_editor_native/src/app/island_authoring.rs",
    "development_semantic_world_bake",
    "world_archipelago_overview_bounds(bake)",
    "self.world_show_entire_world = false;",
)
need(
    "apps/haven_editor_native/src/app/world_surface_authoring.rs",
    "Complete-world LOD is the real generated archipelago",
    "world_overview_landmass_at_point",
    "self.frame_selected_landmass();",
)
need(
    "apps/haven_editor_native/src/app/editor_menu.rs",
    "EditorCommandId::OpenWorld",
    "self.frame_entire_world();",
)
# Scene Library is now a screen-space catalog. Locating a scene must resolve its
# authoritative world assignment/rectangle and switch back into Game Canvas rather
# than owning a second overview camera or reconstructing world geography.
need(
    "apps/haven_editor_native/src/app/scene_bank_workspace.rs",
    "locate_selected_scene_in_world",
    "scene_assignments",
    "scene_rectangles",
    "Opened {name} in Game Canvas",
)
scene_library = read("apps/haven_editor_native/src/app/scene_bank_workspace.rs")
for retired in ["scene_bank_canvas: CanvasCameraState", "world_scene_overview_rect("]:
    if retired in scene_library:
        errors.append(f"Scene Library restored retired world/camera approximation authority: {retired}")
# Help copy is allowed to evolve, but the Entire-World Canvas article must keep
# communicating that the overview is backed by the real generated world rather
# than a disconnected preview/minimap authority. Do not pin validation to one
# exact sentence; that made harmless help-copy edits fail the project gate.
help_text = read("apps/haven_editor_native/src/app/editor_help.rs")
for marker in [
    "HelpPage::EntireWorldCanvas",
    'title: "Entire-World Canvas"',
]:
    if marker not in help_text:
        errors.append(f"apps/haven_editor_native/src/app/editor_help.rs missing marker: {marker}")
if not any(
    marker in help_text
    for marker in [
        "actual scene terrain",
        "authoritative scene terrain",
        "generated archipelago layout",
        "real archipelago overview",
    ]
):
    errors.append(
        "apps/haven_editor_native/src/app/editor_help.rs missing authoritative entire-world overview semantics"
    )

if errors:
    print("FAIL: W81R30R44H6 editor UX + real world view closure")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("PASS: W81R30R44H6 editor UX + real world view closure")
