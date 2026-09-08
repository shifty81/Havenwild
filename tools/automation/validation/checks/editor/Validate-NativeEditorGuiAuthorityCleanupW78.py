#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


contract_path = ROOT / "content/editor/native_editor_gui_authority_cleanup_w78_v1.json"
try:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
except Exception as exc:
    contract = {}
    errors.append(f"invalid W78 contract: {exc}")

require(contract.get("schema") == "havenwild.editor.native_gui_authority_cleanup.w78.v1", "W78 schema mismatch")
require(contract.get("pass") == "167Z109W78", "W78 pass mismatch")
require(contract.get("pixelLayers", {}).get("duplicatePanelForbidden") is True, "duplicate Pixel layer panel must be forbidden")
require(contract.get("historicalRepairPolicy", {}).get("w60e3aCompileRepair") == "fail_closed", "W60E3A repair must fail closed")
require(contract.get("warningCleanup", {}).get("deadCodeSuppressionsAdded") is False, "W78 must not hide cleanup behind dead-code suppressions")

for rel in contract.get("retiredRuntimeModules", []):
    require(not (ROOT / rel).exists(), f"retired GUI module still exists: {rel}")

mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
for module in ["canvas_layers", "canvas_tool_rack", "pixel_layer_rail", "pixel_context_layout", "right_dock"]:
    require(f"mod {module};" in mod_rs, f"canonical module not registered: {module}")
for module in ["pixel_layer_panel", "scene_toolrail", "asset_shelf", "asset_library_panel", "asset_intake_panel"]:
    require(f"mod {module};" not in mod_rs, f"retired module returned to graph: {module}")

layers = read("apps/haven_editor_native/src/app/canvas_layers.rs")
pixel_layer_rail = read("apps/haven_editor_native/src/app/pixel_layer_rail.rs")
layer_surface = layers + "\n" + pixel_layer_rail
for token in [
    "draw_pixel_layer_footer",
    "handle_pixel_layer_footer_click",
    "document.add_layer",
    "document.duplicate_active_layer",
    "document.delete_active_layer",
    "document.move_active_layer",
    "document.merge_active_down",
    "document.set_active_layer_opacity",
    "document.toggle_active_layer_visibility",
    "document.toggle_active_layer_lock",
    "layer_rename_buffer",
    "canvas_layer_rail_expanded_width",
]:
    require(token in layer_surface, f"canonical Layers rail missing: {token}")
require("CANVAS_LAYER_RAIL_WIDTH" not in layers, "obsolete fixed layer-rail width returned")

pixel_context = read("apps/haven_editor_native/src/app/pixel_context_layout.rs")
for token in [
    "pixel_asset_tab_rect",
    "pixel_animation_tab_rect",
    "pixel_animation_onion_rect",
    "pixel_animation_focus_rect",
    "pixel_animation_save_return_rect",
    "pixel_animation_cancel_return_rect",
]:
    require(token in pixel_context, f"Pixel context layout missing {token}")

island = read("apps/haven_editor_native/src/app/island_authoring.rs")
require("focus_right_dock(RightDockTab::Assets)" in island, "World Assets context does not route to canonical right dock")
require("focus_right_dock(RightDockTab::Properties)" in island, "World Selection context does not route to canonical right dock")

types = read("apps/haven_editor_native/src/app/editor_types.rs")
input_rs = read("apps/haven_editor_native/src/app/input.rs")
world_ui = read("apps/haven_editor_native/src/app/world_surface_authoring_ui.rs")
require("WorldInspectorTab" not in types + mod_rs + world_ui, "retired WorldInspectorTab authority returned")
require("handle_scene_rectangle_inspector_click" not in input_rs, "retired SceneRectangles inspector handler returned")
require("handle_world_properties_click" in input_rs and "RightDockTab::Properties" in input_rs, "World properties are not routed through canonical right dock")

rack = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
registry = read("apps/haven_editor_native/src/app/tool_registry.rs")
for token in ["UniversalTool::Rectangle", "UniversalTool::Fill", "UniversalTool::Replace", "UniversalTool::Pick"]:
    require(token in rack + registry, f"canonical tool authority missing {token}")
for token in ["draw_tool_group_popup", "tool_group_popup_rect", "tool_group_button_rect", "draw_tooltip_for_group"]:
    require(token not in rack, f"retired tool-group popup authority remains: {token}")

layout = read("apps/haven_editor_native/src/app/pixel_studio_layout.rs")
for token in [
    "pixel_document_tabs_bar_rect",
    "pixel_zoom_out_rect",
    "pixel_zoom_label_rect",
    "pixel_zoom_in_rect",
    "pixel_one_to_one_rect",
    "pixel_frame_rect",
    "pixel_atlas_grid_rect",
    "pixel_pixel_grid_rect",
]:
    require(token not in layout, f"retired Pixel-specific canvas chrome remains: {token}")

character = read("apps/haven_editor_native/src/app/character_studio.rs")
require("CharacterStudioMode::Population" not in character and "CharacterStudioMode::Validation" not in character, "unreachable Character Studio debug modes remain")

repair = read("tools/repairs/Apply-W60E3A-CompileRepair.py")
require("retired and fail-closed" in repair, "historical W60E3A repair is not fail-closed")
require("pixel_layer_panel" not in repair, "historical repair can still recreate Pixel Layer panel imports")

# W78 removes dead code; it must not solve the warning set by adding broad new
# suppression attributes to the canonical files it touches.
for rel in [
    "apps/haven_editor_native/src/app/canvas_layers.rs",
    "apps/haven_editor_native/src/app/canvas_tool_rack.rs",
    "apps/haven_editor_native/src/app/pixel_layer_rail.rs",
    "apps/haven_editor_native/src/app/pixel_context_layout.rs",
    "apps/haven_editor_native/src/app/world_surface_authoring_ui.rs",
]:
    source = read(rel)
    require("#[expect(dead_code)]" not in source, f"dead-code expect added to {rel}")

if errors:
    print("FAIL: W78 native editor GUI authority cleanup")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS: W78 native editor GUI authority cleanup")
print("- duplicate Pixel Layer/World inspector/tool-popup authorities are absent")
print("- Pixel layer lifecycle lives in the canonical Canvas Layers rail")
print("- World context/property routing uses the canonical right dock")
print("- historical W60E3A repair is fail-closed")
