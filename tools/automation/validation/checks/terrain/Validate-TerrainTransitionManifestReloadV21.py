#!/usr/bin/env python3
"""Validate in-session terrain transition rule manifest reload wiring."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
checks: list[tuple[bool, str]] = []

def require(condition: bool, message: str) -> None:
    checks.append((condition, message))

def read(path: str) -> str:
    full = ROOT / path
    require(full.exists(), f"file exists: {path}")
    return full.read_text(encoding="utf-8") if full.exists() else ""

manifest_src = read("crates/haven_world/src/autotile/transition_rules_manifest.rs")
autotile_mod = read("crates/haven_world/src/autotile/mod.rs")
panel = read("crates/haven_game/src/transition_rule_editor_panel.rs")
input_rs = read("crates/haven_game/src/runtime_input.rs")

require("Mutex<&'static Result<TerrainTransitionRuleManifest, String>>" in manifest_src, "manifest cache uses a replaceable mutex-backed leaked snapshot")
require("TerrainTransitionRuleManifestReloadReport" in manifest_src, "reload report is defined world-side")
require("reload_terrain_transition_rule_manifest" in manifest_src, "world-side reload function exists")
require("TerrainTransitionRuleManifest::load_default()?" in manifest_src, "reload validates a fresh manifest before replacing cache")
require("*cached = fresh_result" in manifest_src, "reload swaps cached manifest after successful parse")
require("terrain_transition_rule_manifest_cache_summary" in manifest_src, "cache summary helper is exposed")
require("manifest_cache_can_reload_without_restart" in manifest_src, "unit coverage documents no-restart reload behavior")

for symbol in [
    "reload_terrain_transition_rule_manifest",
    "terrain_transition_rule_manifest_cache_summary",
    "TerrainTransitionRuleManifestReloadReport",
]:
    require(symbol in autotile_mod, f"autotile mod re-exports {symbol}")

require("reload_terrain_transition_rule_manifest" in panel, "transition rule editor imports reload function")
require("Reload" in panel, "transition rule editor exposes Reload button")
require("reload_transition_rule_manifest_cache" in panel, "game editor has reload action")
require("runtime cache reloads" in panel and "Reload refreshes live rules" in panel, "panel help text documents live reload")
require("match reload_terrain_transition_rule_manifest()" in panel, "promotion path refreshes cache after promotion")
require("KeyCode::R" in panel, "transition rule editor has reload hotkey")
require("self.editor_tab != EditorTab::Transitions" in input_rs, "global scene reset does not steal R from transition-rule reload tab")

failed = [message for ok, message in checks if not ok]
for ok, message in checks:
    print(f"{'PASS' if ok else 'FAIL'}: {message}")

if failed:
    print("\nTerrain transition manifest reload validation failed:")
    for message in failed:
        print(f" - {message}")
    sys.exit(1)

print("\nTerrain transition manifest reload validation passed.")
