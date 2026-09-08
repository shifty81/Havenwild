#!/usr/bin/env python3
"""Materialize the default continuous open-world biome slice.

The historical file name is retained so existing build entrypoints remain stable.
Pass 167Z38 keeps the open-world Willowmere-outskirts slice and derives every
freshwater/ocean band from the exact material pairs already authored in
terrain-map-v7. Runtime code selects those committed tiles; it does not rebuild
shoreline geometry from quarter cells. The historical script
and evidence filenames remain stable for build compatibility. Farms, taverns,
shops, and other businesses remain player/city placement systems rather than
baked terrain fixtures.
"""
from __future__ import annotations

from collections import Counter, deque
import json
import math
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SCENE = ROOT / "content/worldgen/scenes/open_world/willowmere_outskirts_region_v0_1.json"
CONTRACT = ROOT / "content/worldgen/client_test_world_materialization_v0_3.json"
PREVIEW = ROOT / "docs/audits/generated/havenwild_open_world_biome_semantic_map_v167z38.png"
METRICS = ROOT / "docs/audits/generated/havenwild_open_world_biome_v167z38_metrics.json"
SEED = 167_260_826
WIDTH = 96
HEIGHT = 64

WATER = {"ShallowWater", "Water", "DeepWater", "OceanShallow", "OceanDeep"}
SHORE = {"MudBank", "Sand"}
ROUTES = {"Road"}
FORBIDDEN_STATIC_TERRAIN = {
    "TilledSoil",
    "WateredSoil",
    "Crop",
    "MountainRock",
    "MountainPath",
    "Cliff",
    "PebbleShore",
    "Bridge",
    "StonePath",
    "ShoreFoam",
    "RiverMouthBlend",
}

PREVIEW_COLORS = {
    "Grass": (52, 132, 54, 255),
    "TallGrass": (62, 145, 60, 255),
    "Road": (170, 129, 78, 255),
    "Sand": (225, 199, 137, 255),
    "MudBank": (119, 87, 56, 255),
    "ShallowWater": (53, 153, 183, 255),
    "DeepWater": (25, 75, 119, 255),
    "OceanShallow": (48, 145, 177, 255),
    "OceanDeep": (20, 58, 94, 255),
}


def hash01(x: int, y: int, salt: int = 0) -> float:
    value = (x * 374761393 + y * 668265263 + salt * 2147483647 + SEED) & 0xFFFFFFFF
    value = (value ^ (value >> 13)) * 1274126177 & 0xFFFFFFFF
    value ^= value >> 16
    return value / 0xFFFFFFFF


def neighbors4(x: int, y: int):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
            yield nx, ny


def neighbors8(x: int, y: int):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT:
                yield nx, ny


def smooth_coast(values: list[int]) -> list[int]:
    values = values[:]
    for _ in range(5):
        median = values[:]
        for y in range(1, HEIGHT - 1):
            median[y] = sorted(values[y - 1 : y + 2])[1]
        for y in range(1, HEIGHT):
            median[y] = max(median[y - 1] - 1, min(median[y - 1] + 1, median[y]))
        for y in range(HEIGHT - 2, -1, -1):
            median[y] = max(median[y + 1] - 1, min(median[y + 1] + 1, median[y]))
        values = median
    return values


def generate_coast(terrain: list[list[str]]) -> list[int]:
    coast = [
        max(
            72,
            min(
                80,
                76
                + round(math.sin(y * 0.19) * 2.0)
                + round(math.sin(y * 0.071 + 1.1) * 1.5)
                + round((hash01(0, y, 17) - 0.5) * 1.4),
            ),
        )
        for y in range(HEIGHT)
    ]
    coast = smooth_coast(coast)
    for y, edge in enumerate(coast):
        for x in range(max(0, edge - 6), WIDTH):
            distance = x - edge
            if distance <= -1:
                terrain[y][x] = "Sand"
            elif distance <= 2:
                terrain[y][x] = "OceanShallow"
            elif distance <= 6:
                terrain[y][x] = "Water"
            else:
                terrain[y][x] = "OceanDeep"
    return coast


def generate_lake(terrain: list[list[str]]) -> None:
    # Build all freshwater bands from one rotated signed-distance contour.
    # The previous dilation of a symmetric deep core created obvious north,
    # south, east, and west shelves even when the LPC corner roles were valid.
    # Rotation plus low-amplitude angular variation avoids axis-aligned cardinal
    # plateaus while preserving a deterministic, continuous natural lake.
    cx, cy = 27.0, 44.0
    rx, ry = 8.8, 5.8
    angle = math.radians(17.0)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)

    for y in range(max(0, int(cy - ry - 7)), min(HEIGHT, int(cy + ry + 8))):
        for x in range(max(0, int(cx - rx - 7)), min(WIDTH, int(cx + rx + 8))):
            # Evaluate at cell centers so the contour does not bias whole rows
            # or columns at integer coordinates.
            world_x = x + 0.5 - cx
            world_y = y + 0.5 - cy
            local_x = (world_x * cos_angle + world_y * sin_angle) / rx
            local_y = (-world_x * sin_angle + world_y * cos_angle) / ry
            theta = math.atan2(local_y, local_x)
            radial = math.sqrt(local_x * local_x + local_y * local_y)
            boundary = (
                1.0
                + math.sin(theta * 3.0 + 0.45) * 0.070
                + math.sin(theta * 5.0 - 0.70) * 0.040
                + math.sin((x + 0.5) * 0.29 + (y + 0.5) * 0.13) * 0.015
            )
            signed_distance = (radial - boundary) * min(rx, ry)
            if signed_distance <= -1.2:
                terrain[y][x] = "DeepWater"
            elif signed_distance <= 1.6:
                terrain[y][x] = "Water"
            elif signed_distance <= 4.0:
                terrain[y][x] = "ShallowWater"
            elif signed_distance <= 6.2:
                terrain[y][x] = "MudBank"


def draw_road(terrain: list[list[str]], zones: list[list[str]]) -> None:
    # One continuous public road links the wilderness to Willowmere's future
    # city gate. It does not stamp a tavern, field, farmstead, or bridge.
    for x in range(0, 63):
        center_y = 27 + round(math.sin(x * 0.10 + 0.6) * 2.0)
        for y in range(center_y - 1, center_y + 2):
            if not (0 <= y < HEIGHT):
                continue
            if terrain[y][x] in WATER | SHORE:
                continue
            terrain[y][x] = "Road"
            zones[y][x] = "public_path"

    # North/south branch through the open region; this is a generated route,
    # not a pre-authored farm boundary.
    for y in range(0, HEIGHT):
        center_x = 52 + round(math.sin(y * 0.12 + 0.3) * 1.5)
        for x in range(center_x - 1, center_x + 2):
            if not (0 <= x < WIDTH):
                continue
            if terrain[y][x] in WATER | SHORE:
                continue
            terrain[y][x] = "Road"
            zones[y][x] = "public_path"


def add_natural_tall_grass(terrain: list[list[str]]) -> None:
    original = [row[:] for row in terrain]
    for y in range(2, HEIGHT - 2):
        for x in range(2, WIDTH - 2):
            if original[y][x] != "Grass":
                continue
            nearby = {original[ny][nx] for nx, ny in neighbors8(x, y)}
            if nearby & (WATER | SHORE | ROUTES):
                continue
            # Broad sparse patches, not single noisy substitutions.
            patch = math.sin(x * 0.19) + math.cos(y * 0.23) + math.sin((x + y) * 0.07)
            if patch > 2.15 and hash01(x // 2, y // 2, 43) > 0.58:
                terrain[y][x] = "TallGrass"



def forest_density(x: int, y: int) -> float:
    """Broad deterministic forest stands, not independent object noise."""
    broad = (
        math.sin(x * 0.105 + 0.7)
        + math.cos(y * 0.135 - 0.4)
        + math.sin((x + y) * 0.055 + 1.8)
    ) / 3.0
    detail = (hash01(x // 3, y // 3, 177) - 0.5) * 0.42
    # Keep the central Willowmere approach more open while allowing forest
    # stands to frame it from the north-west and south-west.
    approach_clearance = max(0.0, 1.0 - abs(x - 52) / 16.0) * 0.28
    return broad + detail - approach_clearance


TREE_VARIANTS = [
    "oak_tree",
    "oak_tree_variant_02",
    "oak_tree_variant_03",
    "oak_tree_variant_04",
    "oak_tree_variant_05",
    "oak_tree_variant_06",
    "oak_tree_variant_07",
    "oak_tree_variant_08",
]
BUSH_VARIANTS = [
    "berry_bush",
    "berry_bush_variant_02",
    "berry_bush_variant_03",
    "berry_bush_variant_04",
]
ROCK_VARIANTS = [
    "boulder",
    "boulder_variant_02",
    "boulder_variant_03",
    "boulder_variant_04",
]
MUSHROOM_VARIANTS = [
    "forage_mushroom",
    "forage_mushroom_variant_02",
    "forage_mushroom_variant_03",
    "forage_mushroom_variant_04",
]
HERB_VARIANTS = ["wild_herb", "wild_herb_variant_02", "wild_herb_variant_03"]
FLOWER_VARIANTS = [
    "wildflower_patch",
    "wildflower_patch_variant_02",
    "wildflower_patch_variant_03",
]
REED_VARIANTS = ["reed_patch", "reed_patch_variant_02"]


def natural_variant_id(variants: list[str], x: int, y: int, salt: int) -> str:
    index = int(hash01(x, y, salt) * len(variants)) % len(variants)
    return variants[index]


def tree_variant_id(x: int, y: int) -> str:
    return natural_variant_id(TREE_VARIANTS, x, y, 233)


def rect_cells(rect: list[int]):
    x, y, width, height = rect
    for cell_y in range(y, y + height):
        for cell_x in range(x, x + width):
            yield cell_x, cell_y


def add_natural_objects(
    terrain: list[list[str]], zones: list[list[str]], spawn: tuple[int, int]
) -> list[dict]:
    """Build the biome around natural-scale ElizaWy tree canopies.

    Trees are the primary ecology layer. Their trunk spacing, canopy footprint,
    road/shore buffers, player clearing, chopping interaction, and render layer
    are resolved before bushes, rocks, mushrooms, flowers, and herbs are placed.
    """
    objects: list[dict] = []
    tree_positions: list[tuple[int, int]] = []
    occupied_trunks: set[tuple[int, int]] = set()
    canopy_cells: set[tuple[int, int]] = set()
    allowed_ground = {"Grass", "TallGrass"}

    def clear_of_restricted_terrain(x: int, y: int, radius: int) -> bool:
        for check_y in range(max(0, y - radius), min(HEIGHT, y + radius + 1)):
            for check_x in range(max(0, x - radius), min(WIDTH, x + radius + 1)):
                if terrain[check_y][check_x] in WATER | SHORE | ROUTES:
                    return False
                if zones[check_y][check_x] != "none":
                    return False
        return True

    def tree_fits(x: int, y: int) -> bool:
        if terrain[y][x] not in allowed_ground or zones[y][x] != "none":
            return False
        if abs(x - spawn[0]) <= 7 and abs(y - spawn[1]) <= 7:
            return False
        if not clear_of_restricted_terrain(x, y, 2):
            return False
        if any((x - other_x) ** 2 + (y - other_y) ** 2 < 10 for other_x, other_y in tree_positions):
            return False
        visual_rect = [x - 1, y - 3, 3, 4]
        return all(
            0 <= cell_x < WIDTH
            and 0 <= cell_y < HEIGHT
            and terrain[cell_y][cell_x] in allowed_ground
            for cell_x, cell_y in rect_cells(visual_rect)
        )

    # Tree-first canopy pass. Sampling every second cell and enforcing trunk
    # distance yields authored groves instead of a uniform placeholder scatter.
    for y in range(4, HEIGHT - 3, 2):
        for x in range(4, WIDTH - 4, 2):
            density = forest_density(x, y)
            if density < 0.16 or hash01(x, y, 211) < 0.30:
                continue
            if not tree_fits(x, y):
                continue
            asset_id = tree_variant_id(x, y)
            object_id = f"natural_tree_{x:02d}_{y:02d}"
            visual_rect = [x - 1, y - 3, 3, 4]
            trunk_rect = [x, y, 1, 1]
            objects.append(
                {
                    "id": object_id,
                    "assetId": asset_id,
                    "visualRect": visual_rect,
                    "canopyRect": visual_rect,
                    "collisionRect": trunk_rect,
                    "trunkRect": trunk_rect,
                    "layer": "tall_object",
                    "fadeWhenPlayerBehind": True,
                    "blocksMovement": True,
                    "ecologyRole": "forest_canopy_primary",
                    "resourceProfile": "temperate_hardwood_tree",
                    "interactions": [
                        {"id": f"chop_{object_id}", "kind": "chop", "rect": trunk_rect}
                    ],
                }
            )
            tree_positions.append((x, y))
            occupied_trunks.add((x, y))
            canopy_cells.update(rect_cells(visual_rect))

    # Understory and forage pass. It is driven by distance to real trees, so
    # mushrooms, bushes, flowers, and herbs form a forest-floor ecology instead
    # of appearing as unrelated generic circles across the whole map.
    for y in range(2, HEIGHT - 2):
        for x in range(2, WIDTH - 2):
            if terrain[y][x] not in allowed_ground or zones[y][x] != "none":
                continue
            if (x, y) in occupied_trunks:
                continue
            if abs(x - spawn[0]) <= 5 and abs(y - spawn[1]) <= 5:
                continue
            nearby_tree_distance = min(
                ((x - tree_x) ** 2 + (y - tree_y) ** 2 for tree_x, tree_y in tree_positions),
                default=10_000,
            )
            near_forest = nearby_tree_distance <= 36
            near_water = any(
                terrain[ny][nx] in WATER | SHORE
                for ny in range(max(0, y - 2), min(HEIGHT, y + 3))
                for nx in range(max(0, x - 2), min(WIDTH, x + 3))
            )
            if terrain[y][x] in ROUTES or any(
                terrain[ny][nx] in ROUTES for nx, ny in neighbors8(x, y)
            ):
                continue

            roll = hash01(x, y, 307)
            asset_id = None
            label = None
            if near_water and roll > 0.962:
                asset_id = natural_variant_id(REED_VARIANTS, x, y, 401)
                label = "reed"
            elif near_forest and roll > 0.988:
                asset_id = natural_variant_id(BUSH_VARIANTS, x, y, 409)
                label = "bush"
            elif near_forest and roll > 0.973:
                asset_id = natural_variant_id(MUSHROOM_VARIANTS, x, y, 419)
                label = "mushroom"
            elif (near_forest or (x, y) in canopy_cells) and roll > 0.958:
                asset_id = natural_variant_id(FLOWER_VARIANTS, x, y, 421)
                label = "flower"
            elif (near_forest or (x, y) in canopy_cells) and roll > 0.946:
                asset_id = natural_variant_id(HERB_VARIANTS, x, y, 431)
                label = "herb"
            elif not near_forest and roll > 0.982:
                asset_id = natural_variant_id(ROCK_VARIANTS, x, y, 439)
                label = "rock"
            if asset_id is None:
                continue

            object_id = f"natural_{label}_{x:02d}_{y:02d}"
            if asset_id.startswith("berry_bush"):
                record = {
                    "id": object_id,
                    "assetId": asset_id,
                    "visualRect": [x, y - 1, 2, 2],
                    "collisionRect": [x, y, 1, 1],
                    "layer": "low_object",
                    "ecologyRole": "forest_understory",
                    "interactions": [
                        {"id": f"forage_{object_id}", "kind": "forage", "rect": [x, y, 1, 1]}
                    ],
                }
            elif asset_id.startswith("boulder"):
                record = {
                    "id": object_id,
                    "assetId": asset_id,
                    "visualRect": [x, y - 1, 2, 2],
                    "collisionRect": [x, y, 1, 1],
                    "layer": "low_object",
                    "ecologyRole": "natural_obstacle",
                    "interactions": [
                        {"id": f"mine_{object_id}", "kind": "mine", "rect": [x, y, 1, 1]}
                    ],
                }
            else:
                record = {
                    "id": object_id,
                    "assetId": asset_id,
                    "visualRect": [x, y, 1, 1],
                    "collisionRect": [x, y, 0, 0],
                    "blocksMovement": False,
                    "layer": "ground_object",
                    "ecologyRole": "forest_floor" if near_forest else "waterside_plant",
                    "interactions": [
                        {"id": f"forage_{object_id}", "kind": "forage", "rect": [x, y, 1, 1]}
                    ],
                }
            objects.append(record)

    if len(tree_positions) < 12:
        raise ValueError(f"tree-first worldgen produced too few ElizaWy trees: {len(tree_positions)}")
    return objects

def build_scene() -> dict:
    terrain = [["Grass" for _ in range(WIDTH)] for _ in range(HEIGHT)]
    zones = [["none" for _ in range(WIDTH)] for _ in range(HEIGHT)]
    coast = generate_coast(terrain)
    generate_lake(terrain)
    draw_road(terrain, zones)
    add_natural_tall_grass(terrain)

    spawn = [48, 31]
    for y in range(spawn[1] - 1, spawn[1] + 2):
        for x in range(spawn[0] - 1, spawn[0] + 2):
            terrain[y][x] = "Road"
            zones[y][x] = "public_path"

    objects = add_natural_objects(terrain, zones, tuple(spawn))

    return {
        "id": "havenwild_open_world_willowmere_outskirts_v0_1",
        "version": "0.1.0",
        "kind": "worldgen_scene",
        "sceneId": "willowmere_outskirts_open_world",
        "title": "Willowmere Outskirts — Continuous Open World Biome Slice",
        "sceneKind": "exterior",
        "biome": "temperate",
        "role": "continuous_open_world_surface_region",
        "sceneSize": [WIDTH, HEIGHT],
        "tileSize": 32,
        "edgePolicy": {
            "mustAvoidVoid": True,
            "streamingContract": "continuous_chunk_neighbors",
            "resolvedBorders": {
                "north": "temperate_wilderness",
                "south": "temperate_wilderness",
                "east": "ocean",
                "west": "willowmere_approach",
            },
        },
        "layers": {"terrain": terrain, "zones": zones},
        "objects": objects,
        "transitions": [],
        "spawns": [{"id": "player_default", "tile": spawn}],
        "editor": {
            "showLayers": ["terrain", "zones", "objects", "collision", "interactions"],
            "defaultTool": "inspect_select",
            "allowPaintTerrain": True,
            "allowMoveObjects": True,
            "generatedBy": "tools/automation/worldgen/Build-ClientWorldgenTestSceneV167Z.py",
            "generationSeed": SEED,
            "generationProfile": "open_world_v7_source_pure_certification_v167z67",
            "visualFamily": "lpc_terrain_v7_island_v1",
            "legacyFarmsteadFixture": False,
            "coastColumnRange": [min(coast), max(coast)],
        },
        "validationRules": [
            "scene_size_matches_layers",
            "no_void_scene_edges",
            "no_static_farmstead",
            "single_visual_family_per_biome",
            "transition_safe_intermediate_bands",
            "continuous_outdoor_surface",
        ],
    }


def validate(scene: dict) -> dict:
    terrain = scene["layers"]["terrain"]
    if len(terrain) != HEIGHT or any(len(row) != WIDTH for row in terrain):
        raise ValueError("open-world biome scene dimensions changed")

    counts = Counter(tile for row in terrain for tile in row)
    required = {
        "Grass",
        "Road",
        "Sand",
        "Sand",
        "OceanShallow",
        "OceanDeep",
        "Water",
        "MudBank",
        "ShallowWater",
        "DeepWater",
    }
    missing = required - set(counts)
    if missing:
        raise ValueError(f"open-world biome scene is missing roles: {sorted(missing)}")
    forbidden = FORBIDDEN_STATIC_TERRAIN & set(counts)
    if forbidden:
        raise ValueError(f"static/mixed-family terrain returned: {sorted(forbidden)}")
    if scene.get("transitions"):
        raise ValueError("open-world biome test scene must not bake outdoor scene portals")
    allowed_natural_assets = set(
        TREE_VARIANTS
        + BUSH_VARIANTS
        + ROCK_VARIANTS
        + MUSHROOM_VARIANTS
        + HERB_VARIANTS
        + FLOWER_VARIANTS
        + REED_VARIANTS
    )
    objects = scene.get("objects", [])
    unexpected_assets = {item.get("assetId") for item in objects} - allowed_natural_assets
    if unexpected_assets:
        raise ValueError(f"open-world biome contains non-natural static assets: {sorted(unexpected_assets)}")
    if not objects:
        raise ValueError("open-world biome must exercise reviewed LPC Terrain-folder nature assets")
    tree_objects = [item for item in objects if "tree" in str(item.get("assetId", ""))]
    if len(tree_objects) < 12:
        raise ValueError(f"open-world biome must contain a real ElizaWy forest layer: {len(tree_objects)} tree(s)")
    tree_variants = {item.get("assetId") for item in tree_objects}
    if len(tree_variants) < 4:
        raise ValueError(f"tree-first worldgen must exercise at least four authored tree variants: {sorted(tree_variants)}")
    for item in tree_objects:
        visual = item.get("visualRect")
        collision = item.get("collisionRect")
        if not isinstance(visual, list) or visual[2:] != [3, 4]:
            raise ValueError(f"tree visual footprint must remain 3x4 cells: {item.get('id')}")
        if not isinstance(collision, list) or collision[2:] != [1, 1]:
            raise ValueError(f"tree trunk collision must remain 1x1: {item.get('id')}")

    natural_asset_ids = {str(item.get("assetId", "")) for item in objects}
    required_ecology = {
        "bush": any(asset.startswith("berry_bush") for asset in natural_asset_ids),
        "rock": any(asset.startswith("boulder") for asset in natural_asset_ids),
        "mushroom": any(asset.startswith("forage_mushroom") for asset in natural_asset_ids),
        "flower": any(asset.startswith("wildflower_patch") for asset in natural_asset_ids),
        "waterside_reed": any(asset.startswith("reed_patch") for asset in natural_asset_ids),
    }
    missing_ecology = sorted(name for name, present in required_ecology.items() if not present)
    if missing_ecology:
        raise ValueError(f"tree-first ecology is missing authored ElizaWy groups: {missing_ecology}")

    violations: list[str] = []
    for y, row in enumerate(terrain):
        for x, tile in enumerate(row):
            cardinal = {terrain[ny][nx] for nx, ny in neighbors4(x, y)}
            if tile == "OceanDeep" and cardinal - {"OceanDeep", "Water"}:
                violations.append(f"ocean deep touches non-mid-water at {x},{y}")
            if tile == "DeepWater" and cardinal - {"DeepWater", "Water"}:
                violations.append(f"lake deep touches non-mid-water at {x},{y}")
            if tile == "Sand" and not ({"Sand", "OceanShallow"} <= cardinal | {tile}):
                # End/corner cells may meet one family diagonally, but every wet
                # sand cell must remain part of the coastal chain.
                if not ("Sand" in cardinal or "OceanShallow" in cardinal):
                    violations.append(f"wet sand detached from coast at {x},{y}")
            if tile == "ShallowWater" and "MudBank" in cardinal and "Water" in cardinal:
                # This contact is expected at the inner edge; it must never jump
                # directly to deep water.
                if "DeepWater" in cardinal:
                    violations.append(f"lake authored pair sequence collapsed at {x},{y}")
            if tile == "OceanShallow" and ({"Sand", "Sand"} & cardinal) and "OceanDeep" in cardinal:
                violations.append(f"ocean authored pair sequence collapsed at {x},{y}")
            if tile == "Water" and ({"MudBank", "Sand", "Sand"} & cardinal):
                violations.append(f"mid water touches land without authored shallows at {x},{y}")
    if violations:
        raise ValueError("transition-band topology violations: " + "; ".join(violations[:16]))

    start = tuple(scene["spawns"][0]["tile"])
    queue = deque([start])
    visited = {start}
    walkable = {"Grass", "TallGrass", "Road", "Sand", "Sand", "MudBank"}
    while queue:
        x, y = queue.popleft()
        for nx, ny in neighbors4(x, y):
            if (nx, ny) in visited or terrain[ny][nx] not in walkable:
                continue
            visited.add((nx, ny))
            queue.append((nx, ny))
    if len(visited) < 2400:
        raise ValueError(f"open-world walkable surface is too fragmented: {len(visited)} cells")

    return {
        "schema": "havenwild.open_world_biome_metrics.v167z38",
        "scene": SCENE.relative_to(ROOT).as_posix(),
        "generation_seed": SEED,
        "visual_family": "lpc_terrain_v7_island_v1",
        "terrain_counts": dict(sorted(counts.items())),
        "forbidden_static_terrain_count": 0,
        "natural_object_count": len(scene.get("objects", [])),
        "tree_count": len(tree_objects),
        "tree_variant_count": len(tree_variants),
        "tree_variants": sorted(tree_variants),
        "natural_object_assets": sorted({item.get("assetId") for item in scene.get("objects", [])}),
        "outdoor_transition_portal_count": 0,
        "transition_band_violations": 0,
        "reachable_walkable_cells": len(visited),
    }


def write_preview(scene: dict) -> None:
    terrain = scene["layers"]["terrain"]
    scale = 8
    image = Image.new("RGBA", (WIDTH, HEIGHT), PREVIEW_COLORS["Grass"])
    pixels = image.load()
    for y, row in enumerate(terrain):
        for x, tile in enumerate(row):
            pixels[x, y] = PREVIEW_COLORS.get(tile, (255, 0, 255, 255))
    image = image.resize((WIDTH * scale, HEIGHT * scale), Image.Resampling.NEAREST)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    image.save(PREVIEW, optimize=True)


def main() -> int:
    scene = build_scene()
    metrics = validate(scene)
    SCENE.parent.mkdir(parents=True, exist_ok=True)
    SCENE.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    write_preview(scene)
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {SCENE.relative_to(ROOT)} and {PREVIEW.relative_to(ROOT)} "
        f"as a coherent open-world biome slice: {metrics['terrain_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
