#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

def text(path: str) -> str:
    p = ROOT / path
    if not p.is_file():
        errors.append(f"missing {path}")
        return ""
    return p.read_text(encoding="utf-8")

def require(path: str, *markers: str) -> None:
    source = text(path)
    for marker in markers:
        if marker not in source:
            errors.append(f"{path} missing marker: {marker}")

def load_json(path: str, schema: str) -> dict:
    raw = text(path)
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except Exception as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if value.get("schema") != schema:
        errors.append(f"{path} schema mismatch: {value.get('schema')!r}")
    return value

# W62A: dependency governance and Havenwild-owned seams.
cargo = text("Cargo.toml")
for member in [
    "haven_identity", "haven_diagnostics", "haven_schema", "haven_jobs",
    "haven_spatial", "haven_audio", "haven_logic",
]:
    if f'crates/{member}' not in cargo:
        errors.append(f"workspace member missing: {member}")
for dependency in ['rayon = "1.12"', 'hound = "3.5"']:
    if dependency not in cargo:
        errors.append(f"bounded activated dependency missing: {dependency}")
require("crates/haven_identity/src/lib.rs", "pub struct HavenId", "AuthoringSessionId", "RevisionId")
require("crates/haven_diagnostics/src/lib.rs", "pub struct DiagnosticsHub", "MetricSnapshot", "DiagnosticEvent")
require("crates/haven_schema/src/lib.rs", "SchemaIssue", "validate_schema_tag")
require("crates/haven_jobs/src/lib.rs", "rayon::prelude::*", "JobRecord", "parallel_map")
require("crates/haven_spatial/src/lib.rs", "SpatialIndex", "Aabb2")
oss = load_json("content/architecture/oss_dependency_intake_w62a_v1.json", "havenwild.oss_dependency_intake.w62a.v1")
if oss and not oss.get("policy", {}).get("thirdPartyTypesForbiddenInPublicSaveSchemas"):
    errors.append("OSS contract must keep third-party types out of Havenwild save schemas")

# W62B/C: seven major studios + canvas-first/contextual asset shelf.
require("apps/haven_editor_native/src/app/editor_types.rs", "LogicStudio", "SoundStudio")
require("apps/haven_editor_native/src/app/render_helpers.rs", "EditorViewportMode::LogicStudio", "EditorViewportMode::SoundStudio")
require("apps/haven_editor_native/src/app/workspace_shell.rs", "left_panel_visible: false", "asset_shelf_open", "canvas_tool_rail_collapsed", "canvas_layer_rail_collapsed")
require("apps/haven_editor_native/src/app/ui_shell.rs", "visible_panels_and_bottom_dock_expose_resize_splitters", "left_panel_visible: true", "right_panel_visible: true", "bottom_dock_open: true")
normalization70 = load_json("content/architecture/project_normalization_w70_v1.json", "havenwild.architecture.project_normalization.w70.v1")
if normalization70:
    require("apps/haven_editor_native/src/app/asset_shelf.rs", "draw_universal_asset_shelf", "handle_universal_asset_shelf_click", "focus_right_dock", "RightDockTab::Assets")
    require("apps/haven_editor_native/src/app/right_dock.rs", "draw_right_dock_assets", "draw_asset_palette", "draw_logic_library", "draw_sound_library", "RightDockTab::Assets")
else:
    require("apps/haven_editor_native/src/app/asset_shelf.rs", "draw_universal_asset_shelf", "handle_universal_asset_shelf_click", "draw_asset_palette", "draw_logic_library", "draw_sound_library")
require("apps/haven_editor_native/src/app/tool_registry.rs", 'Self::Place => "Stamp / Place"', "V::LogicStudio", "V::SoundStudio")
load_json("content/editor/canvas/canvas_workspace_w62b_v1.json", "havenwild.canvas_workspace.w62b.v1")

# W62D: authoring session / multi-publish.
require("crates/haven_authoring/src/session.rs", "pub struct AuthoringSession", "PublishEverywhere" if False else "enable_publish_everywhere", "PcgExemplar", "PresentationSet", "StampMotif")
require("apps/haven_editor_native/src/app/authoring_publish.rs", "Publish Authored Composition", "Publish Everywhere", "execute_authoring_publish", "authoring_session.json", "publish_preview.json")
load_json("content/editor/authoring/authoring_session_publish_w62d_v1.json", "havenwild.authoring_session_publish.w62d.v1")

# W62E: generated transform tracks/rig continuation.
require("crates/haven_authoring/src/animation_tracks.rs", "TransformTrack2D", "Rig2D", "GeneratedTransformPreset", "Hinge", "Sway", "Bob", "Pulse", "Recoil")
require("crates/haven_authoring/src/lib.rs", "pub mod animation_tracks", "pub mod session")
load_json("content/editor/authoring/rig_animation_generation_w62e_v1.json", "havenwild.rig_animation_generation.w62e.v1")

# W62F: first-class Sound Studio + real bounded audio backend.
require("crates/haven_audio/src/lib.rs", "pub struct SoundDocument", "InstrumentKind", "AudioNodeKind", "render_preview_wav", "hound::WavWriter")
require("apps/haven_editor_native/src/app/sound_studio.rs", "SoundStudioState", "draw_sound_workspace", "Render Preview WAV", "Add C4 MIDI Note", "UniversalTool::Place", "UniversalTool::Link", "UniversalTool::Move")
if (ROOT / "content/editor/gui/gui_authoring_character_milestone_w74b_v1.json").is_file():
    require("apps/haven_editor_native/src/app/command_registry.rs", '"Sound Studio"', "TOOLS_COMMANDS")
else:
    require("apps/haven_editor_native/src/app/editor_menu.rs", '"Sound Studio"', "EditorMenuKind::Tools")
load_json("content/editor/sound/sound_studio_w62f_v1.json", "havenwild.sound_studio.w62f.v1")

# W62G: deterministic Logic Studio.
require("crates/haven_logic/src/lib.rs", "pub struct LogicGraph", "CompiledLogicGraph", "event.interact", "action.play_sound")
require("apps/haven_editor_native/src/app/logic_studio.rs", "LogicStudioState", "draw_logic_workspace", "Compile / Validate", "UniversalTool::Place", "UniversalTool::Link", "UniversalTool::Move")
load_json("content/editor/logic/logic_studio_w62g_v1.json", "havenwild.logic_studio.w62g.v1")


# W62H: unified browser runtime + black-text containment.
require("apps/haven_editor_native/src/app/unified_asset_browser.rs",
        "UnifiedAssetBrowserRuntime",
        "UNIFIED_BROWSER_THUMBNAIL_EDGE: u32 = 96",
        "UNIFIED_BROWSER_CACHE_LIMIT: usize = 96",
        "UNIFIED_BROWSER_MAX_SOURCE_DIMENSION: u32 = 4096",
        "build_bounded_thumbnail")
require("apps/haven_editor_native/src/app/asset_browser_ui.rs",
        "draw_browser_card_surface",
        "draw_browser_card_labels",
        "draw_browser_texture",
        "final texture/material owner")
require("apps/haven_editor_native/src/app/render_helpers.rs", "restore_editor_ui_render_state")
require("apps/haven_editor_native/src/app/pixel_studio_render.rs", "restore_editor_ui_render_state")
require("apps/haven_editor_native/src/app/animation_studio_render.rs", "restore_editor_ui_render_state")
require("apps/haven_editor_native/src/app/pixel_library_panel.rs",
        "unified_asset_browser.texture",
        "unified_asset_browser.load_thumbnail",
        "Asset Browser")
require("apps/haven_editor_native/src/app/animation_studio.rs",
        "unified_asset_browser.texture",
        "Asset Browser")
require("apps/haven_editor_native/src/app/atlas_render.rs",
        "Asset-browser thumbnails are UI draws",
        "restore_editor_ui_render_state")
# W62H1: sibling modules that call the UI-state fence must import it explicitly.
require("apps/haven_editor_native/src/app/asset_browser_ui.rs",
        "use super::render_helpers::restore_editor_ui_render_state;")
require("apps/haven_editor_native/src/app/atlas_render.rs",
        "use super::render_helpers::restore_editor_ui_render_state;")
browser_loader = text("apps/haven_editor_native/src/app/pixel_library_panel.rs")
for forbidden in ["self.asset_browser_thumbnails", "self.asset_browser_thumbnail_failures", "load_texture(&raw)"]:
    if forbidden in browser_loader:
        errors.append(f"legacy/raw thumbnail path remains: {forbidden}")
load_json("content/editor/assets/unified_asset_browser_w62h_v1.json", "havenwild.unified_asset_browser.w62h.v1")
# W62H2: legacy W60C validation must recognize the unified browser as the
# superseding implementation instead of requiring retired per-studio cache names.
require("tools/automation/validation/checks/editor/Validate-CanvasUxAssetBrowserW60C.py",
        "unified_browser_active",
        "UnifiedAssetBrowserRuntime",
        "thumbnailRuntimeShared")


# W62H3: persistent Segoe/Macroquad font-atlas stabilization.
require("apps/haven_editor_native/src/app/editor_text.rs",
        "EDITOR_FONT_RASTER_TIERS",
        "populate_font_cache",
        "font_scale: raster_scale",
        "font.set_filter(FilterMode::Linear)",
        "macroquad::miniquad::window::dpi_scale")
load_json("content/editor/text/editor_font_atlas_w62h3_v1.json", "havenwild.editor_font_atlas.w62h3.v1")

# Save All keeps document persistence in editor_menu. W73D/W73E move menu
# labels/routing vocabulary into the canonical command registry.
require("apps/haven_editor_native/src/app/editor_menu.rs", "sound_studio.document.save_to_path", "logic_studio.graph.save_to_path")
if (ROOT / "content/editor/gui/gui_authoring_character_milestone_w74b_v1.json").is_file():
    require("apps/haven_editor_native/src/app/command_registry.rs", "Publish Authored Composition...", "Sound Studio", "Logic Studio", "TOOLS_COMMANDS")
else:
    require("apps/haven_editor_native/src/app/editor_menu.rs", "Publish Authored Composition...", "Sound Studio", "EditorMenuKind::Tools")
require("apps/haven_editor_native/src/app/workspace_chrome.rs", "pub(crate) fn persist_workspace_shell")
require("apps/haven_editor_native/src/app/input.rs", "update_logic_studio_input", "update_sound_studio_input")
require("apps/haven_editor_native/src/app/draw.rs", "draw_logic_workspace", "draw_sound_workspace", "draw_authoring_publish_panel")

if errors:
    print("FAIL: W62 unified foundation / authoring / sound / logic")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("PASS: W62 unified foundation / authoring / sound / logic")
