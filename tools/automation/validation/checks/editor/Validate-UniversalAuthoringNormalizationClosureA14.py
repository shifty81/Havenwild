#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8-sig")


def data(rel: str):
    try:
        return json.loads(text(rel))
    except Exception as exc:
        errors.append(f"invalid JSON {rel}: {exc}")
        return {}


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


# 1) Structural connector authority: discrete normal levels and transactional
# area-selected connectors, not raw atlas stamping.
struct_types = text("crates/haven_editor/src/world_surface_edit/mod.rs")
struct_ops = text("crates/haven_editor/src/world_surface_edit/operations.rs")
struct_ui = text("apps/haven_editor_native/src/app/world_surface_authoring_ui.rs")
struct_native = text("apps/haven_editor_native/src/app/world_surface_structural_authoring.rs")
struct_tests = text("crates/haven_editor/src/world_surface_edit/tests.rs")
editor_root = text("crates/haven_editor/src/lib.rs")
palette = text("apps/haven_editor_native/src/app/brush_palette_drawer.rs")
for token in ('"Ramp 2→1→0"', '"Ladder"', "WorldStructuralConnectorPlan"):
    require(token in struct_types, f"structural connector type missing {token}")
for token in (
    "resolve_world_structural_connector_plan",
    "place_world_structural_connector",
    "Structural connector preview is stale",
    "CertifiedRampOrientationV1",
    "SetStructuralLevel",
):
    require(token in struct_ops, f"connector authority missing {token}")
for token in ("world_structural_connector_preview", "Apply {}"):
    require(token in struct_native + struct_ui, f"connector area-selection UI missing {token}")
for token in ("connector.ramp", "connector.ladder"):
    require(token in palette + struct_native, f"connector palette choice missing {token}")
for token in (
    "selected_cliff_resolves_and_commits_certified_ramp_as_one_undo_step",
    "selected_true_cliff_places_stateful_ladder_and_undo_restores_world",
):
    require(token in struct_tests, f"connector regression coverage missing {token}")
for token in (
    "place_world_structural_connector",
    "resolve_world_structural_connector_plan",
    "WorldStructuralConnectorKind",
    "WorldStructuralConnectorPlan",
):
    require(token in editor_root, f"native editor connector API is not re-exported from haven_editor: {token}")
require("Level 6" not in struct_ui, "obsolete Level 6 remains authorable")

# 2) World/editor parity must use canonical semantic materialization and one
# world-creation settings/seed authority.
world_editor = text("apps/haven_editor_native/src/app/world_surface_editor.rs")
development = text("apps/haven_editor_native/src/app/development_session.rs")
island_authoring = text("apps/haven_editor_native/src/app/island_authoring.rs")
require("SemanticWorldBakeV1" in world_editor + development + island_authoring, "semantic world bake is not shared by editor/play")
require("WorldCreationSettings" in development, "development Play does not persist canonical world-creation settings")
require("let world_path = editor_world_path();" in development, "development world authority borrows the parent of a temporary editor_world_path")
require("seed: 1337" not in development and "seed = 1337" not in development, "editor Play still contains the stale seed 1337 authority")

# 3) Neutral Resource Context and exact animation source-frame propagation.
context_model = text("crates/haven_authoring/src/resource_context.rs")
context_runtime = text("crates/haven_game/src/development_resource_context.rs")
context_live_bridge = text("crates/haven_game/src/development_live_bridge.rs")
context_editor = text("apps/haven_editor_native/src/app/resource_context_bridge.rs")
animation = text("apps/haven_editor_native/src/app/animation_studio.rs")
animation_runtime = text("apps/haven_editor_native/src/app/animation_studio_runtime_context.rs")
character_runtime = text("apps/haven_editor_native/src/app/character_studio_runtime_ext.rs")
character_studio = text("apps/haven_editor_native/src/app/character_studio.rs")
for token in ("havenwild.resource_context.v1", "CharacterAnimationResourceContext", "UiResourceContext", "ResourceContextKind"):
    require(token in context_model, f"neutral Resource Context missing {token}")
for token in ("ResourceContextKind::Character", "ResourceContextKind::Equipment", "ResourceContextKind::Animation", "ResourceContextKind::Frame"):
    require(token in context_runtime, f"runtime Resource Context missing {token}")
for token in ("RESOURCE_CONTEXT_HEARTBEAT_MS", "development_resource_context", "write_resource_context"):
    require(token in context_live_bridge, f"active DevelopmentLiveBridge does not publish Resource Context: {token}")
require("socket_ids: Vec::new()" in context_runtime, "runtime fabricates socket metadata instead of failing closed")
for token in ("authoring_ui_document_id", "developer_focus_requested: self.dev_mode", "ResourceContextKind::Ui"):
    require(token in context_runtime + text("crates/haven_game/src/player_inventory_ui.rs"), f"direct runtime UI context missing {token}")
require("handle_development_mode_toggle" in text("crates/haven_game/src/client_pause_menu.rs"), "F3 cannot focus modal UI resources")
require("open_game_canvas_ui_document_by_id" in context_editor, "editor cannot open exact runtime UI document")
for token in ("open_runtime_context_animation_in_studio", "resolve_runtime_animation_source", "apply_runtime_source_context"):
    require(token in context_editor + character_runtime + animation, f"runtime-to-animation context bridge missing {token}")
require("apply_runtime_frame_context" in animation_runtime, "Animation Studio runtime Resource Context module is missing frame application")
require("frame.source.x" in animation_runtime and "frame_width" in animation_runtime and "source_frame_index" in animation_runtime, "Animation Studio does not map runtime source-frame identity to the actual source cell")
require('.get("body")' in character_studio and 'body_item_id' in character_studio, "Character Studio runtime animation fallback is not tied to the recipe body selection")
require('resolved.layers.iter().find(|layer| layer.slot' not in character_studio, "Character Studio assumes a nonexistent ResolvedUniversalLpcLayer.slot field")

# 4) Game Canvas owns UI documents. The retired standalone gui_studio module
# must remain absent from the active module graph.
mod_rs = text("apps/haven_editor_native/src/app/mod.rs")
game_ui = text("apps/haven_editor_native/src/app/game_canvas_ui.rs")
ui_model = text("crates/haven_authoring/src/ui_document.rs")
require("mod game_canvas_ui;" in mod_rs, "Game Canvas UI document implementation is not active")
require("mod gui_studio;" not in mod_rs, "retired standalone GUI Studio was reactivated")
for token in ("Layout", "Controls", "Data", "Behavior", "Presentation", "Overrides"):
    require(token in ui_model, f"UI authoring lane missing {token}")
for token in ("Edit Visual in Pixel Studio", "PixelPreviewMode::Ui", "ResourceContextKind::Visual", "ResourceContextKind::Source"):
    require(token in game_ui, f"resolved UI visual editing missing {token}")

# 5) Scene Library must be a screen-space collection, not another hidden
# infinite-camera authority.
scene_bank = text("apps/haven_editor_native/src/app/scene_bank_workspace.rs")
canvas_controller = text("apps/haven_editor_native/src/app/canvas_controller.rs")
mod_source = text("apps/haven_editor_native/src/app/mod.rs")
require("scene_library_layout" in scene_bank and "scene_library_card_rect" in scene_bank, "Scene Library lacks screen-space card layout authority")
require("draw_infinite_grid" not in scene_bank, "Scene Library still draws an infinite grid")
for forbidden in ("scene_bank_canvas", "scene_bank_pan_tool"):
    require(forbidden not in canvas_controller + mod_source, f"retired Scene Library camera state remains: {forbidden}")

# 6) A14X GUI shell closure: one top-level Game Canvas, a real reserved Layers
# panel, and non-overlapping upper canvas status/view controls.
top_bar = text("apps/haven_editor_native/src/app/render_helpers.rs")
input_rs = text("apps/haven_editor_native/src/app/input.rs")
ui_shell = text("apps/haven_editor_native/src/app/ui_shell.rs")
layers_ui = text("apps/haven_editor_native/src/app/canvas_layers.rs")
scene_draw = text("apps/haven_editor_native/src/app/draw_scene_views.rs")
require('(Some(EditorViewportMode::SceneMap), "Game Canvas")' in top_bar, "global studio strip lacks the single Game Canvas tab")
require('EditorViewportMode::SceneRectangles,\n        EditorViewportMode::SceneMap' not in top_bar, "global studio strip still renders duplicate World/Scene Game Canvas tabs")
require('const WIDTHS: [f32; 7]' in ui_shell, "global workspace strip is not normalized to Game Canvas + Assets + five specialized studios")
require('if !self.viewport_mode.is_game_canvas()' in input_rs, "Game Canvas tab does not preserve contextual Game Canvas views")
require('+ self.canvas_layer_rail_width()' in layers_ui, "Layers does not reserve its own sibling panel width")
require('Layers is a dedicated panel, not text painted over the world' in layers_ui, "Layers panel is still rendered as canvas overlay text")
require('canvas_view_control_rect(viewport, 0).x' in scene_draw and 'status_width' in scene_draw, "upper canvas status is not clipped before zoom/view controls")

# 7) Typed production UI examples must validate semantically, not through
# historical marker strings.
ui_dir = ROOT / "content/ui/documents"
docs = {path.stem.replace(".ui", ""): data(str(path.relative_to(ROOT))) for path in sorted(ui_dir.glob("*.ui.json"))}
for required in ("gameplay_hud", "inventory", "crafting", "world_creation", "loading_default", "map", "pause", "settings"):
    require(required in docs, f"acceptance UI document missing {required}")
for name, document in docs.items():
    if not document:
        continue
    require(document.get("schema") == "havenwild.ui_document.v1", f"{name}: wrong UI schema")
    require(bool(document.get("id")), f"{name}: empty id")
    require(document.get("reference_size", [0, 0])[0] > 0 and document.get("reference_size", [0, 0])[1] > 0, f"{name}: invalid reference size")
    ids: set[str] = set()
    for widget in document.get("widgets", []):
        wid = widget.get("id", "")
        require(bool(wid) and wid not in ids, f"{name}: duplicate/empty control id {wid!r}")
        ids.add(wid)
        rect = widget.get("rect", {})
        require(rect.get("width", 0) > 0 and rect.get("height", 0) > 0, f"{name}/{wid}: invalid rectangle")
        for binding in widget.get("data_bindings", []):
            require(bool(binding.get("property")) and bool(binding.get("source")), f"{name}/{wid}: incomplete data binding")
        for binding in widget.get("behavior_bindings", []):
            require(bool(binding.get("event")) and bool(binding.get("action")), f"{name}/{wid}: incomplete behavior binding")
    for widget in document.get("widgets", []):
        parent = widget.get("parent")
        require(parent is None or parent in ids, f"{name}/{widget.get('id')}: missing parent {parent}")

craft = docs.get("crafting", {})
craft_button = next((widget for widget in craft.get("widgets", []) if widget.get("id") == "craft_button"), {})
require(any(binding.get("source") == "crafting.can_craft_selected" for binding in craft_button.get("data_bindings", [])), "Craft button lacks typed enabled binding")
require(any(binding.get("action") == "crafting.craft_selected" for binding in craft_button.get("behavior_bindings", [])), "Craft button lacks typed craft action")
transition = data("content/transitions/default_scene_transition.transition.json")
require(transition.get("schema") == "havenwild.transition_resource.v1", "transition schema mismatch")
require(transition.get("loading_ui_document_id") == "loading_default", "transition does not reference loading UI document")

if errors:
    print("FAIL: A14 Universal Authoring Normalization Closure")
    for error in errors:
        print(" -", error)
    sys.exit(1)
print("PASS: A14 Universal Authoring Normalization Closure")
print("- structural connectors: area-resolved, previewed, transactional")
print("- world/editor: canonical semantic bake/settings authority")
print("- runtime context: character -> equipment -> animation -> source frame + modal UI focus")
print("- UI/loading: typed Game Canvas documents with resolved Pixel visual editing")
print("- Scene Library: adaptive screen-space collection with no hidden camera")
print("- GUI shell: one Game Canvas tab + reserved Layers panel + collision-free canvas header")
