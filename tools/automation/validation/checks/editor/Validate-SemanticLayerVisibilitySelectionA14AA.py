#!/usr/bin/env python3
"""Validate A14AA semantic layer visibility and independent multi-selection authority."""
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

mod = need(
    "apps/haven_editor_native/src/app/mod.rs",
    "canvas_selected_layer_kinds",
    "canvas_hidden_layer_kinds",
)
for stale in ["world_show_objects", "world_show_zones", "world_show_structural_levels"]:
    if stale in mod:
        errors.append(f"legacy monolithic world visibility authority remains: {stale}")

layers = need(
    "apps/haven_editor_native/src/app/canvas_layers.rs",
    "canvas_layer_kind_for_surface_tile",
    "canvas_layer_kind_for_world_object",
    "canvas_layer_kind_for_stamp",
    "toggle_game_canvas_layer_visibility",
    "toggle_game_canvas_layer_selection",
    "editing selection unchanged",
    "multi-select",
    "water_and_paths_do_not_collapse_into_terrain_layer",
    "structure_tiles_and_world_objects_have_independent_families",
    "stamps_follow_semantic_visibility_families",
)
if "if hovered || row.active {\n                let eye_center" in layers:
    errors.append("visibility control is still hover-only instead of static")

scene = need(
    "apps/haven_editor_native/src/app/scene_render_helpers.rs",
    "SceneCanvasLayerVisibility",
    "visibility.tile_visible(tile)",
    "visibility.structural_levels",
    "visibility.objects_props",
    "visibility.structures",
    "visibility.stamp_visible(stamp, stamp_registry)",
    "if !visibility.object_visible(object.kind)",
)
inspector = need(
    "apps/haven_editor_native/src/app/object_inspector.rs",
    "canvas_layer_kind_for_stamp",
    "if !self.canvas_layer_kind_visible(layer)",
)
views = need(
    "apps/haven_editor_native/src/app/draw_scene_views.rs",
    "let scene_visibility = SceneCanvasLayerVisibility",
    "let show_structures = scene_visibility.structures",
    "visibility: scene_visibility",
    "if show_structures",
    "canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Water)",
    "canvas_layer_kind_visible(canvas_layers::CanvasLayerKind::Structures)",
)
if views:
    snapshot = views.find("let scene_visibility = SceneCanvasLayerVisibility")
    cache_borrow = views.find("let cache = self")
    if snapshot < 0 or cache_borrow < 0 or snapshot > cache_borrow:
        errors.append("scene semantic visibility must be snapshotted before mutable autotile cache borrowing")

world = need(
    "apps/haven_editor_native/src/app/world_surface_editor.rs",
    "world_surface_tile_visible",
    "world_object_layer_visible",
    "show_water",
    "show_structures",
    "show_vegetation",
    "show_resources",
)
toolbar = need(
    "apps/haven_editor_native/src/app/autotile_authoring.rs",
    "canvas_layer_kind_visible(super::canvas_layers::CanvasLayerKind::Zones)",
    "toggle_game_canvas_layer_visibility(super::canvas_layers::CanvasLayerKind::Zones)",
    "toggle_game_canvas_layer_visibility(super::canvas_layers::CanvasLayerKind::Links)",
)


rack = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
if "set_game_canvas_layer_visibility(super::canvas_layers::CanvasLayerKind::Collision, true)" in rack:
    errors.append("selecting the Collision tool still forces visibility instead of preserving independent visibility state")
if "CanvasLayerKind::Collision => self.set_game_canvas_layer_visibility(CanvasLayerKind::Collision, true)" in layers:
    errors.append("layer/shortcut selection still forces Collision visibility")

build = read("tools/build/Build.sh")
if "Validate-SemanticLayerVisibilitySelectionA14AA.py" not in build:
    errors.append("A14AA semantic layer validator is not registered in the Windows Full Quality Gate")

if errors:
    print("A14AA Semantic Layer Visibility/Selection validation FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("PASS: A14AA Semantic Layer Visibility + Multi-Selection")
print("- Water, paths, structures, terrain, vegetation, resources and props use semantic render families")
print("- visibility controls are static and independent from editing selection")
print("- layer-name clicks support additive/toggle multi-selection")
print("- building previews obey Structures & Buildings visibility")
print("- legacy monolithic world object/zones/structural visibility flags are retired")
