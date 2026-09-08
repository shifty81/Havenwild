#!/usr/bin/env python3
"""Validate Pass 167Z109W76A-T native-editor GUI closure capabilities.

This validator intentionally checks current capability boundaries instead of
historical UI literals. W76 supersedes several older magic-offset and retired-panel
implementations while preserving the established Tool Rail | Layers | Canvas |
Right Dock architecture.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
ERRORS: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        ERRORS.append(f"missing required file: {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def require(text: str, needles: list[str], context: str) -> None:
    for needle in needles:
        if needle not in text:
            ERRORS.append(f"{context}: missing capability marker {needle!r}")


def require_absent(text: str, needles: list[str], context: str) -> None:
    for needle in needles:
        if needle in text:
            ERRORS.append(f"{context}: retired/duplicate marker still active {needle!r}")


def require_file_absent(rel: str) -> None:
    if (ROOT / rel).exists():
        ERRORS.append(f"retired GUI module still present: {rel}")


def main() -> int:
    contract_path = ROOT / "content/editor/native_editor_gui_closure_w76_v1.json"
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:
        ERRORS.append(f"could not load W76 contract: {exc}")
        contract = {}
    if contract.get("schema") != "havenwild.native_editor_gui_closure.w76.v1":
        ERRORS.append("W76 contract schema mismatch")

    mod_rs = read("apps/haven_editor_native/src/app/mod.rs")
    workspace = read("apps/haven_editor_native/src/app/canvas_workspace.rs")
    shell = read("apps/haven_editor_native/src/app/workspace_shell.rs")
    chrome = read("apps/haven_editor_native/src/app/workspace_chrome.rs")
    controller = read("apps/haven_editor_native/src/app/canvas_controller.rs")
    controls = read("apps/haven_editor_native/src/app/gui_controls.rs")
    palette = read("apps/haven_editor_native/src/app/shared_palette.rs")
    sprite_workspace = read("apps/haven_editor_native/src/app/sprite_workspace.rs")
    color = read("apps/haven_editor_native/src/app/pixel_color_panel.rs")
    tabs = read("apps/haven_editor_native/src/app/document_tabs.rs")
    pixel_input = read("apps/haven_editor_native/src/app/pixel_studio_input.rs")
    pixel_render = read("apps/haven_editor_native/src/app/pixel_studio_render.rs")
    pixel_doc = read("crates/haven_pixel/src/document.rs")
    character = read("apps/haven_editor_native/src/app/character_studio.rs")
    animation = read("apps/haven_editor_native/src/app/animation_studio.rs")
    animation_input = read("apps/haven_editor_native/src/app/animation_studio_input.rs")
    tools = read("apps/haven_editor_native/src/app/tool_registry.rs")
    direct_visual = read("apps/haven_editor_native/src/app/direct_visual_authoring.rs")

    # W76A/B/I: shared vertical geometry and protected tab ownership.
    require(mod_rs, ["mod canvas_workspace;", "mod document_tabs;", "mod gui_controls;", "mod asset_hot_reload;"], "module graph")
    require(workspace, [
        "DOCUMENT_TAB_H", "CONTEXT_TOOLBAR_H", "RULER_H", "RULER_W",
        "pub document_tabs: Rect", "pub context_toolbar: Rect", "pub viewport: Rect",
        "ruler_and_canvas_never_overlap_document_tabs",
        "palette_reservation_never_covers_viewport",
    ], "CanvasWorkspace")
    require(shell + chrome + controller, ["canvas_workspace_layout"], "workspace layout integration")
    require(tabs, [
        "SceneDocumentUiState", "scene_document_states", "store_active_scene_document_ui_state",
        "restore_active_scene_document_ui_state", "draw_workspace_document_tabs",
        "handle_workspace_document_tabs_click", "scene_tab_window",
        "selected_scene_remains_visible_when_scene_count_exceeds_tab_limit",
    ], "DocumentTabBar")
    require(animation + animation_input, ["canvas_workspace_layout().workspace_body"], "Animation Studio protected workspace body")

    # W76C/D/E: pointer capture, real slider, continuous color drag.
    require(controls, [
        "GuiPointerCapture", "BrushSlider(Rect)", "ColorPicker(Rect)", "GuiInteractionState",
        "SliderSpec", "draw_slider", "begin_brush_slider_drag", "begin_color_picker_drag",
        "update_gui_pointer_capture", "is_mouse_button_down(MouseButton::Left)",
    ], "shared pointer/slider controls")
    require(color + controls, ["update_color_from_pointer"], "continuous color picker")
    require(mod_rs, ["gui_interaction: gui_controls::GuiInteractionState", "primary_pointer_owned_by_ui"], "EditorApp interaction ownership")

    # W76F/G/R: palette fixed-right cluster + semantic control classes.
    require(palette, [
        "sprite_bottom_foreground_color_rect", "sprite_bottom_background_color_rect",
        "sprite_bottom_swap_color_rect", "sprite_bottom_reset_color_rect",
        "shared_palette_scroll", "Swapped palette foreground/background colors",
        "Reset palette foreground/background colors", "active_palette",
    ], "shared palette")
    require(sprite_workspace, ["palette_swatches_never_enter_fixed_fg_bg_swap_reset_cluster"], "palette geometry regression")
    require(controls, [
        "GuiControlClass", "Primary", "Secondary", "Toolbar", "Toggle", "Segmented", "Quiet", "Danger",
        "draw_control",
    ], "shared GUI control hierarchy")

    # W76H/I: expanded tool registry and real transactional Pixel implementations.
    for variant in ["MagicSelect", "Ellipse", "Gradient", "Blur", "Smudge", "Lighten", "Darken"]:
        require(tools, [variant], "Tool Rail registry")
        require(pixel_doc, [variant], "PixelTool enum")
    require(pixel_doc, [
        "draw_ellipse", "magic_select_contiguous", "blur_region", "adjust_luma_region",
        "smudge_pixel", "draw_gradient", "magic_select_uses_contiguous_color_bounds",
        "blur_lighten_and_gradient_are_undoable_pixel_edits", "ellipse_draws_without_leaving_document_bounds",
    ], "Pixel Studio operations/tests")
    require(pixel_input + pixel_render, ["MagicSelect", "Gradient", "Blur", "Smudge", "Lighten", "Darken"], "Pixel Studio adapters")

    # W76J-M: Pixel remains richer multi-doc/split host while shared row is protected elsewhere.
    require(pixel_render + pixel_input + mod_rs, ["PixelStudio"], "Pixel Studio host")
    # Current Pixel Studio already owns document arrays/split-pane state; accept either marker set.
    if not re.search(r"documents|document_count|active_document|secondary_document|split", pixel_render + pixel_input + read("apps/haven_editor_native/src/app/pixel_studio.rs"), re.I):
        ERRORS.append("Pixel Studio: no multi-document/split-pane state markers found")
    for studio in ["AnimationStudio", "CharacterStudio", "LogicStudio", "SoundStudio", "SceneMap", "SceneRectangles"]:
        require(tabs, [studio], "protected workspace document row")

    # W76N-P/Q: wardrobe-first Character Studio. W81R5 supersedes the original
    # debug-shaped button labels with the production Character Creator while preserving
    # the same guarded randomization/lock/preset capabilities.
    common_character = [
        "locked_slots", "toggle_current_slot_lock", "randomize_recipe_scope",
        "Assembled Character Preview", "sync_assembled_preview", "Advanced",
    ]
    require(character, common_character, "Character Studio wardrobe workflow")
    legacy_character = [
        "Create, dress, preview, randomize and save a valid player/NPC recipe",
        "Randomize Outfit", "Randomize Appearance", "Lock Slot", "Save Preset", "Load Preset",
    ]
    creator_character = [
        "Character Creator", "Player Character", "Wardrobe & Gear", "All Unlocked",
        "Add Selected", "Turn Left", "Turn Right", "Restart Animation",
    ]
    if not all(marker in character for marker in legacy_character) and not all(marker in character for marker in creator_character):
        ERRORS.append("Character Studio: neither legacy W76 wardrobe UI nor W81R5 production creator UI is complete")
    # Compatibility filtering must be explicit rather than random raw-layer assignment.
    if "compatible" not in character.lower():
        ERRORS.append("Character Studio: compatibility-filtered randomization marker missing")

    # W76A/Q: retired visible authorities are removed, while hot reload survives separately.
    for rel in [
        "apps/haven_editor_native/src/app/asset_shelf.rs",
        "apps/haven_editor_native/src/app/asset_library_panel.rs",
        "apps/haven_editor_native/src/app/asset_intake_panel.rs",
        "apps/haven_editor_native/src/app/scene_toolrail.rs",
    ]:
        require_file_absent(rel)
    require_absent(mod_rs, ["mod asset_shelf;", "mod asset_library_panel;", "mod asset_intake_panel;", "mod scene_toolrail;"], "module graph")
    require(mod_rs, ["mod asset_hot_reload;"], "asset hot-reload service migration")

    # Do-not-regress: direct authoring remains visual-only and semantic authorities stay separate.
    require(direct_visual, ["SceneVisualOverride"], "direct visual authoring")
    if not ("semantic" in direct_visual.lower() and "collision" in direct_visual.lower()):
        ERRORS.append("direct visual authoring: semantic/collision separation markers missing")

    if ERRORS:
        print("W76 native editor GUI closure validation FAILED")
        for error in ERRORS:
            print(f"- {error}")
        return 1

    print("PASS: W76A-T native editor GUI closure contract")
    print("- protected CanvasWorkspace/document tabs + ruler-safe viewport")
    print("- pointer-captured slider/color interactions + fixed-right shared palette")
    print("- normalized controls/tool registry + transactional Pixel effects")
    print("- scene document state + Pixel multi-document preservation")
    print("- Character Wardrobe/randomization/Advanced workflow")
    print("- retired duplicate GUI modules removed; visual/gameplay authority separation retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
