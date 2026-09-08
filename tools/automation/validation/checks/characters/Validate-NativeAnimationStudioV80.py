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


contract = data("content/editor/pixel_editor/native_animation_studio_v0_1.json")
assert contract["schema"] == "havenwild.editor.native_animation_studio.v0_1"
assert contract["workspace"] == "Animation Studio"
assert contract["sourceLibrary"]["sharedWithPixelStudio"] is True
assert contract["sourceLibrary"]["explicitRuntimePromotion"] is True
assert contract["timeline"]["frameThumbnails"] is True
assert contract["timeline"]["perFrameDurationMilliseconds"] is True
assert contract["timeline"]["onionSkin"] is True
assert contract["sheetAuthoring"]["sourcePixelsRemainUnchanged"] is True
assert contract["publishing"]["validationRequired"] is True
assert contract["publishing"]["copiesPromotedImage"] is True
assert len(contract["directionSupport"]) == 9
assert len(contract["frameMetadata"]["sockets"]) >= 8
assert len(contract["frameMetadata"]["events"]) >= 7

profiles = data("content/assets/pixel_editor/cc0_animation_sheet_profiles_v0_1.json")
assert profiles["schema"] == "havenwild.pixel_editor.cc0_animation_sheet_profiles.v0_1"
profile_names = {match for profile in profiles["profiles"] for match in profile["matches"]}
for required in ["chicken_walk", "llama_walk", "pig_walk", "horse", "cat", "base"]:
    assert required in profile_names, f"missing animation profile coverage for {required}"

catalog = data("content/animations/animation_catalog_v0_1.json")
assert catalog["schema"] == "havenwild.runtime_animation_catalog.v0_1"
assert isinstance(catalog["animations"], list)

pixel_lib = text("crates/haven_pixel/src/lib.rs")
animation_mod = text("crates/haven_pixel/src/animation/mod.rs")
animation_types = text("crates/haven_pixel/src/animation/types.rs")
animation_document = text("crates/haven_pixel/src/animation/document.rs")
animation_publish = text("crates/haven_pixel/src/animation/publish.rs")
assert "pub mod animation;" in pixel_lib
for token in [
    "AnimationDocument",
    "AnimationClip",
    "AnimationFrame",
    "AnimationDirection",
    "AnimationLoopMode",
    "AnimationSocketKind",
    "AnimationEventKind",
]:
    assert token in pixel_lib or token in animation_mod
for token in [
    "pub const ALL: [Self; 9]",
    "MainHand",
    "Tool",
    "Ground",
    "Footstep",
    "SpawnEffect",
    "duration_ms",
    "shadow_offset",
]:
    assert token in animation_types
for token in [
    "load_or_create",
    "add_clip",
    "add_frame",
    "duplicate_selected_frame",
    "delete_selected_frame",
    "move_selected_frame",
    "auto_slice_selected_row",
    "apply_recommended_profile",
    "toggle_selected_event",
    "pub fn validate",
    "pub fn save",
    "pub fn publish_runtime",
    "find_workspace_root",
    "source_reference",
]:
    assert token in animation_document
for token in [
    "GENERATED_ANIMATION_IMAGE_ROOT",
    "RUNTIME_ANIMATION_CATALOG_PATH",
    "fs::copy",
    "havenwild.runtime_animation.v0_1",
    "update_runtime_catalog",
]:
    assert token in animation_publish

native_mod = text("apps/haven_editor_native/src/app/mod.rs")
native_draw = text("apps/haven_editor_native/src/app/draw.rs")
native_input = text("apps/haven_editor_native/src/app/input.rs")
native_menu = text("apps/haven_editor_native/src/app/editor_menu.rs")
command_registry = text("apps/haven_editor_native/src/app/command_registry.rs")
studio = text("apps/haven_editor_native/src/app/animation_studio.rs")
studio_render = text("apps/haven_editor_native/src/app/animation_studio_render.rs")
studio_input = text("apps/haven_editor_native/src/app/animation_studio_input.rs")
for token in [
    "mod animation_studio;",
    "mod animation_studio_input;",
    "mod animation_studio_render;",
    "EditorViewportMode::AnimationStudio",
    'argument == "--animation-studio"',
]:
    assert token in native_mod
assert "Animation Studio" in native_draw
assert "draw_animation_timeline" in studio_render
assert "self.update_animation_studio_input()" in native_input
assert "self.handle_animation_studio_click(mx, my)" in native_input
assert '"Animation Studio"' in (native_menu + command_registry)
assert "animation_result" in native_menu
for token in [
    "AnimationStudioState",
    "advance_playback",
    "selected_source",
    "draw_animation_workspace",
    "draw_animation_inspector",
    "Save Animation",
    "Publish Runtime",
]:
    assert token in studio
for token in [
    "draw_animation_source_sheet",
    "draw_animation_preview",
    "draw_animation_timeline",
    "Onion",
]:
    assert token in studio_render
assert "Place Socket" in studio
for token in [
    "KeyCode::Space",
    "KeyCode::A",
    "KeyCode::P",
    "KeyCode::H",
    "KeyCode::K",
    "auto_slice_selected_row",
    "apply_recommended_profile",
    "toggle_selected_event",
    "place_animation_point",
    "animation_shadow_mode_rect",
    "shadow_offset",
]:
    assert token in studio_input

registry = text("crates/haven_editor/src/validation_registry.rs")
assert 'id: "animation_studio"' in registry
assert "native_animation_studio_v0_1.json" in registry

build = text("tools/build/Build.sh")
assert "animation-studio)" in build
assert "--animation-studio" in build
assert "animation-audit)" in build
assert "Validate-NativeAnimationStudioV80.py" in build

print("Native Animation Studio validation V80 passed")
