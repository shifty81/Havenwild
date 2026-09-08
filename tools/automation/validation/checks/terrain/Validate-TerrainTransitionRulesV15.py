#!/usr/bin/env python3
"""Validate data-driven terrain transition rule manifest wiring.

This ensures coast/terrain transition behavior is no longer only hardwired in
Rust. The runtime may keep conservative fallback rules, but normal resolution
must first consult an editor-facing manifest under content/worldgen.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
MANIFEST = ROOT / "content" / "worldgen" / "terrain_transition_rule_manifest_v0_1.json"
RULES_RS = ROOT / "crates" / "haven_world" / "src" / "autotile" / "transition_rules_manifest.rs"
RESOLVER_RS = ROOT / "crates" / "haven_world" / "src" / "autotile" / "transition_resolver.rs"
ATLAS_RS = ROOT / "crates" / "haven_world" / "src" / "autotile" / "transition_atlas.rs"
MOD_RS = ROOT / "crates" / "haven_world" / "src" / "autotile" / "mod.rs"
FAMILY_RS = ROOT / "crates" / "haven_world" / "src" / "autotile" / "terrain_family.rs"
DEBUG_RS = ROOT / "crates" / "haven_game" / "src" / "terrain_debug_overlay.rs"

REQUIRED_MATERIALS = {
    "wet_sand",
    "shallow_water_edge",
    "grass_fringe",
    "dirt_blend",
    "road_shoulder",
    "stone_shoulder",
    "rock_shadow",
}
REQUIRED_SELECTOR_CODES = {
    "soft_natural",
    "blocking_wall",
    "non_blocking_wall",
    "shallow_water",
    "deep_water",
}
REQUIRED_ATLAS_GROUPS = {
    "grass_over_dirt",
    "grass_over_sand",
    "grass_bank_over_shallow",
    "dirt_bank_over_shallow",
    "sand_bank_over_shallow",
    "shallow_rim_over_deep",
    "riverbank_mud",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require_file(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    data = json.loads(require_file(MANIFEST))
    if data.get("schema") != "havenwild.worldgen.terrain_transition_rule_manifest.v0_1":
        fail("terrain transition rule manifest schema mismatch")
    if data.get("kind") != "terrain_transition_rules":
        fail("terrain transition rule manifest kind mismatch")

    rules = data.get("rules")
    if not isinstance(rules, list) or len(rules) < 12:
        fail("terrain transition rule manifest needs at least 12 concrete rules")

    materials: set[str] = set()
    selector_codes: set[str] = set()
    atlas_groups: set[str] = set()
    ids: set[str] = set()
    for rule in rules:
        rid = rule.get("id")
        if not isinstance(rid, str) or not rid:
            fail(f"invalid rule id: {rid!r}")
        if rid in ids:
            fail(f"duplicate rule id: {rid}")
        ids.add(rid)
        for key in ("center", "neighbor", "material", "atlasGroup", "appliesTo", "priority"):
            if key not in rule:
                fail(f"rule {rid} missing {key}")
        if not isinstance(rule["appliesTo"], list) or not set(rule["appliesTo"]).issubset({"edge", "corner"}):
            fail(f"rule {rid} has invalid appliesTo: {rule['appliesTo']!r}")
        if not isinstance(rule["priority"], int):
            fail(f"rule {rid} priority must be an integer")
        materials.add(rule["material"])
        atlas_groups.add(rule["atlasGroup"])
        selector_codes.add(rule["center"])
        selector_codes.add(rule["neighbor"])

    missing_materials = REQUIRED_MATERIALS - materials
    if missing_materials:
        fail(f"terrain transition rule manifest missing materials: {sorted(missing_materials)}")
    missing_groups = REQUIRED_ATLAS_GROUPS - atlas_groups
    if missing_groups:
        fail(f"terrain transition rule manifest missing atlas groups: {sorted(missing_groups)}")
    missing_selectors = REQUIRED_SELECTOR_CODES - selector_codes
    if missing_selectors:
        fail(f"terrain transition rule manifest missing selector examples: {sorted(missing_selectors)}")

    rules_src = require_file(RULES_RS)
    for needle in [
        "TERRAIN_TRANSITION_RULE_MANIFEST_PATH",
        "TerrainTransitionRuleManifest",
        "TerrainFamilySelector",
        "TransitionRulePhase",
        "transition_rule_material",
        "transition_rule_atlas_group_for_material",
        "load_json::<TerrainTransitionRuleManifestFile>",
        "highest priority matching rule wins",
    ]:
        if needle not in rules_src:
            fail(f"transition rules module missing hook: {needle}")

    resolver_src = require_file(RESOLVER_RS)
    for needle in [
        "transition_rule_material(TransitionRulePhase::Edge",
        "transition_rule_material(TransitionRulePhase::Corner",
        "builtin_edge_material",
        "TransitionMaterial::from_code",
    ]:
        if needle not in resolver_src:
            fail(f"transition resolver missing data-driven/fallback hook: {needle}")

    atlas_src = require_file(ATLAS_RS)
    for needle in ["transition_rule_atlas_group_for_material(material)", "transition_pair_atlas_group"]:
        if needle not in atlas_src:
            fail(f"transition atlas grouping missing hook: {needle}")

    mod_src = require_file(MOD_RS)
    for needle in [
        "pub mod transition_rules_manifest;",
        "terrain_transition_rule_manifest",
        "TerrainTransitionRuleManifest",
        "TransitionRulePhase",
    ]:
        if needle not in mod_src:
            fail(f"autotile module does not export rule manifest hook: {needle}")

    family_src = require_file(FAMILY_RS)
    if "pub fn from_code(code: &str) -> Option<Self>" not in family_src:
        fail("TerrainFamily does not expose from_code for manifest loading")

    debug_src = require_file(DEBUG_RS)
    if "terrain_transition_rule_manifest()" not in debug_src or "terrain transition rules" not in debug_src:
        fail("terrain debug overlay does not report rule manifest coverage")

    print("OK: terrain transition rule manifest and runtime hooks validated")


if __name__ == "__main__":
    main()
