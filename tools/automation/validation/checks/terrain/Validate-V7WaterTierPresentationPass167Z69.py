#!/usr/bin/env python3
"""Validate Pass167Z69 source-pure V7 water-tier presentation authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
RUST = ROOT / "crates/haven_assets/src/lpc_mapped_terrain.rs"
PALETTE = ROOT / "crates/haven_assets/src/asset_palette.rs"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
AUTHORITY = ROOT / "content/worldgen/terrain_visual_family_authority_v0_1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"V7 water-tier presentation validation FAILED: {message}")


def tuple_set(payload: dict) -> set[tuple[str, str, str, str]]:
    return {
        (
            entry["corners"]["topLeft"],
            entry["corners"]["topRight"],
            entry["corners"]["bottomLeft"],
            entry["corners"]["bottomRight"],
        )
        for entry in payload["entries"]
    }


def contains_pair(tuples: set[tuple[str, str, str, str]], first: str, second: str) -> bool:
    return any(first in corners and second in corners for corners in tuples)


def main() -> None:
    rust = RUST.read_text(encoding="utf-8")
    palette = PALETTE.read_text(encoding="utf-8")
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    tuples = tuple_set(atlas)

    require(
        'return Some("Water");' in rust
        and "touches_same_domain_shallow_water" in rust,
        "deep cells beside same-domain shallows must derive the V7 medium-water presentation rim",
    )
    require(
        'TileKind::OceanDeep => neighbor == TileKind::OceanShallow' in rust,
        "ocean presentation rim must preserve raw ocean identity",
    )
    require(
        'matches!(neighbor, TileKind::ShallowWater | TileKind::Water)' in rust,
        "freshwater medium-rim contact policy is missing",
    )
    require(
        '"Water_Shallows_Sand"' in rust,
        "V7 ocean shallows must participate in authored water animation",
    )
    require(
        (
            "retired_legacy_aliases = 1" in palette
            or "non_paintable_state_tiles = 2" in palette
        )
        and 'catalog.entry("tile/wet_sand").is_none()' in palette,
        "palette coverage must explicitly exclude the retired WetSand brush alias",
    )

    require(
        not contains_pair(tuples, "Water_Deep", "Water_Shallows_Dirt"),
        "the atlas unexpectedly contains a direct freshwater shallow/deep tuple; re-audit source semantics",
    )
    require(
        not contains_pair(tuples, "Water_Deep", "Water_Shallows_Sand"),
        "the atlas unexpectedly contains a direct ocean-shallow/deep tuple; re-audit source semantics",
    )
    require(
        contains_pair(tuples, "Water", "Water_Deep"),
        "V7 atlas lacks the required medium/deep authored tuples",
    )
    require(
        contains_pair(tuples, "Water", "Water_Shallows_Dirt"),
        "V7 atlas lacks the required freshwater shallow/medium authored tuples",
    )
    require(
        contains_pair(tuples, "Water", "Water_Shallows_Sand"),
        "V7 atlas lacks the required ocean shallow/medium authored tuples",
    )

    require(authority.get("version", 0) >= 6, "terrain visual authority version was not advanced")
    v7 = next(f for f in authority["families"] if f["id"] == "lpc_terrain_v7_island_v1")
    presentation = v7.get("waterTierPresentation", {})
    require(
        presentation.get("sequence")
        == ["Water_Shallows_Dirt_or_Sand", "Water", "Water_Deep"],
        "V7 three-tier water presentation sequence is missing",
    )
    require(
        presentation.get("semanticMutation") is False,
        "presentation rim must not rewrite freshwater/ocean gameplay identity",
    )

    print("V7 water-tier presentation authority validated")
    print("- direct shallow/deep tuple: absent by source")
    print("- shallow/medium and medium/deep tuples: present")
    print("- derived medium rim: enabled without semantic mutation")
    print("- WetSand palette alias: retired")


if __name__ == "__main__":
    main()
