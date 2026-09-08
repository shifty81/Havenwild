#!/usr/bin/env python3
"""Validate the Havenwild terrain transition rule editor/browser pass.

This is a structural validator for the data-driven transition-rule editor tab.
It does not compile Rust; it verifies that the world catalog, game editor panel,
input routing, draw routing, and manifest-driven rule browser hooks are present.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
LOG = ROOT / "logs" / "terrain_transition_rule_editor_v18_validation_report.json"

CHECKS = []


def require_file(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        raise AssertionError(f"missing required file: {path}")
    CHECKS.append({"check": f"file:{path}", "status": "ok"})
    return full.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing {label}: {needle}")
    CHECKS.append({"check": label, "status": "ok"})


def main() -> None:
    catalog = require_file("crates/haven_world/src/autotile/transition_rule_catalog.rs")
    mod_rs = require_file("crates/haven_world/src/autotile/mod.rs")
    panel = require_file("crates/haven_game/src/transition_rule_editor_panel.rs")
    editor_state = require_file("crates/haven_game/src/editor_state.rs")
    main_rs = require_file("crates/haven_game/src/main.rs")
    input_rs = require_file("crates/haven_game/src/runtime_input.rs")
    shell_rs = require_file("crates/haven_game/src/runtime_editor_shell.rs")
    draw_rs = require_file("crates/haven_game/src/runtime_draw.rs")
    manifest = json.loads(require_file("content/worldgen/terrain_transition_rule_manifest_v0_1.json"))

    require(catalog, "TransitionRuleCatalogFilter", "world catalog filter enum")
    require(catalog, "transition_rule_catalog_rows", "world catalog row query")
    require(catalog, "transition_rule_catalog_summary", "world catalog summary")
    require(catalog, "Shoreline", "shoreline filter")
    require(catalog, "Constructed", "constructed filter")
    require(mod_rs, "pub mod transition_rule_catalog;", "world catalog module export")
    require(mod_rs, "TransitionRuleCatalogFilter", "world catalog re-export")
    require(panel, "handle_transition_rules_tab_click", "game editor tab click handler")
    require(panel, "draw_transition_rules_editor_tab", "game editor tab draw handler")
    require(panel, "sync_transition_rule_preview_to_editor_selection", "preview sync hook")
    require(panel, "handle_transition_rule_editor_hotkeys", "editor rule hotkeys")
    require(editor_state, "Transitions", "editor tab enum entry")
    require(main_rs, "mod transition_rule_editor_panel;", "game module wiring")
    require(main_rs, "transition_rule_editor_filter", "game state filter field")
    require(input_rs, "handle_transition_rule_editor_hotkeys", "runtime input routing")
    require(shell_rs, "handle_transition_rules_tab_click", "editor click routing")
    require(draw_rs, "draw_transition_rules_editor_tab", "editor draw routing")

    rules = manifest.get("rules", [])
    if len(rules) < 12:
        raise AssertionError("transition rule manifest should contain the authored rule set")
    water_rules = [rule for rule in rules if rule.get("center") == "water" or rule.get("neighbor") == "water"]
    if not water_rules:
        raise AssertionError("transition rule manifest should still include water/shoreline rules")
    CHECKS.append({"check": "manifest authored rules", "status": "ok", "count": len(rules)})
    CHECKS.append({"check": "manifest shoreline rules", "status": "ok", "count": len(water_rules)})

    LOG.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "havenwild.validation.terrain_transition_rule_editor.v18",
        "status": "passed",
        "checks": CHECKS,
    }
    LOG.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Terrain transition rule editor validation passed: {len(CHECKS)} checks")


if __name__ == "__main__":
    main()
