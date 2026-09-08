#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]; errors=[]
def read(rel):
 p=ROOT/rel
 if not p.is_file(): errors.append(f"missing {rel}"); return ""
 return p.read_text(encoding="utf-8")
def need(rel,*markers):
 s=read(rel)
 for m in markers:
  if m not in s: errors.append(f"{rel} missing marker: {m}")
helpers=read("apps/haven_editor_native/src/app/render_helpers.rs")
if "W60E3H: text clipping must stay on UTF-8 character boundaries." not in helpers: errors.append("shared editor text clipping is missing UTF-8 safety contract")
if 'shown.truncate(shown.len() - 3)' in helpers: errors.append("shared editor text clipping still uses byte-index String::truncate")
need("apps/haven_editor_native/src/app/canvas_layers.rs", "CANVAS_TOOL_RACK_WIDTH: f32 =", "canvas_layer_rail_expanded_width", "draw_lock_icon", "draw_circle_lines", "display_label")
need("apps/haven_editor_native/src/app/workspace_shell.rs", "canvas_layer_rail_width: 174.0", "clamp(132.0, 480.0)")
layers=read("apps/haven_editor_native/src/app/canvas_layers.rs")
if "row.detail" in layers: errors.append("layer rail must not render per-layer detail text")
need("apps/haven_editor_native/src/app/tool_registry.rs", "enum ToolGroup", "tool_is_applicable", "group_has_applicable_tool")
need("apps/haven_editor_native/src/app/canvas_tool_rack.rs", "centered_icon_rect", "draw_brush_mode_icon", "draw_brush_source_icon", "draw_palette_icon")
need("apps/haven_editor_native/src/app/canvas_tool_rack.rs", "draw_tool_icon", "TEXT_DISABLED", "canvas_tool_rack_rect")
pixel=read("apps/haven_editor_native/src/app/pixel_studio_render.rs")
if "PixelTool::ALL" in pixel: errors.append("Pixel Studio top chrome still duplicates centralized tool selection")
need("apps/haven_editor_native/src/app/pixel_color_panel.rs", "color_wheel_center", "draw_pixel_color_panel", "update_color_from_pointer")
need("apps/haven_editor_native/src/app/shared_palette.rs", "pixel_color_popup_open", "begin_color_picker_drag")
need("apps/haven_editor_native/src/app/asset_browser_ui.rs", "browser_card_rect", "browser_thumbnail_rect", "fit_preview_rect", "draw_browser_card_surface", "draw_browser_card_labels", "draw_thumbnail_placeholder")
need("apps/haven_editor_native/src/app/pixel_library_panel.rs", "load_visible_asset_browser_thumbnails", "draw_browser_card_surface")
need("apps/haven_editor_native/src/app/animation_studio.rs", "draw_browser_card_surface", "draw_browser_card_labels", "PixelLibraryCategory")
need("apps/haven_editor_native/src/app/asset_palette_panel.rs", "draw_browser_card_surface", "draw_browser_card_labels")
need("apps/haven_editor_native/src/app/unified_asset_browser.rs", "Project-wide thumbnail runtime", "load_thumbnail")
need("crates/haven_pixel/src/library.rs", "enum PixelLibraryCategory", "classify_pixel_library_entry", "Objects / Props", "Clothing / Gear", "Tools / Items")
# W60C originally validated three monolithic Help pages. R42 split those
# responsibilities into the indexed Help Wiki while preserving the same UX
# authority. Validate the modern semantic equivalents instead of requiring
# retired article titles to remain as dead compatibility strings.
need(
 "apps/haven_editor_native/src/app/editor_help.rs",
 "Keyboard Shortcuts",
 "Canvas Workspace",
 "Layers Rail",
 "Unified Asset Browser",
 "Pixel Studio",
 "Repair Unsupported Transitions",
 "Color & Palette",
 "ToolGroup::ALL",
)
need("apps/haven_editor_native/src/app/workspace_chrome.rs", "KeyCode::F1")
need("apps/haven_editor_native/src/app/command_registry.rs", '"Asset Browsers"', '"Color & Palette"')
contract=ROOT/"content/editor/native_editor_canvas_ux_w60c_v1.json"
if not contract.is_file(): errors.append("missing W60C canvas UX contract")
else:
 data=json.loads(contract.read_text(encoding="utf-8"))
 if data.get("schema")!="havenwild.native_editor_canvas_ux.w60c.v1": errors.append("W60C canvas UX schema mismatch")
 if data.get("layerPane",{}).get("detailTextVisible") is not False: errors.append("W60C layer pane must prohibit detail text")
 if data.get("toolRail",{}).get("duplicateTopToolSelectorsAllowed") is not False: errors.append("W60C must prohibit duplicate top tool selectors")
 if data.get("assetBrowsers",{}).get("sharedThumbnailCards") is not True: errors.append("W60C must require shared thumbnail cards")
if errors:
 print("FAIL: W60C canvas UX and asset-browser authority"); [print(" -",e) for e in errors]; sys.exit(1)
print("PASS: W60C canvas UX and asset-browser authority (unified-browser compatible)")
