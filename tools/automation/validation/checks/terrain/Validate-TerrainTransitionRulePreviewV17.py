#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
required_files = [
    ROOT / "crates/haven_world/src/autotile/transition_rule_preview.rs",
    ROOT / "crates/haven_game/src/transition_rule_preview_overlay.rs",
    ROOT / "content/worldgen/terrain_transition_rule_manifest_v0_1.json",
]
for path in required_files:
    if not path.exists():
        print(f"ERROR: missing {path.relative_to(ROOT)}")
        sys.exit(1)

world_mod = (ROOT / "crates/haven_world/src/autotile/mod.rs").read_text()
for token in [
    "pub mod transition_rule_preview;",
    "preview_transition_rule",
    "preview_transition_rules",
    "TerrainTransitionRulePreview",
    "TransitionPreviewSampleKind",
]:
    if token not in world_mod:
        print(f"ERROR: autotile module does not export {token}")
        sys.exit(1)

preview_src = (ROOT / "crates/haven_world/src/autotile/transition_rule_preview.rs").read_text()
for token in [
    "TransitionPreviewSampleKind",
    "TransitionPreviewCellRole",
    "preview_transition_rules",
    "build_preview_sample",
    "resolve_terrain_transitions_from_neighbors",
    "resolve_transition_atlas_requests",
]:
    if token not in preview_src:
        print(f"ERROR: transition_rule_preview.rs missing {token}")
        sys.exit(1)

game_main = (ROOT / "crates/haven_game/src/main.rs").read_text()
for token in [
    "mod transition_rule_preview_overlay;",
    "show_transition_rule_preview: bool",
    "transition_rule_preview_index: usize",
]:
    if token not in game_main:
        print(f"ERROR: main.rs missing {token}")
        sys.exit(1)

input_src = (ROOT / "crates/haven_game/src/runtime_input.rs").read_text()
for token in [
    "KeyCode::U",
    "show_transition_rule_preview",
    "cycle_transition_rule_preview(-1)",
    "cycle_transition_rule_preview(1)",
]:
    if token not in input_src:
        print(f"ERROR: runtime_input.rs missing {token}")
        sys.exit(1)

draw_src = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text()
if "draw_transition_rule_preview_overlay" not in draw_src:
    print("ERROR: runtime draw path does not call transition rule preview overlay")
    sys.exit(1)

overlay_src = (ROOT / "crates/haven_game/src/transition_rule_preview_overlay.rs").read_text()
for token in [
    "draw_transition_rule_preview_overlay",
    "draw_preview_sample",
    "draw_preview_cell",
    "U toggles preview",
    "J/K cycle rules",
]:
    if token not in overlay_src:
        print(f"ERROR: transition_rule_preview_overlay.rs missing {token}")
        sys.exit(1)

manifest = json.loads((ROOT / "content/worldgen/terrain_transition_rule_manifest_v0_1.json").read_text())
rules = manifest.get("rules", [])
if len(rules) < 12:
    print("ERROR: transition rule manifest has too few rules for preview coverage")
    sys.exit(1)
for rule in rules:
    seen = set()
    # This cannot catch duplicate JSON keys after json.loads, so check the raw slice too below.
    for key in ["id", "center", "neighbor", "material", "atlasGroup", "appliesTo", "priority"]:
        if key not in rule:
            print(f"ERROR: rule {rule.get('id', '<unknown>')} missing {key}")
            sys.exit(1)
raw_manifest = (ROOT / "content/worldgen/terrain_transition_rule_manifest_v0_1.json").read_text()
if raw_manifest.count('"id": "wall_touching_water_rock_shadow"') == 1:
    wall_rule_block = raw_manifest.split('"id": "wall_touching_water_rock_shadow"', 1)[1].split('"id":', 1)[0]
    if wall_rule_block.count('"center"') != 1:
        print("ERROR: wall_touching_water_rock_shadow contains duplicate center fields")
        sys.exit(1)

print("Terrain transition rule preview validation passed")
