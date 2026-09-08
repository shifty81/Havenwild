#!/usr/bin/env python3
"""Validate Havenwild's ordinary cave-mouth geometry without changing runtime behavior.

The source artwork/host envelope is intentionally 1x3. The playable aperture contract is
1x2 inside that host, and the interaction/approach authority is one bottom cell. Keeping
those concepts separate prevents the source crop from being incorrectly resized or the
runtime opening from being treated as three traversable cells tall.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "content/worldgen/cliff_cave_mouth_policy_v0_1.json"
TOPOLOGY = ROOT / "content/worldgen/elizawy_cliff_topology_certification_v0_1.json"
PUBLISHED = ROOT / "content/asset_packs/havenwild_objects/published_world_assets_v1.json"
ESTATE = ROOT / "content/worldgen/scenes/home_island/farmstead_scene_v0_3.json"


def load(path: Path):
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def find_id(items, wanted: str):
    for item in items:
        if isinstance(item, dict) and item.get("id") == wanted:
            return item
    fail(f"missing id {wanted!r}")


def main() -> int:
    policy = load(POLICY)
    topology = load(TOPOLOGY)
    published = load(PUBLISHED)
    estate = load(ESTATE)

    default = policy.get("defaultCave", {})
    if default.get("sourceGridSpan") != [6, 9, 1, 3]:
        fail("ordinary cave sourceGridSpan must remain the exact authored [6,9,1,3] host")
    if default.get("visualWidthTiles") != 1:
        fail("ordinary cave host must remain one tile wide")

    topology_entry = find_id(topology.get("certifiedVisualRecipes", []), "elizawy.cave.narrow_host_1x3")
    if topology_entry.get("worldVisualFootprintTiles") != [1, 3]:
        fail("certified narrow cave source/host envelope must remain 1x3")

    published_entry = find_id(published.get("entries", []), "cave_entrance_default")
    footprint = published_entry.get("footprint", {})
    if footprint.get("visual_size") != [1, 3]:
        fail("published cave connector visual host must remain 1x3")
    if footprint.get("interaction_size") != [1, 1]:
        fail("published cave interaction authority must remain one bottom cell")

    open_state = next((s for s in published_entry.get("state_geometry", []) if s.get("state") == "open"), None)
    if not open_state:
        fail("published cave connector is missing open-state geometry")
    open_footprint = open_state.get("footprint", {})
    if open_footprint.get("collision_size") != [0, 0]:
        fail("open cave mouth must not leave a blocking collision cell in the aperture")
    if open_footprint.get("interaction_size") != [1, 1]:
        fail("open cave mouth must retain a 1x1 interaction trigger")

    estate_cave = find_id(estate.get("objects", []), "estate_cave_mouth")
    if estate_cave.get("visualRect", [None, None, None, None])[2:] != [1, 3]:
        fail("Estate cave source/host placement must remain 1x3")
    if estate_cave.get("collisionRect", [None, None, None, None])[2:] != [1, 1]:
        fail("Estate cave host collision authority must remain one bottom host cell")
    interactions = estate_cave.get("interactions", [])
    if not interactions or interactions[0].get("rect", [None, None, None, None])[2:] != [1, 1]:
        fail("Estate cave interaction approach must remain 1x1")

    rules = set(estate.get("validationRules", []))
    if "cave_aperture_is_1x2_on_level2_face" not in rules:
        fail("Estate scene must retain the explicit 1x2 visible cave-aperture acceptance rule")
    if "cave_transition_triggers_from_clear_approach_tile" not in rules:
        fail("Estate scene must retain clear-approach transition acceptance")

    print("PASS: ordinary cave mouth geometry is normalized as:")
    print("  certified source/host envelope : 1x3 tiles")
    print("  visible pass-through aperture  : 1x2 tiles")
    print("  interaction/approach authority : 1x1 bottom cell")
    print("  ordinary generated width       : 1 tile")
    return 0


if __name__ == "__main__":
    sys.exit(main())
