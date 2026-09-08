#!/usr/bin/env python3
"""Validate the LPC placeable-object promotion plan."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PLAN = ROOT / "content/assets/lpc/lpc_placeable_object_promotion_plan_v0_1.json"
ASSET_PALETTE = ROOT / "crates/haven_assets/src/asset_palette.rs"
ASSET_REGISTRY = ROOT / "crates/haven_assets/src/asset_registry.rs"
CATALOG = ROOT / "crates/haven_core/src/foundation/tile_object_catalog.rs"

REQUIRED_METADATA = {
    "stableId",
    "label",
    "category",
    "objectKind",
    "placementLane",
    "sourcePack",
    "sourceFile",
    "sourceRect",
    "runtimeAtlas",
    "atlasRect",
    "visualFootprint",
    "collisionFootprint",
    "interactionFootprint",
    "anchor",
    "walkability",
    "occlusion",
    "interaction",
    "license",
    "attribution",
    "editorTags",
    "paletteGroup",
    "promotionStatus",
}

EXPECTED_GROUPS = {
    "nature_foraging",
    "town_props",
    "tavern_interior",
    "building_transitions",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require_text(path: str, needles: list[str]) -> None:
    payload = read(path)
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V119: {path} missing {missing}")


def object_code_map() -> dict[str, str]:
    payload = CATALOG.read_text(encoding="utf-8")
    return {
        variant: code
        for variant, code in re.findall(r"ObjectKind::(\w+)\s*=>\s*\"([a-z_]+)\"", payload)
    }


def palette_object_codes() -> list[str]:
    payload = ASSET_PALETTE.read_text(encoding="utf-8")
    match = re.search(
        r"pub const PALETTE_OBJECTS:\s*\[ObjectKind;\s*26\]\s*=\s*\[(.*?)\];",
        payload,
        re.S,
    )
    if not match:
        raise SystemExit("V119: PALETTE_OBJECTS array was not found or no longer has 26 entries")
    variants = re.findall(r"ObjectKind::(\w+)", match.group(1))
    code_map = object_code_map()
    missing = sorted(set(variants) - set(code_map))
    if missing:
        raise SystemExit(f"V119: missing ObjectKind code mappings for {missing}")
    return [code_map[variant] for variant in variants]


def main() -> int:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan.get("version") != "0.1.0":
        raise SystemExit("V119: expected placeable object promotion plan version 0.1.0")
    if plan.get("tileSize") != 32:
        raise SystemExit("V119: object promotion plan must target 32px tile anchors")

    safety = " ".join(plan.get("runtimeSafety", [])).lower()
    for needle in [
        "promotion contract only",
        "does not change renderer placement behavior",
        "must not expose unverified source-pack assets",
    ]:
        if needle not in safety:
            raise SystemExit(f"V119: runtime safety missing '{needle}'")

    required = set(plan["requiredPromotedMetadata"])
    missing_metadata = sorted(REQUIRED_METADATA - required)
    if missing_metadata:
        raise SystemExit(f"V119: required metadata missing {missing_metadata}")

    palette_codes = palette_object_codes()
    if len(palette_codes) != 26 or len(set(palette_codes)) != 26:
        raise SystemExit("V119: PALETTE_OBJECTS must expose 26 unique object codes")

    promoted = plan["objectPromotion"]
    promoted_codes = [entry["objectKind"] for entry in promoted]
    if promoted_codes != palette_codes:
        raise SystemExit(
            "V119: object promotion list must match PALETTE_OBJECTS order "
            f"expected={palette_codes} found={promoted_codes}"
        )

    group_ids = {group["id"] for group in plan["paletteGroups"]}
    if group_ids != EXPECTED_GROUPS:
        raise SystemExit(f"V119: palette groups mismatch {sorted(group_ids)}")
    grouped_codes = [
        code
        for group in plan["paletteGroups"]
        for code in group["objectKinds"]
    ]
    if set(grouped_codes) != set(palette_codes) or len(grouped_codes) != len(set(grouped_codes)):
        raise SystemExit("V119: palette groups must cover every object exactly once")

    for entry in promoted:
        if entry["paletteGroup"] not in group_ids:
            raise SystemExit(f"V119: {entry['objectKind']} uses unknown palette group")
        if not entry.get("sourceCandidates"):
            raise SystemExit(f"V119: {entry['objectKind']} has no source candidates")
        if not entry.get("promotionStatus"):
            raise SystemExit(f"V119: {entry['objectKind']} has no promotion status")

    registry = ASSET_REGISTRY.read_text(encoding="utf-8")
    if 'ObjectKind::CaveEntrance => return None' not in registry:
        raise SystemExit("V119: cave_entrance must remain stamp-required until a stamp manifest exists")
    cave = next(entry for entry in promoted if entry["objectKind"] == "cave_entrance")
    if cave["placementLane"] != "stamp_required":
        raise SystemExit("V119: cave_entrance must use the stamp_required lane")
    if cave["currentBinding"] != "missing_runtime_object_binding":
        raise SystemExit("V119: cave_entrance must record its missing object binding")

    object_bound = [entry for entry in promoted if entry["objectKind"] != "cave_entrance"]
    for entry in object_bound:
        pascal = "".join(part.capitalize() for part in entry["objectKind"].split("_"))
        if entry["objectKind"] == "ore_node":
            pascal = "OreNode"
        elif entry["objectKind"] == "greenhouse_marker":
            pascal = "GreenhouseMarker"
        if f"ObjectKind::{pascal} => (" not in registry:
            raise SystemExit(f"V119: {entry['objectKind']} is not covered by object_asset_entry")

    require_text(
        "content/editor/stamps/generic_multitile_stamp_contract_v0_1.json",
        [
            "Click to place as one typed undo transaction",
            "TavernMap::is_cell_walkable checks blocking stamp footprint",
        ],
    )
    require_text(
        "docs/PASS107_LPC_PLACEABLE_OBJECT_PROMOTION_20260713.md",
        [
            "The missing piece is promotion metadata",
            "`cave_entrance` is intentionally marked `stamp_required`",
            "Validate place, save, load, select, move, erase, collision, and interaction",
        ],
    )

    print("V119 OK: placeable object promotion covers all 26 palette objects and keeps cave entrance stamp-required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
