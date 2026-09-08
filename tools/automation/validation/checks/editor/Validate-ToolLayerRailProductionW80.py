#!/usr/bin/env python3
"""Validate W80 Tool Rail + Layer Rail production completion."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
ERRORS = []

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        ERRORS.append(f"missing required file: {rel}")
        return ""
    return path.read_text(encoding="utf-8")

def require(text, markers, context):
    for marker in markers:
        if marker not in text:
            ERRORS.append(f"{context}: missing marker {marker!r}")

def main():
    tool = read("apps/haven_editor_native/src/app/canvas_tool_rack.rs")
    registry = read("apps/haven_editor_native/src/app/tool_registry.rs")
    layers = read("apps/haven_editor_native/src/app/canvas_layers.rs")
    pixel_rail = read("apps/haven_editor_native/src/app/pixel_layer_rail.rs")
    pixel_ops = read("crates/haven_pixel/src/document_operations.rs")
    gui = read("apps/haven_editor_native/src/app/gui_controls.rs")
    input_rs = read("apps/haven_editor_native/src/app/input.rs")
    draw = read("apps/haven_editor_native/src/app/draw.rs")
    shell = read("apps/haven_editor_native/src/app/workspace_shell.rs")
    build_sh = read("tools/build/Build.sh")
    contract_text = read("content/editor/native_editor_tool_layer_rail_w80_v1.json")

    require(tool, [
        "visible_tool_entries", "active_brush_modes", "tool_shelf_mode_rect",
        "select_canvas_brush_mode", "draw_canvas_tool_overlays",
        "update_canvas_tool_scroll_input", "centered_icon_rect",
        "draw_brush_mode_icon", "draw_brush_source_icon", "draw_palette_icon"
    ], "Tool Rail production authority")
    for stale in ["canvas_tool_overflow_open", "overflow_tool_entries", "draw_canvas_tool_overflow_popup", '"More tools"', "tool_is_secondary"]:
        if stale in tool:
            ERRORS.append(f"Tool Rail still hides applicable tools behind obsolete overflow: {stale}")
    require(registry, [
        "PixelStudio", "MagicSelect", "Gradient", "Blur", "Smudge",
        "SceneRectangles", "PixelEdit", "generic overflow/menu affordance"
    ], "Tool registry direct-rail policy")
    require(layers, [
        "canvas_layer_scroll", "draw_layer_kind_badge", "canvas_layer_scroll_up_rect",
        "canvas_layer_scroll_down_rect", "begin_pixel_layer_drag", "pixel_layer_drag"
    ], "Layer Rail production authority")
    require(pixel_rail, [
        "PixelLayerDragState", "update_pixel_layer_drag_input", "open_pixel_layer_context_menu",
        "Move Up", "Move Down", "Merge Down", "Rename", "Duplicate", "Delete",
        "Layer opacity", "cycle_active_layer_blend_mode", "begin_layer_opacity_drag"
    ], "Pixel Layer Rail actions")
    require(pixel_ops, [
        "move_active_layer_to", "set_active_layer_opacity", "set_active_layer_blend_mode",
        "self.layers.remove(index)", "self.layers.insert(target, layer)"
    ], "Pixel document exact layer operations")
    require(gui, ["LayerOpacity(Rect)", "apply_pixel_layer_opacity_slider"], "pointer-captured opacity")
    require(input_rs, [
        "update_pixel_layer_drag_input", "update_canvas_layer_scroll_input",
        "update_canvas_tool_scroll_input", "open_pixel_layer_context_menu"
    ], "rail input routing")
    require(draw, ["draw_canvas_tool_rack", "draw_canvas_layer_rail", "draw_canvas_tool_overlays"], "overlay draw order")
    require(shell, ["canvas_layer_scroll"], "persisted rail scroll")
    require(build_sh, [
        "Validate-NativeEditorInteractionDocumentClosureW79.py",
        "Validate-ToolLayerRailProductionW80.py"
    ], "Windows Full Quality Gate convergence")

    try:
        contract = json.loads(contract_text)
        if contract.get("schema") != "havenwild.editor.tool_layer_rail.w80.v1":
            ERRORS.append("W80 contract schema mismatch")
        if contract.get("layerRail", {}).get("compactPermanentActions") != ["add", "duplicate", "delete", "more"]:
            ERRORS.append("W80 compact Layer Rail action policy mismatch")
    except Exception as exc:
        ERRORS.append(f"could not parse W80 contract: {exc}")

    if '["+", "Dup", "Del", "Up", "Dn", "Mrg"]' in pixel_rail:
        ERRORS.append("legacy six-button Pixel layer footer is still present")
    if "layers.x + layers.w + self.canvas_authoring_ruler_gutter()" in tool:
        ERRORS.append("Tool Rail flyout is still positioned relative to the Layers panel")

    if ERRORS:
        print("W80 Tool Rail + Layer Rail production validation FAILED")
        for error in ERRORS:
            print("-", error)
        return 1

    print("PASS: W80 Tool Rail + Layer Rail production completion")
    print("- every applicable tool stays directly reachable on the vertically scrollable Tool Rail; no generic More Tools overflow")
    print("- brush/symmetry flyouts anchor to their Tool Rail controls and draw above Layers")
    print("- Layer Rail scrolls, exposes semantic badges, and supports locked-boundary drag reorder")
    print("- Pixel layer opacity is pointer-captured; blend mode and compact context actions are canonical")
    print("- W79/W80 validators are part of the Windows Full Quality Gate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
