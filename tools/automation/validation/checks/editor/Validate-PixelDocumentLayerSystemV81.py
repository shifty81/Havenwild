#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def text(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"missing {relative}"
    return path.read_text(encoding="utf-8")


def data(relative: str) -> dict:
    return json.loads(text(relative))


contract = data("content/editor/pixel_editor/pixel_document_layer_system_v0_2.json")
assert contract["schema"] == "havenwild.editor.pixel_document_layer_system.v0_2"
assert contract["documentSchema"] == "havenwild.pixel_document.v0_2"
assert contract["sourcePolicy"]["editGeneratedOutputsDirectly"] is False
assert contract["sourcePolicy"]["publishedRuntimeOutputsAreSeparate"] is True
assert contract["layers"]["minimumCount"] == 1
assert contract["layers"]["compositeIsNonDestructive"] is True
assert set(contract["layers"]["blendModes"]) == {
    "normal", "multiply", "screen", "add", "erase"
}
assert {
    "add", "duplicate", "rename", "reorder", "merge_down", "delete",
    "show_hide", "lock_unlock", "opacity", "blend_mode",
} <= set(contract["layers"]["operations"])
assert {
    "resize_canvas", "crop_to_selection", "trim_transparent_padding",
    "flip_selection_horizontal", "flip_selection_vertical",
} <= set(contract["documentOperations"])
assert contract["history"]["snapshotIncludesPixels"] is True
assert contract["history"]["snapshotIncludesLayers"] is True
assert contract["history"]["snapshotIncludesMetadata"] is True
assert contract["history"]["undoLimit"] == 64
assert contract["persistence"]["layerPackageExtension"] == "hhpixel"
assert contract["persistence"]["autosaveIntervalSeconds"] == 10
assert contract["persistence"]["automaticRecovery"] is True
assert contract["migration"]["readsV01Sidecars"] is True
assert contract["migration"]["writesV02Only"] is True

document = text("crates/haven_pixel/src/document.rs")
operations = text("crates/haven_pixel/src/document_operations.rs")
layers = text("crates/haven_pixel/src/layers.rs")
persistence = text("crates/haven_pixel/src/persistence.rs")
library = text("crates/haven_pixel/src/library.rs")
pixel_lib = text("crates/haven_pixel/src/lib.rs")

for token in [
    "pub enum PixelBlendMode",
    "pub struct PixelLayerMetadata",
    "pub struct PixelLayer",
    "active_layer_id",
    "layers: Vec<PixelLayer>",
    "struct PixelDocumentSnapshot",
    "metadata: PixelDocumentMetadata",
    "layers: Vec<PixelLayer>",
    "undo_limit: 64",
    "pub fn begin_edit",
    "pub fn undo",
    "pub fn redo",
]:
    assert token in document, token

for token in [
    "pub fn add_layer",
    "pub fn duplicate_active_layer",
    "pub fn delete_active_layer",
    "pub fn move_active_layer",
    "pub fn merge_active_down",
    "pub fn rename_active_layer",
    "pub fn toggle_active_layer_visibility",
    "pub fn toggle_active_layer_lock",
    "pub fn adjust_active_layer_opacity",
    "pub fn cycle_active_layer_blend_mode",
    "pub fn resize_canvas",
    "pub fn crop_to_selection",
    "pub fn trim_transparent_padding",
    "pub fn flip_selection_horizontal",
    "pub fn flip_selection_vertical",
]:
    assert token in operations, token

for token in [
    "pub(crate) fn composite_layers",
    "PixelBlendMode::Normal",
    "PixelBlendMode::Multiply",
    "PixelBlendMode::Screen",
    "PixelBlendMode::Add",
    "PixelBlendMode::Erase",
    "flatten_pair",
]:
    assert token in layers, token

for token in [
    'const DOCUMENT_SCHEMA_V1: &str = "havenwild.pixel_document.v0_1"',
    'const DOCUMENT_SCHEMA_V2: &str = "havenwild.pixel_document.v0_2"',
    'const RECOVERY_ROOT: &str = "WORKSPACE/recovery/pixel_studio"',
    "pub fn load(",
    "pub fn save(",
    "pub fn autosave(",
    "pub fn discard_autosave",
    'package.join("layers")',
    'replace_extension(&self.output_path, "hhpixel")',
    "load_recovery",
]:
    assert token in (persistence + document), token

assert 'const RECENT_DOCUMENTS_PATH: &str = "WORKSPACE/pixel_studio/recent_documents.json"' in library
assert "pub fn record_recent_pixel_document" in library
assert '== Some("hhpixel")' in library
assert "record_recent_pixel_document" in pixel_lib
assert "PixelBlendMode" in pixel_lib and "PixelLayerMetadata" in pixel_lib

native_mod = text("apps/haven_editor_native/src/app/mod.rs")
native_state = text("apps/haven_editor_native/src/app/pixel_studio.rs")
native_render = text("apps/haven_editor_native/src/app/pixel_studio_render.rs")
native_layers = text("apps/haven_editor_native/src/app/canvas_layers.rs") + "\n" + text("apps/haven_editor_native/src/app/pixel_layer_rail.rs")
native_context = text("apps/haven_editor_native/src/app/pixel_context_layout.rs")
native_input = text("apps/haven_editor_native/src/app/pixel_layer_input.rs")
native_pixel_input = text("apps/haven_editor_native/src/app/pixel_studio_input.rs")
editor_menu = text("apps/haven_editor_native/src/app/editor_menu.rs")

for module in ["pixel_studio_render", "canvas_layers", "pixel_layer_input", "pixel_layer_rail", "pixel_context_layout"]:
    assert f"mod {module};" in native_mod
assert "enum PixelInspectorTab" in native_state
assert "Asset" in native_state
inspector = native_state[native_state.find("enum PixelInspectorTab"):native_state.find("enum PixelSelectionMode")]
assert "Layers" not in inspector
assert "next_autosave_at" in native_state
assert "update_autosave" in native_state
assert "10.0" in native_state
assert "record_recent_pixel_document" in native_state
assert "recovered_from_autosave" in native_state
assert "PixelInspectorTab::Asset" in native_render
assert "Frame Grid" in native_render and "Pixel Grid" in native_render
for token in [
    "draw_pixel_layer_footer",
    "handle_pixel_layer_footer_click",
    "document.add_layer",
    "document.duplicate_active_layer",
    "document.delete_active_layer",
    "document.move_active_layer",
    "document.merge_active_down",
    "document.adjust_active_layer_opacity",
    "document.toggle_active_layer_visibility",
    "document.toggle_active_layer_lock",
    "layer_rename_buffer",
]:
    assert token in native_layers, token
assert "handle_pixel_layer_rename_input" in native_input
assert "pixel_layer_panel" not in native_mod
assert "pixel_asset_tab_rect" in native_context and "pixel_animation_tab_rect" in native_context
# Crop/trim/resize remain headless PixelDocument capabilities. W78 intentionally
# removed their retired duplicate Layer-panel buttons instead of duplicating them
# beside the canonical Canvas Layers rail.
for token in ["document.crop_to_selection", "document.trim_transparent_padding", "document.resize_canvas"]:
    assert token not in native_layers, token
assert "document.begin_edit();" in native_pixel_input
assert "document.save(repo_root_dir())" in editor_menu
command_registry = text("apps/haven_editor_native/src/app/command_registry.rs")
assert "Close Active Pixel Document" in command_registry and "Save All" in command_registry

registry = text("crates/haven_editor/src/validation_registry.rs")
assert 'id: "pixel_document_layers"' in registry
assert "pixel_document_layer_system_v0_2.json" in registry

build = text("tools/build/Build.sh")
assert "pixel-doc-audit)" in build
assert "Validate-PixelDocumentLayerSystemV81.py" in build
validate = text("tools/automation/validation/validate.py")
assert "Validate-PixelDocumentLayerSystemV81.py" in (validate + build)

print(
    "Pixel Document Layer System validation V81 passed "
    "(layered documents, full-history snapshots, recovery, recent files, and canonical Canvas Layers controls)"
)
