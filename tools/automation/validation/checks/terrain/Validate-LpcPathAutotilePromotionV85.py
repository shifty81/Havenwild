#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
errors: list[str] = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"missing {rel}")
        return ""
    return path.read_text(encoding="utf-8")


core = read("crates/haven_core/src/autotile_data.rs")
tiles = read("crates/haven_core/src/foundation/tile_object_catalog.rs")
generator = read("tools/automation/terrain/Generate-LiveAutotileAtlas.py")
editor_preview = read("apps/haven_editor_native/src/app/autotile_render.rs")
resolver = read("crates/haven_world/src/autotile/transition_resolver.rs")
live = read("crates/haven_world/src/autotile/live_autotile.rs")
validation = read("crates/haven_editor/src/autotile_validation.rs")
editor_tests = read("crates/haven_editor/src/lib_tests.rs")
contract = read("content/editor/autotile/live_autotile_authoring_contract_v0_1.json")
rules = read("content/worldgen/autotile_rules_v0_3.json")
read("docs/assets/OPEN_GAME_ART_ASSET_DUMP_PASS85.md")
read("docs/assets/LPC_PATH_AUTOTILE_PROMOTION_PASS85.md")

checks = [
    ("pub const ALL: [TileAutoGroup; 10]", core, "TileAutoGroup::ALL must include 10 split groups"),
    ("TileAutoGroup::StonePath", core, "StonePath autotile group is missing"),
    ("TileAutoGroup::MountainPath", core, "MountainPath autotile group is missing"),
    ("TileAutoGroup::Bridge", core, "Bridge autotile group is missing"),
    ("TileKind::StonePath => Some(TileAutoGroup::StonePath)", tiles, "StonePath still maps to the wrong group"),
    ("TileKind::MountainPath => Some(TileAutoGroup::MountainPath)", tiles, "MountainPath still maps to the wrong group"),
    ("TileKind::Bridge => Some(TileAutoGroup::Bridge)", tiles, "Bridge still maps to the wrong group"),
    ('("stone_path", "stone_path")', generator, "live atlas generator does not emit stone_path row"),
    ('("mountain_path", "mountain_path")', generator, "live atlas generator does not emit mountain_path row"),
    ('("bridge", "bridge")', generator, "live atlas generator does not emit bridge row"),
    ("TileAutoGroup::StonePath =>", editor_preview, "native autotile preview has no StonePath color"),
    ("TileAutoGroup::MountainPath =>", editor_preview, "native autotile preview has no MountainPath color"),
    ("TileAutoGroup::Bridge =>", editor_preview, "native autotile preview has no Bridge color"),
    ("legacy_road_override_still_applies_to_split_path_tiles", live, "legacy path override compatibility test is missing"),
    ("override_group_matches_tile", validation, "editor validation does not allow legacy road path overrides"),
    ("inspector_reports_split_path_groups_independently", editor_tests, "editor inspector does not lock split path group diagnostics"),
    ('line == "Autotile group: Stone Path"', editor_tests, "editor inspector test does not verify Stone Path group label"),
    ('line == "Autotile mask: 0x00"', editor_tests, "editor inspector test does not verify split path masks stay separate"),
    ('"stone_path"', contract, "editor autotile contract omits stone_path"),
    ('"mountain_path"', contract, "editor autotile contract omits mountain_path"),
    ('"bridge"', contract, "editor autotile contract omits bridge"),
    ('"stone_path": [', rules, "worldgen autotile rules omit stone_path group"),
    ('"mountain_path": [', rules, "worldgen autotile rules omit mountain_path group"),
    ('"bridge": [', rules, "worldgen autotile rules omit bridge group"),
]

for needle, text, message in checks:
    if needle not in text:
        errors.append(message)

transition_import_block = resolver.split("};", 1)[0]
if "family_neighbors" in transition_import_block:
    errors.append("Pass84 Clippy fix regressed: transition_resolver still imports family_neighbors")

old_stale_inspector_shape = (
    "map.set(4, 4, TileKind::Road);\n"
    "    map.set(5, 4, TileKind::StonePath);\n"
    "    let report = inspect_cell(&map, 4, 4);"
)
if old_stale_inspector_shape in editor_tests:
    errors.append("editor inspector test still expects StonePath to join Road mask 0x04")

manifest_path = ROOT / "assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json"
try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    group_ids = [group["id"] for group in manifest.get("groups", [])]
    expected = [
        "road",
        "stone_path",
        "mountain_path",
        "bridge",
        "wood_floor",
        "stone_floor",
        "water",
        "wall",
        "cliff",
        "cave_wall",
    ]
    if group_ids != expected:
        errors.append(f"live autotile group order mismatch: {group_ids}")
    variants = manifest.get("variants", [])
    if len(variants) != 160:
        errors.append(f"live autotile atlas must contain 160 variants, found {len(variants)}")
    by_group: dict[str, set[int]] = {}
    for variant in variants:
        by_group.setdefault(variant.get("group", ""), set()).add(int(variant.get("mask4", -1)))
    for group in expected:
        if by_group.get(group) != set(range(16)):
            errors.append(f"{group} does not cover all 16 cardinal masks")
except Exception as exc:
    errors.append(f"failed to validate live autotile manifest: {exc}")

if errors:
    print("LPC path autotile promotion validation failed:")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("V85 OK: LPC path autotile groups are split, generated, and compatibility-guarded")
