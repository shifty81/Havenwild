#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
def text(relative: str) -> str:
    path = ROOT / relative
    assert path.is_file(), f"missing {relative}"
    return path.read_text(encoding="utf-8")


def data(relative: str) -> dict:
    return json.loads(text(relative))


contract = data("content/editor/pixel_editor/native_pixel_studio_v0_1.json")
assert contract["schema"] == "havenwild.editor.native_pixel_studio.v0_1"
assert contract["workspace"] == "Pixel Studio"
assert contract["baseTileSize"] == [32, 32]
assert contract["characterFrameSize"] == [64, 96]
assert contract["canvas"]["nearestNeighbor"] is True
assert contract["canvas"]["pointerCenteredZoom"] is True
assert contract["canvas"]["middleMousePan"] is True
assert contract["canvas"]["repeatPreview3x3"] is True
assert contract["atlasGridRealignment"]["nonDestructive"] is True
assert contract["atlasGridRealignment"]["requiresArmingAndConfirmation"] is True
assert contract["atlasGridRealignment"]["movesPixels"] is False
assert contract["publishing"]["promotionIsExplicit"] is True
assert contract["publishing"]["runtimeBakeIsSeparate"] is True
required_tools = {
    "pencil",
    "eraser",
    "fill",
    "eyedropper",
    "selection",
    "line",
    "rectangle",
}
assert required_tools <= set(contract["tools"])

workspace = text("Cargo.toml")
app_manifest = text("apps/haven_editor_native/Cargo.toml")
assert '"crates/haven_pixel"' in workspace
assert 'haven_pixel = { path = "../../crates/haven_pixel" }' in app_manifest

pixel_lib = text("crates/haven_pixel/src/lib.rs")
document = text("crates/haven_pixel/src/document.rs")
document_operations = text("crates/haven_pixel/src/document_operations.rs")
persistence = text("crates/haven_pixel/src/persistence.rs")
library = text("crates/haven_pixel/src/library.rs")
publish = text("crates/haven_pixel/src/publish.rs")
for token in [
    "PixelDocument",
    "PixelDocumentMetadata",
    "PixelGrid",
    "PixelSelection",
    "PixelTool",
]:
    assert token in pixel_lib
for token in [
    "pub fn begin_edit",
    "pub fn undo",
    "pub fn redo",
    "pub fn flood_fill",
    "pub fn draw_line",
    "pub fn draw_rectangle",
]:
    assert token in document
for token in [
    "pub fn flip_selection_horizontal",
    "pub fn flip_selection_vertical",
]:
    assert token in document_operations
assert "pub fn save" in persistence
assert "undo_limit: 64" in document
assert 'replace_extension(&self.output_path, "hhasset.json")' in document
assert 'replace_extension(&self.output_path, "hhpixel")' in document
for root in contract["sourceRoots"]:
    assert root in library
assert "PixelLibrarySource::UserCc0" in library
assert "generated output; edit a working copy" in library.lower()
assert "AssetPromotionState::Draft" in publish
assert "publish_working_copy" in publish
assert "selection.x" in publish and "selection.width.max(1)" in publish
assert "catalog.save_default" in publish
assert "document.metadata.pivot[0] - selection.x as i32" in publish
assert "document.metadata.pivot[1] - selection.y as i32" in publish

native_mod = text("apps/haven_editor_native/src/app/mod.rs")
native_draw = text("apps/haven_editor_native/src/app/draw.rs")
native_input = text("apps/haven_editor_native/src/app/input.rs")
native_menu = text("apps/haven_editor_native/src/app/editor_menu.rs")
command_registry = text("apps/haven_editor_native/src/app/command_registry.rs")
native_pixel = text("apps/haven_editor_native/src/app/pixel_studio.rs")
native_pixel_render = text("apps/haven_editor_native/src/app/pixel_studio_render.rs")
native_pixel_input = text("apps/haven_editor_native/src/app/pixel_studio_input.rs")
assert "mod pixel_studio;" in native_mod and "mod pixel_studio_input;" in native_mod
assert "EditorViewportMode::PixelStudio" in native_mod
assert 'argument == "--pixel-studio"' in native_mod
assert "Pixel Studio" in native_draw
assert "canvas_workspace_layout().viewport" in native_pixel_render
assert "self.update_pixel_studio_input()" in native_input
assert '"Pixel Studio"' in (native_menu + command_registry)
for token in [
    "Texture2D::from_rgba8",
    "FilterMode::Nearest",
    "draw_checkerboard",
    "draw_pixel_grid",
    "draw_atlas_grid",
    "draw_repeat_preview",
    "Publish Slice Draft",
    "Save Working Copy",
    "Grid Realign: ON",
    "Confirm Realign",
]:
    assert token in (native_pixel + native_pixel_render)
for token in [
    "mouse_wheel",
    "MouseButton::Middle",
    "KeyCode::Space",
    "KeyCode::Z",
    "KeyCode::Y",
    "grid_realign_armed",
    "grid_realign_enabled",
    "grid_cell_selection",
    "Pivot moved to selected slice bottom-center",
]:
    assert token in native_pixel_input
assert "pixels will not move" in native_pixel_input

registry = text("crates/haven_editor/src/validation_registry.rs")
assert 'id: "pixel_editor"' in registry
assert "ValidationRegistryStatus::Active" in registry
assert "native_pixel_studio_v0_1.json" in registry

manifest = data("content/assets/intake/cc0_user_upload_manifest_v0_1.json")
assert manifest["schema"] == "havenwild.cc0_user_upload_manifest.v0_1"
assets = manifest["assets"]
assert len(assets) >= 19, f"expected at least 19 imported CC0 sources, found {len(assets)}"
seen_ids: set[str] = set()
seen_paths: set[str] = set()
for asset in assets:
    assert asset["id"] not in seen_ids, f"duplicate id {asset['id']}"
    assert asset["path"] not in seen_paths, f"duplicate path {asset['path']}"
    seen_ids.add(asset["id"])
    seen_paths.add(asset["path"])
    assert asset["license"] == "CC0-1.0"
    assert asset["promotionState"] == "pixel_studio_source_only"
    path = ROOT / asset["path"]
    assert path.is_file(), f"missing imported CC0 source {asset['path']}"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == asset["sha256"]
    with Image.open(path) as image:
        assert list(image.size) == [asset["width"], asset["height"]]

build = text("tools/build/Build.sh")
assert "pixel-studio)" in build
assert "--pixel-studio" in build
assert "pixel-audit)" in build
assert "Validate-NativePixelStudioV79.py" in build

print(
    "Native Pixel Studio validation V79 passed "
    f"({len(assets)} traceable CC0 sources, {len(required_tools)} core tools)"
)
