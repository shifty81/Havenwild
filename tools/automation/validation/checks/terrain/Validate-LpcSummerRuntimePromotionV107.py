#!/usr/bin/env python3
"""Validate Pass 95 summer runtime promotion and semantic separation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def data(path: str) -> dict:
    return json.loads(text(path))


def require(haystack: str, needles: list[str], label: str) -> None:
    missing = [needle for needle in needles if needle not in haystack]
    if missing:
        raise AssertionError(f"{label} missing: {missing}")


def main() -> int:
    family = text("crates/haven_world/src/autotile/terrain_family.rs")
    require(
        family,
        [
            "WetSand,",
            "PebblePath,",
            "TileKind::WetSand => Self::WetSand",
            "TileKind::PebbleShore | TileKind::StonePath => Self::PebblePath",
            'Self::WetSand => "wet_sand"',
            'Self::PebblePath => "pebble_path"',
        ],
        "terrain family separation",
    )

    groups = text("crates/haven_world/src/autotile/transition_atlas_groups.rs")
    require(groups, ["sand_over_wet_sand", "pebble_path_over_dirt"], "atlas group routing")

    mapping = data("content/assets/intake/lpc_terrain_family_mapping_v0_3.json")
    family_ids = {item["id"]: item for item in mapping["transitionFamilies"]}
    for group_id in ("sand_over_wet_sand", "pebble_path_over_dirt"):
        if group_id not in family_ids:
            raise AssertionError(f"missing runtime transition family {group_id}")
    if family_ids["pebble_path_over_dirt"].get("innerCornerBlock") is not None:
        raise AssertionError("pebble path must remain outer-role-only until a verified 2x2 block exists")

    atlas = data("assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json")
    for group_id in ("sand_over_wet_sand", "pebble_path_over_dirt"):
        if group_id not in atlas["groups"]:
            raise AssertionError(f"generated atlas missing {group_id}")
        masks = {entry["mask4"] for entry in atlas["variants"] if entry["group"] == group_id}
        if masks != set(range(16)):
            raise AssertionError(f"{group_id} outer mask coverage is incomplete: {sorted(masks)}")
    dry_wet_inner = [entry for entry in atlas["innerCornerVariants"] if entry["group"] == "sand_over_wet_sand"]
    if len(dry_wet_inner) != 4:
        raise AssertionError("dry/wet sand must expose all four authored inner corners")
    pebble_inner = [entry for entry in atlas["innerCornerVariants"] if entry["group"] == "pebble_path_over_dirt"]
    if pebble_inner:
        raise AssertionError("pebble path emitted unverified inner corners")

    source_map = data("assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json")
    status = {cell.get("groupId"): cell.get("runtimeStatus") for cell in source_map["cells"] if cell.get("groupId")}
    for group_id in ("summer_sand_over_wet_sand", "summer_pebble_path_over_dirt", "summer_pebble_path_fill"):
        if status.get(group_id) != "active":
            raise AssertionError(f"{group_id} is not marked active")

    preview = ROOT / "docs/assets/previews/havenwild_lpc_summer_runtime_conformance_v107.png"
    if not preview.is_file() or preview.stat().st_size < 1024:
        raise AssertionError("summer runtime conformance preview missing")

    print("V107 OK: distinct wet-sand and pebble-path families are promoted with verified LPC topology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
