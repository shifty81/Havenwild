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


contract = data("content/editor/pixel_editor/pixel_animation_roundtrip_bridge_v0_1.json")
assert contract["schema"] == "havenwild.editor.pixel_animation_roundtrip_bridge.v0_1"
assert contract["ownership"]["hostExecutable"] == "HavenwildEditor"
assert contract["ownership"]["separateExecutablesRequired"] is False
assert contract["openFrame"]["entryAction"] == "Edit Selected Frame in Pixel Studio"
assert contract["openFrame"]["keyboardShortcut"] == "E"
assert contract["openFrame"]["preservesClipIndex"] is True
assert contract["openFrame"]["preservesFrameIndex"] is True
assert contract["sourcePolicy"]["editsOriginalImportedSourceDirectly"] is False
assert contract["sourcePolicy"]["animationSourceRebindsToWorkingCopyOnSave"] is True
assert contract["pixelAnimationTab"]["showsPreviousAndNextOnionSkin"] is True
assert contract["pixelAnimationTab"]["showsPivotOverlay"] is True
assert contract["pixelAnimationTab"]["showsSocketOverlays"] is True
assert contract["saveReturn"]["returnsToSameClipAndFrame"] is True
assert contract["saveReturn"]["keyboardShortcut"] == "Ctrl+Enter"
assert contract["safety"]["blocksCanvasCropDuringFrameBridge"] is True
assert contract["safety"]["blocksCanvasResizeDuringFrameBridge"] is True
assert contract["safety"]["refusesCrossAnimationWrite"] is True

native_mod = text("apps/haven_editor_native/src/app/mod.rs")
bridge = text("apps/haven_editor_native/src/app/pixel_animation_bridge.rs")
pixel_state = text("apps/haven_editor_native/src/app/pixel_studio.rs")
pixel_render = text("apps/haven_editor_native/src/app/pixel_studio_render.rs")
pixel_input = text("apps/haven_editor_native/src/app/pixel_studio_input.rs")
layer_input = text("apps/haven_editor_native/src/app/pixel_layer_input.rs")
context_layout = text("apps/haven_editor_native/src/app/pixel_context_layout.rs")
animation_render = text("apps/haven_editor_native/src/app/animation_studio.rs")
animation_input = text("apps/haven_editor_native/src/app/animation_studio_input.rs")
animation_rects = text("apps/haven_editor_native/src/app/animation_studio_render.rs")

assert "mod pixel_animation_bridge;" in native_mod
for token in [
    "pub(crate) struct PixelAnimationEditContext",
    "animation_asset_id",
    "clip_index",
    "frame_index",
    "previous_source",
    "next_source",
    "shadow_offset",
    "sockets: Vec<AnimationSocket>",
    "animation_context: Option<PixelAnimationEditContext>",
    "pub(crate) fn frame_selection",
]:
    assert token in pixel_state, token

for token in [
    "open_selected_animation_frame_in_pixel_studio",
    "save_animation_pixels_and_return",
    "return_to_animation_without_pixel_save",
    "reload_animation_texture_from_path",
    "animation.metadata.source_path = output_path.clone()",
    "animation.metadata.asset_id != context.animation_asset_id",
    "context.clip_index.min",
    "animation.selected_frame = context.frame_index",
    "frame.pivot =",
]:
    assert token in bridge, token

for token in [
    "PixelInspectorTab::Animation",
    "draw_pixel_animation_inspector",
    "draw_pixel_animation_context_overlay",
    "context.previous_source",
    "context.next_source",
    "context.shadow_offset",
    "socket.kind.label()",
    '"Save Pixels & Return to Animation"',
    '"Return Without Saving Pixels"',
]:
    assert token in pixel_render, token

for token in [
    "pixel_animation_tab_rect",
    "pixel_animation_onion_rect",
    "pixel_animation_focus_rect",
    "pixel_animation_save_return_rect",
    "pixel_animation_cancel_return_rect",
]:
    assert token in context_layout, token

assert "self.save_animation_pixels_and_return();" in pixel_input
assert "self.return_to_animation_without_pixel_save();" in pixel_input
assert "KeyCode::Enter" in pixel_input and "animation_context.is_some()" in pixel_input
# W78 retired the duplicate geometry controls that lived in the old Pixel Layer
# panel. The active animation-frame bridge therefore has no crop/trim/resize
# route in either the canonical Layers rail or its rename-input handler.
canonical_layers = text("apps/haven_editor_native/src/app/canvas_layers.rs")
for forbidden in ["crop_to_selection", "trim_transparent_padding", "resize_canvas"]:
    assert forbidden not in canonical_layers, forbidden
    assert forbidden not in layer_input, forbidden
assert "animation_context.is_some()" in pixel_input

assert '"Edit Selected Frame in Pixel Studio"' in animation_render
assert "animation_edit_pixels_rect" in animation_rects
assert "self.open_selected_animation_frame_in_pixel_studio();" in animation_input
assert "KeyCode::E" in animation_input

registry = text("crates/haven_editor/src/validation_registry.rs")
assert 'id: "pixel_animation_roundtrip"' in registry
assert "pixel_animation_roundtrip_bridge_v0_1.json" in registry

build = text("tools/build/Build.sh")
assert "pixel-animation-audit)" in build
assert "Validate-PixelAnimationRoundtripBridgeV82.py" in build
validate = text("tools/automation/validation/validate.py")
assert "Validate-PixelAnimationRoundtripBridgeV82.py" in (validate + build)

print(
    "Pixel/Animation round-trip validation V82 passed "
    "(frame context, onion overlays, working-copy rebinding, guarded geometry, and same-frame return)"
)
