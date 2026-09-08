#!/usr/bin/env python3
"""Validate the safe transition-rule draft editing/export pass.

This pass must keep runtime transition behavior manifest-driven while routing
in-game edits into WORKSPACE/generated draft JSON instead of mutating the live
content/worldgen manifest directly.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
LOG = ROOT / "logs" / "terrain_transition_draft_editor_v19_validation_report.json"
CHECKS = []

REQUIRED_DRAFT_FIELDS = {"priority", "material", "atlasGroup", "center", "neighbor"}
VALID_PHASES = {"edge", "corner"}
VALID_MATERIALS = {
    "wet_sand",
    "foam",
    "shallow_water_edge",
    "sand_blend",
    "grass_fringe",
    "dirt_blend",
    "road_shoulder",
    "stone_shoulder",
    "rock_shadow",
}
VALID_SELECTORS = {
    "grass",
    "dirt",
    "sand",
    "road",
    "wood_floor",
    "stone_floor",
    "farm",
    "water",
    "rock_wall",
    "cave",
    "greenhouse",
    "void",
    "land",
    "soft_natural",
    "constructed",
    "blocking_wall",
    "non_blocking_wall",
    "any",
}


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


def validate_rules(data: dict, label: str) -> int:
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise AssertionError(f"{label} needs a non-empty rules array")
    seen = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise AssertionError(f"{label} rule {index} is not an object")
        rid = rule.get("id")
        if not isinstance(rid, str) or not rid:
            raise AssertionError(f"{label} rule {index} has invalid id")
        if rid in seen:
            raise AssertionError(f"{label} duplicate rule id: {rid}")
        seen.add(rid)
        for key in ["center", "neighbor", "material", "atlasGroup", "appliesTo", "priority"]:
            if key not in rule:
                raise AssertionError(f"{label} rule {rid} missing {key}")
        if rule["center"] not in VALID_SELECTORS:
            raise AssertionError(f"{label} rule {rid} has invalid center {rule['center']}")
        if rule["neighbor"] not in VALID_SELECTORS:
            raise AssertionError(f"{label} rule {rid} has invalid neighbor {rule['neighbor']}")
        if rule["material"] not in VALID_MATERIALS:
            raise AssertionError(f"{label} rule {rid} has invalid material {rule['material']}")
        if not isinstance(rule["priority"], int):
            raise AssertionError(f"{label} rule {rid} priority is not an integer")
        phases = rule["appliesTo"]
        if not isinstance(phases, list) or not phases or not set(phases).issubset(VALID_PHASES):
            raise AssertionError(f"{label} rule {rid} has invalid appliesTo {phases!r}")
    return len(rules)


def main() -> None:
    draft_rs = require_file("crates/haven_world/src/autotile/transition_rule_draft.rs")
    mod_rs = require_file("crates/haven_world/src/autotile/mod.rs")
    panel_rs = require_file("crates/haven_game/src/transition_rule_editor_panel.rs")
    live_data = json.loads(require_file("content/worldgen/terrain_transition_rule_manifest_v0_1.json"))
    draft_data = json.loads(require_file("WORKSPACE/generated/terrain_transition_rule_draft_v0_1.json"))

    for needle in [
        "TERRAIN_TRANSITION_RULE_DRAFT_PATH",
        "TransitionRuleDraftEdit",
        "export_transition_rule_draft_from_manifest",
        "apply_transition_rule_draft_edit",
        "transition_rule_draft_selected_summary",
        "validate_transition_rule_draft_value",
        "WORKSPACE/generated",
    ]:
        require(draft_rs, needle, f"draft module hook {needle}")

    for needle in [
        "pub mod transition_rule_draft;",
        "apply_transition_rule_draft_edit",
        "export_transition_rule_draft_from_manifest",
        "TransitionRuleDraftEdit",
        "TERRAIN_TRANSITION_RULE_DRAFT_PATH",
    ]:
        require(mod_rs, needle, f"autotile draft export {needle}")

    for needle in [
        "Draft",
        "Pri-",
        "Pri+",
        "Mat+",
        "Ctr+",
        "Nbr+",
        "Atlas",
        "apply_selected_transition_rule_draft_edit",
        "transition_rule_draft_status",
        "transition_rule_draft_selected_summary",
        "Promote to live manifest manually after review",
    ]:
        require(panel_rs, needle, f"editor panel draft UI {needle}")

    live_count = validate_rules(live_data, "live manifest")
    draft_count = validate_rules(draft_data, "draft manifest")
    if draft_count != live_count:
        raise AssertionError("seed draft should initially mirror the live manifest rule count")
    draft_meta = draft_data.get("draft")
    if not isinstance(draft_meta, dict) or not draft_meta.get("safeDraft"):
        raise AssertionError("draft manifest missing safeDraft metadata")
    editable = set(draft_meta.get("editableFields", []))
    missing_fields = REQUIRED_DRAFT_FIELDS - editable
    if missing_fields:
        raise AssertionError(f"draft metadata missing editable fields: {sorted(missing_fields)}")

    CHECKS.append({"check": "live rules valid", "status": "ok", "count": live_count})
    CHECKS.append({"check": "draft rules valid", "status": "ok", "count": draft_count})
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps({
        "schema": "havenwild.validation.terrain_transition_draft_editor.v19",
        "status": "passed",
        "checks": CHECKS,
    }, indent=2), encoding="utf-8")
    print(f"Terrain transition draft editor validation passed: {len(CHECKS)} checks")


if __name__ == "__main__":
    main()
