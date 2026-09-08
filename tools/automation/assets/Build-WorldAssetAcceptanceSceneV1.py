#!/usr/bin/env python3
"""Build the W43A diagnostic world-asset acceptance scene from PublishedWorldAsset records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CATALOG_REL = Path("content/asset_packs/havenwild_objects/published_world_assets_v1.json")
OUTPUT_REL = Path("content/worldgen/scenes/world_asset_acceptance/world_asset_acceptance_scene_v1.json")
SCENE_W = 64
SCENE_H = 48

LANES = [
    ("trees", 8, ["oak_tree", "oak_tree_variant_02", "oak_tree_variant_03", "oak_tree_variant_04", "oak_tree_variant_05", "oak_tree_variant_06", "oak_tree_variant_07", "oak_tree_variant_08"], 6, 7),
    ("berry_bushes", 16, ["berry_bush", "berry_bush_variant_02", "berry_bush_variant_03", "berry_bush_variant_04"], 8, 6),
    ("boulders", 22, ["boulder", "boulder_variant_02", "boulder_variant_03", "boulder_variant_04"], 8, 7),
    ("mushrooms", 28, ["forage_mushroom", "forage_mushroom_variant_02", "forage_mushroom_variant_03", "forage_mushroom_variant_04"], 8, 6),
    ("herbs", 34, ["wild_herb", "wild_herb_variant_02", "wild_herb_variant_03"], 8, 6),
    ("wildflowers", 34, ["wildflower_patch", "wildflower_patch_variant_02", "wildflower_patch_variant_03"], 32, 6),
    ("reeds", 40, ["reed_patch", "reed_patch_variant_02"], 8, 6),
    ("fallen_log", 40, ["fallen_log"], 26, 6),
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rect(anchor_x: int, anchor_y: int, offset: list[int], size: list[int]) -> list[int]:
    return [anchor_x + offset[0], anchor_y + offset[1], size[0], size[1]]


def object_record(entry: dict, alias: str, x: int, y: int, lane: str) -> dict:
    fp = entry["footprint"]
    visual_offset = fp.get("visual_offset", [0, 0])
    collision_offset = fp.get("collision_offset", [0, 0])
    interaction_offset = fp.get("interaction_offset", [0, 0])
    visual = rect(x, y, visual_offset, fp["visual_size"])
    collision = rect(x, y, collision_offset, fp["collision_size"])
    interaction = rect(x, y, interaction_offset, fp["interaction_size"])
    return {
        "id": f"accept_{alias}",
        "assetId": alias,
        "publishedAssetId": entry["id"],
        "acceptanceLane": lane,
        "visualRect": visual,
        "collisionRect": collision,
        "layer": "tall_object" if entry.get("category") == "tree" else "low_object",
        "blocksMovement": bool(fp.get("blocks_movement", True)),
        "occludesPlayer": bool(fp.get("occludes_player", False)),
        "fadeWhenPlayerBehind": bool(fp.get("fade_when_player_behind", False)),
        "interactions": [
            {
                "id": f"inspect_{alias}",
                "kind": "inspect",
                "rect": interaction,
            }
        ],
        "acceptance": {
            "certification": entry.get("certification"),
            "sourceAuthority": entry.get("provenance", {}).get("authority"),
            "sourcePath": entry.get("provenance", {}).get("source_path"),
            "sourceRect": entry.get("provenance", {}).get("source_rect"),
            "runtimeCacheRect": entry.get("visual", {}).get("frames", [{}])[0].get("source_rect"),
            "footAnchorPixels": entry.get("visual", {}).get("foot_anchor"),
        },
    }


def build(root: Path) -> dict:
    catalog = load(root / CATALOG_REL)
    entries = catalog.get("entries", [])
    by_alias = {
        alias: entry
        for entry in entries
        for alias in entry.get("aliases", [])
    }
    objects = []
    lane_meta = []
    for lane, y, aliases, start_x, step_x in LANES:
        lane_items = []
        for index, alias in enumerate(aliases):
            if alias not in by_alias:
                raise RuntimeError(f"W43A acceptance alias is not published: {alias}")
            entry = by_alias[alias]
            x = start_x + index * step_x
            objects.append(object_record(entry, alias, x, y, lane))
            lane_items.append({"alias": alias, "publishedAssetId": entry["id"], "anchor": [x, y]})
        lane_meta.append({"lane": lane, "anchorY": y, "items": lane_items})

    terrain = [["grass" for _ in range(SCENE_W)] for _ in range(SCENE_H)]
    zones = [["none" for _ in range(SCENE_W)] for _ in range(SCENE_H)]
    return {
        "id": "world_asset_acceptance_scene_v1",
        "version": "1.0.0",
        "kind": "worldgen_scene",
        "sceneId": "world_asset_acceptance",
        "title": "World Asset Acceptance — W43A",
        "sceneKind": "exterior",
        "biome": "temperate",
        "role": "diagnostic_only",
        "sceneSize": [SCENE_W, SCENE_H],
        "tileSize": [32, 32],
        "edgePolicy": {
            "mustAvoidVoid": True,
            "resolvedBorders": {"north": "grass", "south": "grass", "east": "grass", "west": "grass"},
        },
        "layers": {"terrain": terrain, "zones": zones},
        "objects": objects,
        "transitions": [],
        "spawns": [{"id": "player_default", "kind": "player", "tile": [4, 44]}],
        "editor": {
            "showLayers": ["terrain", "objects", "collision", "interactions"],
            "defaultTool": "inspect_select",
            "allowPaintTerrain": False,
            "allowMoveObjects": True,
        },
        "acceptance": {
            "milestone": "Pass167Z109W43A",
            "productionRegistered": False,
            "publishedCatalog": CATALOG_REL.as_posix(),
            "assetCount": len(objects),
            "lanes": lane_meta,
            "visualAssertions": [
                "each published alias renders its own exact runtime-cache frame",
                "bottom-center/source foot anchor lands on the authored object anchor",
                "tree trunks align to the one-tile collision/root cell",
                "variants remain visually distinct instead of collapsing to generic ObjectKind art",
            ],
            "gameplayAssertions": [
                "collision and interaction rectangles match the published footprint",
                "walk-behind/fade behavior follows published metadata",
                "scene aliases canonicalize to PublishedWorldAsset stable refs after asset mounting",
            ],
        },
        "validationRules": [
            "all_w42_scene_candidates_present_once",
            "no_w41_scene_blockers_promoted",
            "published_footprints_match_scene_rects",
            "scene_aliases_resolve_to_published_records",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.root.resolve()
    scene = build(root)
    output = root / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    print(f"W43A world asset acceptance scene: {len(scene['objects'])} assets -> {OUTPUT_REL.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
