#!/usr/bin/env python3
from pathlib import Path
import json, sys
root = Path(__file__).resolve().parents[5]
issues = []
required = [
    "crates/haven_game/src/world_paint_render_binding.rs",
    "crates/haven_game/src/world_paint_editor_draw.rs",
    "crates/haven_game/src/world_paint_editor_panel.rs",
    "crates/haven_game/src/runtime_draw.rs",
    "crates/haven_game/src/main.rs",
    "content/assets/world_paint/world_paint_render_binding_contract_v0_1.json",
    "content/schemas/world_paint_render_binding_contract.schema.v0_1.json",
    "docs/assets/WORLD_PAINT_RENDER_BINDING_PASS37.md",
]
for rel in required:
    if not (root / rel).exists():
        issues.append(f"missing required file: {rel}")
contract_path = root / "content/assets/world_paint/world_paint_render_binding_contract_v0_1.json"
if contract_path.exists():
    data = json.loads(contract_path.read_text())
    if data.get("canonicalTileSize") != [32, 32]:
        issues.append("render binding contract must keep canonicalTileSize [32,32]")
    atlas = data.get("sourceAtlas", "")
    if not atlas.endswith("havenwild_world_environment_test_v0_1.png"):
        issues.append("render binding contract must point at generated world environment atlas")
    if not (root / atlas).exists():
        issues.append(f"render binding source atlas does not exist: {atlas}")
main = (root / "crates/haven_game/src/main.rs").read_text()
for needle in [
    "mod world_paint_render_binding;",
    "world_tile_atlas: Option<Texture2D>",
    "WORLD_PAINT_TEST_ATLAS_PATH",
    "refresh_world_paint_render_bindings_for_active_scene",
]:
    if needle not in main:
        issues.append(f"main.rs missing render-binding hook: {needle}")
render_binding = (root / "crates/haven_game/src/world_paint_render_binding.rs").read_text()
for needle in [
    "WorldPaintRenderBindingCache",
    "resolve_world_paint_scene_transition_tile_details",
    "DrawTextureParams",
]:
    if needle not in render_binding:
        issues.append(f"world_paint_render_binding.rs missing: {needle}")
runtime_draw = (root / "crates/haven_game/src/runtime_draw.rs").read_text()
if "draw_world_paint_atlas_tile_if_bound" not in runtime_draw and "draw_world_paint_atlas_layers_if_bound" not in runtime_draw:
    issues.append("runtime_draw.rs must draw atlas-bound paint tiles/layers before fallback terrain")
panel = (root / "crates/haven_game/src/world_paint_editor_panel.rs").read_text()
if '"Bind"' not in panel or "KeyCode::B" not in panel:
    issues.append("Paint tab must expose Bind button and B hotkey")
world = (root / "crates/haven_world/src/world_paint_transition_tile_resolver.rs").read_text()
for needle in ["WorldPaintTransitionSceneTileDetails", "resolve_world_paint_scene_transition_tile_details"]:
    if needle not in world:
        issues.append(f"transition tile resolver missing detailed scene API: {needle}")
if "draw_world_paint_atlas_tile_if_bound" not in render_binding and "draw_world_paint_atlas_layers_if_bound" not in render_binding:
    issues.append("world_paint_render_binding.rs missing atlas draw function")
if issues:
    print("World paint render binding validation FAILED")
    for issue in issues:
        print(" -", issue)
    sys.exit(1)
print("World paint render binding validation passed")
