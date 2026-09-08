#!/usr/bin/env python3
"""Validate the terrain transition rule inspector pass.

This intentionally performs source/content checks instead of compiling because
some handoff sandboxes do not have Rust installed. It keeps the pass honest by
verifying the inspector is world-side, game-side, toggled, exported, and still
bound to the data-driven transition rule manifest.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
REQUIRED = [
    ROOT / "crates/haven_world/src/autotile/transition_rule_inspector.rs",
    ROOT / "crates/haven_game/src/transition_rule_inspector_overlay.rs",
    ROOT / "content/worldgen/terrain_transition_rule_manifest_v0_1.json",
]

CHECKS = {
    "crates/haven_world/src/autotile/mod.rs": [
        "pub mod transition_rule_inspector;",
        "inspect_terrain_transition_rules",
        "TerrainTransitionRuleHit",
        "TerrainTransitionRuleInspection",
    ],
    "crates/haven_world/src/autotile/transition_rule_inspector.rs": [
        "TerrainTransitionRuleHit",
        "TerrainTransitionRuleInspection",
        "inspect_terrain_transition_rules",
        "terrain_transition_rule_manifest",
        "best_rule_for",
        "used_builtin_fallback",
        "rule_priority",
        "atlas_group",
    ],
    "crates/haven_game/src/main.rs": [
        "mod transition_rule_inspector_overlay;",
        "show_transition_rule_inspector",
    ],
    "crates/haven_game/src/runtime_input.rs": [
        "KeyCode::Y",
        "Terrain transition rule inspector enabled",
        "Terrain transition rule inspector hidden",
    ],
    "crates/haven_game/src/runtime_draw.rs": [
        "draw_transition_rule_inspector_overlay",
    ],
    "crates/haven_game/src/transition_rule_inspector_overlay.rs": [
        "Transition Rule Inspector",
        "inspect_terrain_transition_rules",
        "rule / priority",
        "Y toggles inspector",
        "used_builtin_fallback",
        "first_visible_reason",
    ],
    "crates/haven_game/src/terrain_debug_overlay.rs": [
        "Y toggles rule inspector",
    ],
}


def fail(message: str) -> int:
    print(f"[FAIL] {message}")
    return 1


def main() -> int:
    for path in REQUIRED:
        if not path.exists():
            return fail(f"missing required file: {path.relative_to(ROOT)}")

    for rel, needles in CHECKS.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                return fail(f"missing {needle!r} in {rel}")

    manifest_path = ROOT / "content/worldgen/terrain_transition_rule_manifest_v0_1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rules = manifest.get("rules", [])
    if len(rules) < 12:
        return fail("terrain transition rule manifest should still contain the authored rule set")
    if not any(rule.get("reason") for rule in rules):
        return fail("transition rule manifest should provide at least one editor-facing reason")
    if not any("edge" in rule.get("appliesTo", []) for rule in rules):
        return fail("transition rule manifest should include edge rules")
    if not any("corner" in rule.get("appliesTo", []) for rule in rules):
        return fail("transition rule manifest should include corner rules")

    print("[OK] Terrain transition rule inspector pass is wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
