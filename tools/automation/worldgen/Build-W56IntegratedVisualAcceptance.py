#!/usr/bin/env python3
"""Build the W56I/J integrated visual acceptance scene.

This is a diagnostic-only scene. It deliberately combines the production
starter-cottage BuildingInstance path, discrete 1-4 structural levels, certified
natural placeables, a narrow cave-mouth connector, walkable paths, and water in
one deterministic board. It does not become normal world-generation authority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "content/worldgen/scenes/world_asset_acceptance/w56_integrated_visual_acceptance_scene_v1.json"
REGISTRY = ROOT / "content/asset_packs/havenwild_objects/published_world_assets_v1.json"
W, H = 96, 64


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


published = {entry["id"]: entry for entry in load(REGISTRY)["entries"]}
terrain = [["Grass" for _ in range(W)] for _ in range(H)]
levels = [[0 for _ in range(W)] for _ in range(H)]
zones = [["none" for _ in range(W)] for _ in range(H)]

# A readable stone path connects player spawn to the diagnostic starter cottage.
for y in range(46, 59):
    for x in range(47, 50):
        terrain[y][x] = "StonePath"
for x in range(42, 55):
    terrain[46][x] = "StonePath"

# Compact water feature proves water/shore readability without taking over the board.
for y in range(45, 58):
    for x in range(5, 22):
        dx = (x - 13) / 8.0
        dy = (y - 51) / 6.0
        r = dx * dx + dy * dy
        if r <= 1.0:
            terrain[y][x] = "ShallowWater" if r > 0.45 else "Water"
        elif r <= 1.35:
            terrain[y][x] = "Sand"

# Four independent structural plateaus make 1/2/3/4 height visually comparable.
plateaus = [
    (5, 6, 16, 16, 1),
    (22, 6, 33, 16, 2),
    (39, 6, 50, 16, 3),
    (56, 6, 67, 16, 4),
]
for x0, y0, x1, y1, level in plateaus:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            terrain[y][x] = "MountainRock"
            levels[y][x] = level

# Dedicated Level-2 cliff host for the cave entrance, well separated from comparison bands.
for y in range(7, 23):
    for x in range(73, 84):
        terrain[y][x] = "MountainRock"
        levels[y][x] = 2

# Small terrain texture lanes make scene identity obvious at a glance.
for x in range(25, 39):
    terrain[31][x] = "Dirt"
for x in range(58, 72):
    terrain[33][x] = "TallGrass"

objects = []


def place(asset_id: str, object_id: str, anchor_x: int, anchor_y: int, *, state=None, interaction_kind="inspect"):
    entry = published[asset_id]
    fp = entry["footprint"]
    vo = fp.get("visual_offset", [0, 0])
    vs = fp.get("visual_size", [1, 1])
    co = fp.get("collision_offset", [0, 0])
    cs = fp.get("collision_size", [1, 1])
    io = fp.get("interaction_offset", [0, 0])
    ins = fp.get("interaction_size", [1, 1])
    obj = {
        "id": object_id,
        "assetId": asset_id,
        "visualRect": [anchor_x + vo[0], anchor_y + vo[1], vs[0], vs[1]],
        "collisionRect": [anchor_x + co[0], anchor_y + co[1], cs[0], cs[1]],
        "layer": "tall_object" if entry.get("category") in {"tree", "cave"} else "low_object",
        "blocksMovement": bool(fp.get("blocks_movement", False)),
        "occludesPlayer": bool(fp.get("occludes_player", False)),
        "fadeWhenPlayerBehind": bool(fp.get("fade_when_player_behind", False)),
        "interactions": [{
            "id": f"inspect_{object_id}",
            "kind": interaction_kind,
            "rect": [anchor_x + io[0], anchor_y + io[1], ins[0], ins[1]],
        }],
    }
    if state is not None:
        obj["state"] = state
    objects.append(obj)


# Certified nature gallery around the board. Every anchor is kept away from paths/building/cliffs.
trees = [
    ("tree_oak_mature_01", 8, 31), ("tree_oak_mature_02", 14, 34),
    ("tree_oak_mature_03", 20, 29), ("tree_oak_mature_04", 27, 37),
    ("tree_oak_mature_05", 34, 29), ("tree_oak_mature_06", 64, 29),
    ("tree_oak_mature_07", 72, 36), ("tree_oak_mature_08", 85, 33),
]
for index, (asset, x, y) in enumerate(trees, 1):
    place(asset, f"w56_tree_{index:02d}", x, y, state="mature")

for index, (asset, x, y) in enumerate([
    ("shrub_berry_01", 11, 39), ("shrub_berry_02", 18, 37),
    ("shrub_berry_03", 69, 42), ("shrub_berry_04", 82, 39),
    ("resource_boulder_01", 29, 27), ("resource_boulder_03", 78, 31),
    ("tree_fallen_log_01", 33, 53), ("forage_mushroom_02", 24, 43),
    ("forage_wild_herb_01", 59, 48), ("flora_wildflower_03", 67, 51),
    ("container_crate_wood_01", 53, 49),
], 1):
    place(asset, f"w56_object_{index:02d}", x, y, state="closed" if asset == "container_crate_wood_01" else None)

# Narrow certified cave source is 1x3; visible/interactive opening remains 1x2.
place("cave_entrance_default", "w56_integrated_cave_mouth", 78, 23, state="open", interaction_kind="inspect")
objects[-1]["collisionRect"] = [78, 23, 0, 0]
objects[-1]["blocksMovement"] = False
objects[-1]["interactions"] = [{"id": "inspect_w56_cave_aperture", "kind": "inspect", "rect": [78, 22, 1, 2]}]

scene = {
    "id": "w56_integrated_visual_acceptance_scene_v1",
    "version": "1.0.0-w56ij",
    "kind": "worldgen_scene",
    "sceneId": "w56_integrated_visual_acceptance",
    "title": "W56 Integrated Visual Acceptance",
    "sceneKind": "exterior",
    "biome": "temperate",
    "role": "development_acceptance",
    "sceneSize": [W, H],
    "tileSize": [32, 32],
    "edgePolicy": "bounded",
    "layers": {"terrain": terrain, "structuralLevels": levels, "zones": zones},
    "objects": objects,
    "transitions": [],
    "spawns": [{"id": "player_default", "tile": [48, 57]}],
    "editor": {
        "showLayers": ["terrain", "structural_levels", "objects", "collision"],
        "defaultTool": "inspect_select",
        "notes": [
            "W56I/J permanent diagnostic board: editor and client consume this exact scene.",
            "The starter cottage is materialized from BuildingInstanceRegistry and is intentionally not baked into objects.",
            "Cliff comparison bands exercise requested structural heights 1, 2, 3 and 4 through the shared resolver.",
            "Only published/certified object identities are placed on this board.",
        ],
    },
    "acceptance": {
        "pass": "167Z109W56IJ",
        "status": "SOURCE_READY_BUILD_PENDING",
        "buildingInstanceId": "havenwild.acceptance.w56_integrated_cottage",
        "buildingRecipeId": "havenwild.estate.starter_cottage",
        "buildingAnchorTile": [43, 39],
        "cliffHeights": [1, 2, 3, 4],
        "caveHostSourceTiles": [1, 3],
        "caveVisibleApertureTiles": [1, 2],
        "naturalObjectMinimum": 16,
        "exactAssetIdentityRequired": True,
        "editorRuntimeSceneParityRequired": True,
    },
    "validationRules": [
        "editor and client load one identical scene JSON and shared structural cliff resolver",
        "starter cottage materializes through BuildingInstanceRegistry + BuildingRecipeRegistry",
        "structural levels 1/2/3/4 remain discrete and are never clamped to level 2",
        "cave source remains 1x3 while visible aperture remains 1x2",
        "all visible object assets are present in PublishedWorldAssetRegistry",
        "tree anchors remain bottom-center with 1x1 collision roots",
        "diagnostic board never becomes production world-generation authority",
    ],
}
save(OUT, scene)
print(f"W56I/J integrated visual acceptance scene: {OUT.relative_to(ROOT).as_posix()} ({len(objects)} objects)")
