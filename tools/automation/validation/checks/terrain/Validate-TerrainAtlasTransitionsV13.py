#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
errors = []

required_files = [
    ROOT / "crates/haven_world/src/autotile/transition_atlas.rs",
    ROOT / "crates/haven_assets/src/autotile.rs",
    ROOT / "crates/haven_assets/src/lpc_terrain_family.rs",
    ROOT / "crates/haven_game/src/terrain_render.rs",
    ROOT / "crates/haven_game/src/runtime_draw.rs",
    ROOT / "crates/haven_game/src/main.rs",
    ROOT / "crates/haven_game/src/runtime_assets.rs",
    ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json",
    ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png",
]

required_groups = [
    "grass_over_dirt",
    "grass_over_sand",
    "grass_bank_over_shallow",
    "dirt_bank_over_shallow",
    "sand_bank_over_shallow",
    "shallow_rim_over_deep",
    "riverbank_mud",
]

for path in required_files:
    if not path.exists():
        errors.append(f"missing required file: {path.relative_to(ROOT)}")

world_mod = (ROOT / "crates/haven_world/src/autotile/mod.rs").read_text(encoding="utf-8")
if "pub mod transition_atlas" not in world_mod:
    errors.append("haven_world autotile module does not expose transition_atlas")
for token in ["resolve_transition_atlas_requests", "transition_pair_atlas_group"]:
    if token not in world_mod:
        errors.append(f"haven_world autotile module does not re-export {token}")

assets_autotile = (ROOT / "crates/haven_assets/src/autotile.rs").read_text(encoding="utf-8")
for token in [
    "TERRAIN_AUTOTILE_ATLAS_PATH",
    "TransitionAtlasEntry",
    "transition_atlas_entry",
    *required_groups,
]:
    if token not in assets_autotile:
        errors.append(f"haven_assets autotile missing token: {token}")

terrain_render = (ROOT / "crates/haven_game/src/terrain_render.rs").read_text(encoding="utf-8")
for token in [
    "transition_atlas_entry",
    "resolve_transition_atlas_requests",
    "transition_atlas_tint",
    "draw_atlas_transition_accents",
    "Option<&Texture2D>",
]:
    if token not in terrain_render:
        errors.append(f"terrain_render missing atlas-backed transition token: {token}")
if "draw_transition_edge(px, py" not in terrain_render:
    errors.append("terrain_render lost procedural transition fallback")

runtime_draw = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
if "self.terrain_transition_atlas.as_ref()" not in runtime_draw:
    errors.append("runtime_draw is not passing terrain_transition_atlas to transition overlay renderer")

main_rs = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")
runtime_assets = (ROOT / "crates/haven_game/src/runtime_assets.rs").read_text(encoding="utf-8")
lifecycle = main_rs + "\n" + runtime_assets
for token in ["TERRAIN_AUTOTILE_ATLAS_PATH", "terrain_transition_atlas", "transition_atlas_texture_path"]:
    if token not in lifecycle:
        errors.append(f"game asset lifecycle missing terrain transition atlas token: {token}")

manifest_path = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
if manifest_path.exists():
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    groups = {variant.get("group") for variant in data.get("variants", [])}
    for group in required_groups:
        if group not in groups:
            errors.append(f"terrain autotile manifest missing group: {group}")
    masks_by_group = {}
    for variant in data.get("variants", []):
        masks_by_group.setdefault(variant.get("group"), set()).add(variant.get("mask4"))
    for group in required_groups:
        if masks_by_group.get(group) != set(range(16)):
            errors.append(f"terrain autotile manifest group {group} does not cover all 16 mask4 cells")

if errors:
    print("FAIL TerrainAtlasTransitionsV13")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("PASS TerrainAtlasTransitionsV13")
