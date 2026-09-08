#!/usr/bin/env python3
"""Generate deterministic Havenwild terrain certification scenes.

The fixtures are diagnostic-only and are shared by the native editor, client
terrain loader, topology validator, and visual evidence tools. Pass 167Z5 adds
full shoreline depth bands, ponds/bridges, mixed-material junctions, and a
complete semantic terrain gallery while preserving production registration as
off.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

WIDTH = 40
HEIGHT = 28
TILE_SIZE = [32, 32]
PRODUCTION_PACK = "content/worldgen/packs/worldgen_open_world_v0_1.json"
TEST_PACK = "content/worldgen/packs/worldgen_open_world_test_v0_12.json"
CONTACT_SHEET = "docs/audits/generated/havenwild_terrain_topology_contact_sheet_v167z5a.png"

MAPPED_TERRAIN = [
    "Grass", "TallGrass", "Sand", "WetSand", "PebbleShore", "Road",
    "StonePath", "MountainPath", "Bridge", "Cliff", "MountainRock", "Dirt",
    "CaveFloor", "TilledSoil", "WateredSoil", "Water", "ShallowWater",
    "DeepWater", "OceanDeep", "OceanShallow", "RiverWater",
    "RiverMouthBlend", "ShoreFoam", "MudBank",
]

NON_MAPPED_PRESENTATION_SEMANTICS = [
    "WoodFloor", "PlankFloor", "StoneFloor", "BrickFloor", "Wall",
    "CaveWall", "Crop", "GreenhouseZone",
]


def blank(fill: str = "Grass") -> list[list[str]]:
    return [[fill for _ in range(WIDTH)] for _ in range(HEIGHT)]


def coastline() -> list[list[str]]:
    grid = blank("Grass")
    for y in range(HEIGHT):
        shore = 18 + round(3.5 * math.sin(y / 3.0))
        for x in range(WIDTH):
            distance = shore - x
            if distance >= 8:
                grid[y][x] = "DeepWater"
            elif distance >= 4:
                grid[y][x] = "Water"
            elif distance >= 2:
                grid[y][x] = "ShallowWater"
            elif distance == 1:
                grid[y][x] = "WetSand"
            elif distance == 0:
                grid[y][x] = "Sand"
    return grid


def river() -> list[list[str]]:
    grid = blank("Grass")
    for y in range(HEIGHT):
        center = 19 + round(6 * math.sin(y / 4.2))
        width = 2 if y < 9 else 3 if y < 19 else 4
        for x in range(max(0, center - width - 2), min(WIDTH, center + width + 3)):
            distance = abs(x - center)
            if distance <= width:
                grid[y][x] = "RiverWater"
            elif distance == width + 1:
                grid[y][x] = "MudBank"
    return grid


def pond_bridge() -> list[list[str]]:
    grid = blank("Grass")
    cx, cy = 20, 14
    for y in range(HEIGHT):
        for x in range(WIDTH):
            distance = ((x - cx) / 10.0) ** 2 + ((y - cy) / 7.0) ** 2
            if distance <= 0.48:
                grid[y][x] = "Water"
            elif distance <= 0.78:
                grid[y][x] = "ShallowWater"
            elif distance <= 1.02:
                grid[y][x] = "MudBank"
    for x in range(7, 34):
        grid[13][x] = "Bridge" if grid[13][x] in {"Water", "ShallowWater", "MudBank"} else "Road"
        grid[14][x] = "Bridge" if grid[14][x] in {"Water", "ShallowWater", "MudBank"} else "Road"
    return grid


def farm_soil() -> list[list[str]]:
    grid = blank("Grass")
    for y in range(4, 24):
        for x in range(5, 35):
            if x in (5, 34) or y in (4, 23):
                grid[y][x] = "Dirt"
            elif 8 <= x <= 31 and 7 <= y <= 20:
                grid[y][x] = "WateredSoil" if (x + y) % 4 == 0 else "TilledSoil"
    return grid


def mountain() -> list[list[str]]:
    grid = blank("Grass")
    plateau: set[tuple[int, int]] = set()
    for y in range(2, HEIGHT - 2):
        ridge = 13 + y // 5 + round(math.sin(y / 3.0))
        for x in range(ridge, WIDTH - 2):
            plateau.add((x, y))
            grid[y][x] = "MountainRock"
    for x, y in plateau:
        if any((nx, ny) not in plateau for nx, ny in ((x - 1, y), (x + 1, y), (x, y + 1))):
            grid[y][x] = "Cliff"
    for y in range(HEIGHT):
        path = 17 + y // 5 + ((y // 4) % 2)
        for x in (path, path + 1):
            if 0 <= x < WIDTH:
                grid[y][x] = "MountainPath"
    return grid


def junctions() -> list[list[str]]:
    grid = blank("Grass")
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if x >= WIDTH // 2 and y < HEIGHT // 2:
                grid[y][x] = "Dirt"
            elif x < WIDTH // 2 and y >= HEIGHT // 2:
                grid[y][x] = "Sand"
            elif x >= WIDTH // 2 and y >= HEIGHT // 2:
                grid[y][x] = "MountainRock"
    for x in range(WIDTH):
        grid[HEIGHT // 2 - 1][x] = "Road"
        grid[HEIGHT // 2][x] = "Road"
    for y in range(HEIGHT):
        grid[y][WIDTH // 2 - 1] = "StonePath"
        grid[y][WIDTH // 2] = "StonePath"
    return grid


def snow_ice() -> list[list[str]]:
    grid = blank("Dirt")
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if y < 6:
                grid[y][x] = "DeepWater"
            elif y < 10:
                grid[y][x] = "Water"
            elif y < 13:
                grid[y][x] = "ShallowWater"
            elif y < 15:
                grid[y][x] = "PebbleShore"
            elif y < 20:
                grid[y][x] = "MountainRock"
            else:
                grid[y][x] = "Grass"
    return grid


def wrapped_world_seam() -> list[list[str]]:
    grid = blank("Grass")
    for y in range(HEIGHT):
        band = 6 + (y // 4) % 4
        for x in range(WIDTH):
            distance = min(x, WIDTH - 1 - x)
            if distance < band - 4:
                grid[y][x] = "Water"
            elif distance < band - 2:
                grid[y][x] = "ShallowWater"
            elif distance < band - 1:
                grid[y][x] = "WetSand"
            elif distance < band + 1:
                grid[y][x] = "Sand"
    return grid


def terrain_gallery() -> list[list[str]]:
    grid = blank("Grass")
    columns = 8
    cell_w = WIDTH // columns
    cell_h = 6
    # ShoreFoam remains visible only in this compatibility gallery. It is not
    # allowed as generated semantic world terrain.
    for index, tile in enumerate(MAPPED_TERRAIN):
        gx = index % columns
        gy = index // columns
        min_x = gx * cell_w
        min_y = gy * cell_h
        for y in range(min_y, min(HEIGHT, min_y + cell_h)):
            for x in range(min_x, min(WIDTH, min_x + cell_w)):
                grid[y][x] = tile
    return grid


PREVIEW_COLORS = {
    "Grass": (48, 132, 55, 255), "TallGrass": (58, 147, 59, 255),
    "Sand": (211, 188, 126, 255), "WetSand": (159, 139, 99, 255),
    "PebbleShore": (142, 140, 128, 255), "Road": (193, 151, 86, 255),
    "StonePath": (145, 137, 125, 255), "MountainPath": (176, 132, 78, 255),
    "WoodFloor": (126, 83, 47, 255), "PlankFloor": (150, 99, 56, 255),
    "StoneFloor": (115, 115, 111, 255), "BrickFloor": (139, 75, 62, 255),
    "Wall": (75, 65, 62, 255), "Cliff": (105, 82, 65, 255),
    "MountainRock": (109, 104, 96, 255), "Dirt": (116, 78, 48, 255),
    "Bridge": (146, 97, 54, 255), "CaveFloor": (73, 68, 65, 255),
    "CaveWall": (48, 44, 43, 255), "TilledSoil": (94, 55, 34, 255),
    "WateredSoil": (73, 46, 33, 255), "Crop": (90, 146, 54, 255),
    "GreenhouseZone": (105, 176, 94, 255), "Water": (40, 126, 170, 255),
    "ShallowWater": (63, 157, 183, 255), "DeepWater": (29, 83, 135, 255),
    "OceanDeep": (24, 65, 112, 255), "OceanShallow": (70, 165, 190, 255),
    "RiverWater": (47, 137, 176, 255), "RiverMouthBlend": (57, 148, 178, 255),
    "ShoreFoam": (220, 240, 235, 255), "MudBank": (92, 67, 43, 255),
}


def render_contact_sheet(generated: list[tuple[str, list[list[str]]]], path: Path) -> None:
    scale = 3
    label_h = 18
    card_w = WIDTH * scale
    card_h = HEIGHT * scale + label_h
    columns = 3
    rows = (len(generated) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * card_w, rows * card_h), (24, 27, 31, 255))
    draw = ImageDraw.Draw(sheet)
    for index, (scene_id, terrain) in enumerate(generated):
        tile_image = Image.new("RGBA", (WIDTH, HEIGHT), PREVIEW_COLORS["Grass"])
        pixels = tile_image.load()
        for y, row in enumerate(terrain):
            for x, tile in enumerate(row):
                pixels[x, y] = PREVIEW_COLORS.get(tile, (255, 0, 255, 255))
        tile_image = tile_image.resize((card_w, HEIGHT * scale), Image.Resampling.NEAREST)
        gx, gy = index % columns, index // columns
        ox, oy = gx * card_w, gy * card_h
        sheet.alpha_composite(tile_image, (ox, oy + label_h))
        draw.text((ox + 4, oy + 3), scene_id.replace("_", " ").title(), fill=(236, 232, 215, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)


SCENARIOS: dict[str, tuple[Callable[[], list[list[str]]], list[str], list[str]]] = {
    "coastline": (
        coastline,
        ["continuous authored shoreline curves", "deep/water/shallow/shore bands remain ordered"],
        ["DeepWater never touches land", "Sand and WetSand remain walkable"],
    ),
    "river": (
        river,
        ["connected narrow/wide turns", "mud bank remains subordinate to the channel"],
        ["RiverWater uses shallow traversal", "MudBank remains tillable ground"],
    ),
    "pond_bridge": (
        pond_bridge,
        ["organic pond rings", "bridge replaces route cells only across water/bank"],
        ["pond has no direct deep-water edge", "route remains connected"],
    ),
    "farm_soil": (
        farm_soil,
        ["clean Grass/Dirt/Soil boundary", "watered and dry cultivated cells remain readable"],
        ["TilledSoil and WateredSoil remain buildable", "farming classes remain distinct"],
    ),
    "mountain": (
        mountain,
        ["connected cliff face and walkable plateau", "mountain path cuts through without broken corners"],
        ["Cliff remains blocking", "MountainRock and MountainPath remain walkable"],
    ),
    "junctions": (
        junctions,
        ["three/four-material junctions retain one visual owner", "road and stone path stay continuous"],
        ["junction visuals do not alter semantic collision"],
    ),
    "snow_ice": (
        snow_ice,
        ["continuous cold-biome bands", "water/shore/stone/grass boundaries resolve"],
        ["DeepWater, Water, and ShallowWater remain distinct"],
    ),
    "wrapped_world_seam": (
        wrapped_world_seam,
        ["left/right tuple parity", "no horizontal seam discontinuity"],
        ["edge collision uses wrapped semantic neighbors"],
    ),
    "terrain_gallery": (
        terrain_gallery,
        ["all mapped terrain semantics have a deterministic atlas-backed display cell", "non-terrain presentation roles remain outside mapped terrain certification"],
        ["gallery is diagnostic-only and certifies mapped terrain only"],
    ),
}


def scene_payload(scene_id: str, terrain: list[list[str]], visual: list[str], gameplay: list[str]) -> dict:
    return {
        "id": f"terrain_acceptance_{scene_id}_v1",
        "version": "1.1.0",
        "kind": "worldgen_scene",
        "sceneId": f"terrain_acceptance_{scene_id}",
        "title": f"Terrain Acceptance — {scene_id.replace('_', ' ').title()}",
        "sceneKind": "exterior",
        "biome": "acceptance_fixture",
        "role": "diagnostic_only",
        "sceneSize": [WIDTH, HEIGHT],
        "tileSize": TILE_SIZE,
        "edgePolicy": {
            "mustAvoidVoid": True,
            "wrapX": scene_id == "wrapped_world_seam",
            "wrapY": False,
            "resolvedBorders": {"north": "fixture", "south": "fixture", "east": "fixture", "west": "fixture"},
        },
        "layers": {"terrain": terrain},
        "objects": [],
        "transitions": [],
        "spawns": [{"id": "player_start", "kind": "player", "tile": [WIDTH // 2, HEIGHT // 2]}],
        "acceptance": {
            "visualAssertions": visual,
            "gameplayAssertions": gameplay,
            "productionRegistered": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    out = args.root / "content/worldgen/scenes/terrain_acceptance"
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    generated: list[tuple[str, list[list[str]]]] = []
    for scene_id, (builder, visual, gameplay) in SCENARIOS.items():
        terrain = builder()
        generated.append((scene_id, terrain))
        payload = scene_payload(scene_id, terrain, visual, gameplay)
        path = out / f"{scene_id}_scene_v1.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        entries.append({
            "id": scene_id,
            "sceneId": payload["sceneId"],
            "path": path.relative_to(args.root).as_posix(),
            "size": payload["sceneSize"],
            "wrapX": payload["edgePolicy"]["wrapX"],
            "visualAssertions": visual,
            "gameplayAssertions": gameplay,
        })
    manifest = {
        "schema": "havenwild.terrain_acceptance_scene_manifest.v1",
        "version": 2,
        "diagnosticOnly": True,
        "productionRegistration": False,
        "compatibilityOnlyTerrain": ["ShoreFoam"],
        "mappedTerrainSemantics": MAPPED_TERRAIN,
        "excludedPresentationSemantics": NON_MAPPED_PRESENTATION_SEMANTICS,
        "semanticTopologyOnly": True,
        "scenes": entries,
    }
    (out / "terrain_acceptance_scene_manifest_v1.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    production_path = args.root / PRODUCTION_PACK
    production = json.loads(production_path.read_text(encoding="utf-8"))
    test_pack = dict(production)
    test_pack["id"] = "worldgen_open_world_test_v0_12"
    test_pack["name"] = "Havenwild Open World Biome and Terrain Test Pack"
    test_pack["version"] = "0.12.0-test"
    test_pack["previousPack"] = PRODUCTION_PACK
    acceptance_paths = [entry["path"] for entry in entries]
    test_pack["sceneFiles"] = list(production.get("sceneFiles", [])) + acceptance_paths
    test_pack["smokeTests"] = list(production.get("smokeTests", [])) + acceptance_paths
    test_pack["testWorld"] = {
        "enabledByDefaultDuringTerrainDevelopment": True,
        "defaultScene": "willowmere_outskirts_open_world",
        "terrainAcceptanceManifest": "content/worldgen/scenes/terrain_acceptance/terrain_acceptance_scene_manifest_v1.json",
        "developerNavigation": "F3 then PageUp/PageDown",
        "productionReleasePack": PRODUCTION_PACK,
        "staticFarmsteadFixture": False,
    }
    test_path = args.root / TEST_PACK
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(json.dumps(test_pack, indent=2) + "\n", encoding="utf-8")
    render_contact_sheet(generated, args.root / CONTACT_SHEET)

    print(
        f"Generated {len(entries)} terrain acceptance scenes in {out} and "
        f"client test pack {test_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
