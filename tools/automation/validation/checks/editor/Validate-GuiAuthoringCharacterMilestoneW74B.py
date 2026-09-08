#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        errors.append(f"missing {rel}")
        return ""
    return p.read_text(encoding="utf-8")

def require(rel: str, *markers: str) -> str:
    text = read(rel)
    for marker in markers:
        if marker not in text:
            errors.append(f"{rel} missing marker: {marker}")
    return text

contract_path = ROOT / "content/editor/gui/gui_authoring_character_milestone_w74b_v1.json"
try:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "havenwild.editor.gui_authoring_character_milestone.w74b.v1":
        errors.append("W74B contract schema mismatch")
    if len(contract.get("passes", [])) != 17:
        errors.append("W74B contract must enumerate W73A-W73O and W74A-W74B")
    if contract.get("lockedGeometry", {}).get("toolRail") != "dedicated left sibling column outside canvas":
        errors.append("W74B must preserve locked external Tool Rail geometry")
    if contract.get("lockedGeometry", {}).get("layers") != "dedicated sibling column immediately right of Tool Rail outside canvas":
        errors.append("W74B must preserve locked external Layers geometry")
except Exception as exc:
    errors.append(f"W74B contract invalid: {exc}")

# W73A/B/C: authority + no live legacy left-panel workflow.
authority = require(
    "apps/haven_editor_native/src/app/gui_authority.rs",
    "GUI_WORKFLOW_AUTHORITIES",
    'id: "tool_selection", owner: "canvas.tool_rail"',
    'id: "layer_management", owner: "canvas.layers"',
    'id: "asset_browser", owner: "right_dock.assets"',
    'id: "outliner", owner: "right_dock.outliner"',
    "RETIRED_GUI_AUTHORITIES",
    "every_workflow_has_one_owner",
)
workspace = require(
    "apps/haven_editor_native/src/app/workspace_shell.rs",
    "left_panel_visible: false",
    "self.left_panel_visible = false",
    "asset_shelf_open: false",
    "AssetBrowserScope",
    "shared_palette_visible",
)
for rel in [
    "apps/haven_editor_native/src/app/draw.rs",
    "apps/haven_editor_native/src/app/input.rs",
    "apps/haven_editor_native/src/app/right_dock.rs",
]:
    text = read(rel)
    for forbidden in [
        "draw_universal_asset_shelf(", "handle_universal_asset_shelf_click(",
        "draw_scene_dock(", "handle_scene_dock_click(",
        "draw_scene_toolrail(", "handle_scene_toolrail_click(",
        "draw_asset_intake(", "handle_asset_intake_click(",
        "draw_asset_library(", "handle_asset_library_click(",
    ]:
        if forbidden in text:
            errors.append(f"live shell file {rel} reintroduces retired GUI path {forbidden}")

# W73D/E: one command vocabulary and nine menus.
registry = require(
    "apps/haven_editor_native/src/app/command_registry.rs",
    "pub(crate) enum EditorCommandId",
    "FILE_COMMANDS", "EDIT_COMMANDS", "VIEW_COMMANDS", "WORLD_COMMANDS",
    "SCENE_COMMANDS", "ASSET_COMMANDS", "BUILD_COMMANDS", "TOOLS_COMMANDS", "HELP_COMMANDS",
    "nine_menu_groups_are_registered",
)
menu = require(
    "apps/haven_editor_native/src/app/editor_menu.rs",
    "const ALL: [Self; 9]",
    "Self::World", "Self::Scene", "Self::Asset", "Self::Build",
    "execute_editor_command",
)
if "Self::Run" in menu:
    errors.append("retired Run menu returned after Build menu normalization")

# W73F/G: locked sibling panels and canvas-only zoom.
require(
    "apps/haven_editor_native/src/app/canvas_layers.rs",
    "Tool Rail is a dedicated left column outside",
    "Layers is the dedicated panel immediately to",
    "self.main_viewport_rect()",
    "PANEL_GAP",
)
require(
    "apps/haven_editor_native/src/app/draw.rs",
    "self.draw_canvas_tool_rack();",
    "self.draw_canvas_layer_rail();",
    "self.draw_canvas_view_controls_overlay();",
)
require(
    "apps/haven_editor_native/src/app/canvas_view.rs",
    "only zoom/view chrome",
    "upper-right corner",
)

# W73H/I/J: grouping + sole bottom options + brush inventory.
rack = require(
    "apps/haven_editor_native/src/app/canvas_tool_rack.rs",
    "visible_tool_entries",
    "TOOL_GROUP_GAP",
    "Tool-specific options are always bottom-anchored",
    "direct_visual_tool_uses_brush_slider",
    "PixelBrushKind::Cross", "PixelBrushKind::Ring", "PixelBrushKind::Noise",
)
pixel_render = require(
    "apps/haven_editor_native/src/app/pixel_studio_render.rs",
    "Tool-specific options are intentionally NOT duplicated here",
    "shared_palette_visible",
    "shared_palette_hide_rect",
)
if "draw_sprite_tool_options(" in pixel_render:
    errors.append("Pixel palette still duplicates Tool Rail options")
brush = require(
    "crates/haven_pixel/src/brush.rs",
    "pub const ALL: [Self; 9]",
    "Cross", "Ring", "Noise",
    "cross_brush_keeps_orthogonal_arms",
    "ring_brush_leaves_center_open_when_large_enough",
    "noise_brush_is_deterministic_in_image_space",
)

# W73K/L/M: shared palette and direct presentation-only authoring.
require(
    "apps/haven_editor_native/src/app/shared_palette.rs",
    "shared_palette_visible",
    "shared_palette_collapsed_rect",
    "shared_palette_hide_rect",
    "draw_sprite_bottom_dock",
    "handle_pixel_color_controls",
)
direct = require(
    "apps/haven_editor_native/src/app/direct_visual_authoring.rs",
    "CanvasLayerKind::AuthoredPixels",
    "UniversalTool::Paint | UniversalTool::Erase | UniversalTool::Pick",
    "SceneVisualOverride::new",
    "scene.dimensions",
    "dimensions.width",
    "dimensions.height",
    "gameplay semantics unchanged",
)
for forbidden in ["set_tile(", "set_collision", "structural_level", "semantic_layers"]:
    if forbidden in direct:
        errors.append(f"direct visual authoring must not mutate gameplay semantics: {forbidden}")
require(
    "apps/haven_editor_native/src/app/input.rs",
    "update_direct_visual_authoring",
    "handle_shared_palette_click",
)

# W73N: one Assets dock, with broad and contextual views.
right = require(
    "apps/haven_editor_native/src/app/right_dock.rs",
    "AssetBrowserScope::AllProject",
    "AssetBrowserScope::ALL",
    "self.draw_asset_palette(body)",
    "draw_right_dock_assets",
)

# W74A/B: real character recipe workspace, layered static preview and publish.
character = require(
    "apps/haven_editor_native/src/app/character_studio.rs",
    "New Player Recipe", "New NPC Recipe",
    "cycle_direction", "cycle_action", "cycle_palette_variant",
    "move_selected_recipe_layer", "cycle_selected_recipe_layer",
    "sync_assembled_preview", "assembled_preview_layers",
    "Assembled static preview",
    "Publish Character Preset", "publish_recipe_preset",
    "CHARACTER_STUDIO_PRESET_SCHEMA",
    "draft_recipe_round_trips",
)
if "Assembled animated preview" in character:
    errors.append("Character Studio must not claim unsupported animated composition")

require(
    "tools/automation/validation/checks/editor/Validate-CanvasChromeCompileRepairW72D1.py",
    "W72D: canvas_host_rect already begins after the dedicated Tool Rail",
)

# Historical validators that are part of the Full gate must know this superseding authority.
require(
    "tools/automation/validation/checks/editor/Validate-EditorUiAuthorityW60B.py",
    "w74b_contract",
    "self.canvas_host_rect()",
)
require(
    "tools/automation/validation/checks/editor/Validate-EditorCommandRoutingW60E22.py",
    "gui_authoring_character_milestone_w74b_v1.json",
    "W74B command registry marker",
)
require(
    "tools/automation/validation/checks/editor/Validate-UnifiedFoundationAuthoringSoundLogicW62.py",
    "gui_authoring_character_milestone_w74b_v1.json",
    "command_registry.rs",
)
require(
    "tools/automation/validation/checks/editor/Validate-SelectionTransformGizmoW61C.py",
    "command_surface=commands if w74b else menu",
    "command_registry.rs",
)
require(
    "tools/automation/validation/checks/editor/Validate-EditorTextAuthorityW60A.py",
    "w72b_contract",
    "Dedicated Segoe UI editor font atlas.",
)
require(
    "tools/automation/validation/checks/editor/Validate-CanvasCornerLayerDockW60D.py",
    "locked_sibling_geometry",
    "W72D/W74B supersede W60D",
)
require(
    "tools/automation/validation/checks/editor/Validate-CanvasUxAssetBrowserW60C.py",
    "w74b_contract",
    "EditorCommandId::OpenAssetBrowser",
    "EditorCommandId::TogglePalette",
)
require(
    "tools/automation/validation/checks/editor/Validate-CanvasWorkspaceAuthorityW60E3.py",
    "locked_sibling_geometry",
    "self.canvas_host_rect()",
)

if errors:
    print("FAIL: W74B cumulative GUI / authoring / Character Studio milestone")
    for error in errors:
        print(" - " + error)
    sys.exit(1)
print("PASS: W74B cumulative GUI / authoring / Character Studio milestone")
