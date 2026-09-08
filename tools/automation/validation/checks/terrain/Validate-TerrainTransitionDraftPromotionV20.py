#!/usr/bin/env python3
"""Validate transition-rule draft compare/promote workflow wiring."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
checks: list[tuple[bool, str]] = []

def require(condition: bool, message: str) -> None:
    checks.append((condition, message))

world_draft = ROOT / "crates" / "haven_world" / "src" / "autotile" / "transition_rule_draft.rs"
autotile_mod = ROOT / "crates" / "haven_world" / "src" / "autotile" / "mod.rs"
panel = ROOT / "crates" / "haven_game" / "src" / "transition_rule_editor_panel.rs"
live_manifest = ROOT / "content" / "worldgen" / "terrain_transition_rule_manifest_v0_1.json"
draft_manifest = ROOT / "WORKSPACE" / "generated" / "terrain_transition_rule_draft_v0_1.json"

world_text = world_draft.read_text(encoding="utf-8")
mod_text = autotile_mod.read_text(encoding="utf-8")
panel_text = panel.read_text(encoding="utf-8")

require("TransitionRuleDraftCompareReport" in world_text, "world draft module defines compare report")
require("TransitionRuleDraftPromotionReport" in world_text, "world draft module defines promotion report")
require("compare_transition_rule_draft_to_live" in world_text, "world draft module compares draft to live")
require("promote_transition_rule_draft_to_manifest" in world_text, "world draft module promotes draft deliberately")
require("TERRAIN_TRANSITION_RULE_LIVE_BACKUP_PATH" in world_text, "world draft module defines live backup path")
require("strip_draft_metadata_for_live_manifest" in world_text, "promotion strips safe-draft metadata before writing live manifest")
require("copy(&live_path, &backup_path)" in world_text, "promotion backs up live manifest before overwrite")
require("Restart/reload" in world_text or "restart/reload" in world_text, "promotion status warns about cached runtime manifest")
require("transition_rule_draft_compare_lines" in world_text, "world draft module exposes compact diff lines")

for symbol in [
    "compare_transition_rule_draft_to_live",
    "promote_transition_rule_draft_to_manifest",
    "transition_rule_draft_compare_lines",
    "transition_rule_draft_compare_status",
    "TransitionRuleDraftCompareReport",
    "TransitionRuleDraftPromotionReport",
    "TERRAIN_TRANSITION_RULE_LIVE_BACKUP_PATH",
]:
    require(symbol in mod_text, f"autotile mod re-exports {symbol}")

require("Compare" in panel_text, "transition rule editor panel has Compare button")
require("Promote" in panel_text, "transition rule editor panel has Promote button")
require("compare_transition_rule_draft" in panel_text, "panel calls compare workflow")
require("promote_transition_rule_draft" in panel_text, "panel calls promote workflow")
require("transition_rule_draft_compare_status" in panel_text, "panel draws compare status")
require("transition_rule_draft_compare_lines" in panel_text, "panel draws compact diff lines")
require("KeyCode::C" in panel_text, "transition rule editor exposes compare hotkey")

live = json.loads(live_manifest.read_text(encoding="utf-8"))
draft = json.loads(draft_manifest.read_text(encoding="utf-8"))
require(isinstance(live.get("rules"), list) and len(live["rules"]) > 0, "live manifest has rules")
require(isinstance(draft.get("rules"), list) and len(draft["rules"]) == len(live["rules"]), "draft has same starting rule count as live")
require(draft.get("draft", {}).get("safeDraft") is True, "draft manifest is marked safeDraft")

live_ids = [rule.get("id") for rule in live["rules"]]
draft_ids = [rule.get("id") for rule in draft["rules"]]
require(len(live_ids) == len(set(live_ids)), "live manifest rule ids are unique")
require(len(draft_ids) == len(set(draft_ids)), "draft manifest rule ids are unique")
require(set(live_ids) == set(draft_ids), "draft and live initially cover same rule ids")

failed = [message for ok, message in checks if not ok]
for ok, message in checks:
    print(f"{'PASS' if ok else 'FAIL'}: {message}")

if failed:
    print("\nTerrain transition draft promotion validation failed:")
    for message in failed:
        print(f" - {message}")
    sys.exit(1)

print("\nTerrain transition draft promotion workflow validation passed.")
