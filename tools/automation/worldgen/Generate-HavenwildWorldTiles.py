from __future__ import annotations

import json
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
TILE = 32

# Havenwild palette target: warm earth, readable terrain, vibrant items/decor later.
PALETTE = {
    "grass": ((72, 122, 70), (92, 148, 83), (53, 94, 55)),
    "tall_grass": ((78, 134, 73), (107, 168, 92), (48, 98, 54)),
    "meadow": ((82, 138, 79), (120, 174, 96), (54, 96, 57)),
    "flower": ((80, 134, 75), (110, 166, 88), (225, 206, 104)),
    "clover": ((67, 128, 70), (100, 169, 91), (190, 218, 112)),
    "autumn_grass": ((128, 122, 68), (166, 145, 74), (86, 96, 50)),
    "snow_grass": ((169, 183, 164), (220, 226, 210), (96, 124, 96)),
    "dirt": ((112, 75, 48), (144, 94, 56), (70, 45, 32)),
    "tilled": ((83, 54, 35), (112, 68, 39), (52, 34, 25)),
    "wet_soil": ((65, 46, 35), (90, 62, 43), (37, 29, 24)),
    "rich_soil": ((74, 49, 32), (111, 75, 45), (42, 31, 23)),
    "mud": ((87, 69, 50), (121, 92, 59), (52, 41, 32)),
    "road": ((128, 105, 72), (161, 130, 82), (85, 65, 45)),
    "stone": ((121, 117, 106), (159, 152, 136), (72, 72, 70)),
    "mountain_path": ((124, 115, 92), (158, 146, 113), (74, 72, 64)),
    "wood": ((129, 84, 48), (174, 112, 58), (76, 45, 27)),
    "dark_wood": ((108, 67, 42), (148, 93, 54), (63, 38, 25)),
    "brick": ((128, 78, 68), (164, 101, 82), (80, 49, 45)),
    "wall": ((83, 59, 40), (119, 84, 56), (44, 31, 24)),
    "cliff": ((112, 101, 81), (151, 139, 111), (62, 57, 51)),
    "rock": ((92, 96, 100), (138, 142, 146), (49, 53, 58)),
    "cave_floor": ((74, 70, 66), (103, 96, 87), (39, 38, 37)),
    "cave_wall": ((39, 42, 46), (73, 74, 76), (21, 22, 25)),
    "water": ((48, 111, 169), (88, 166, 211), (29, 68, 122)),
    "shallow_water": ((70, 147, 190), (123, 203, 224), (38, 96, 145)),
    "deep_water": ((28, 70, 124), (60, 115, 166), (15, 40, 84)),
    "river": ((47, 125, 179), (95, 181, 218), (24, 76, 135)),
    "foam": ((105, 170, 198), (198, 229, 232), (55, 119, 156)),
    "sand": ((207, 185, 127), (236, 218, 164), (154, 129, 86)),
    "wet_sand": ((169, 148, 106), (203, 184, 137), (112, 96, 74)),
    "pebble": ((145, 142, 134), (180, 176, 164), (91, 90, 88)),
    "crop": ((76, 149, 71), (122, 194, 82), (45, 88, 42)),
    "greenhouse": ((52, 108, 76), (120, 188, 135), (31, 70, 50)),
    "lava": ((123, 49, 34), (225, 111, 41), (70, 28, 25)),
    "void": ((16, 14, 15), (31, 26, 24), (5, 4, 5)),
}


def rng_for(name: str) -> random.Random:
    return random.Random(sum((i + 1) * ord(c) for i, c in enumerate(name)))


def shade(c, d):
    return tuple(max(0, min(255, int(v + d))) for v in c)


def base_tile(name: str, palette_key: str) -> Image.Image:
    a, b, c = PALETTE[palette_key]
    r = rng_for(name)
    img = Image.new("RGBA", (TILE, TILE), a + (255,))
    draw = ImageDraw.Draw(img)
    for y in range(TILE):
        for x in range(TILE):
            n = r.randint(-8, 8) + int(4 * math.sin((x + y) / 8.0))
            if r.random() < 0.08:
                col = shade(b, n - 5)
            elif r.random() < 0.08:
                col = shade(c, n + 4)
            else:
                col = shade(a, n)
            img.putpixel((x, y), col + (255,))
    # subtle edge readability, not a hard outline
    draw.rectangle((0, 0, TILE - 1, TILE - 1), outline=shade(c, -8) + (70,))
    return img


def grass(name, key="grass", flowers=False, blades=True):
    img = base_tile(name, key)
    draw = ImageDraw.Draw(img)
    r = rng_for(name + "grass")
    if blades:
        for _ in range(10):
            x = r.randrange(3, 29)
            y = r.randrange(11, 29)
            draw.line((x, y, x + r.choice([-1, 1, 2]), y - r.randrange(3, 8)), fill=(159, 207, 103, 95), width=1)
    if flowers:
        colors = [(225, 206, 104, 190), (232, 144, 130, 190), (214, 199, 235, 190)]
        for _ in range(5):
            x = r.randrange(5, 28)
            y = r.randrange(7, 28)
            draw.point((x, y), fill=r.choice(colors))
            draw.point((x+1, y), fill=r.choice(colors))
    return img


def soil(name, key="dirt", furrows=False, wet=False):
    img = base_tile(name, key)
    draw = ImageDraw.Draw(img)
    r = rng_for(name + "soil")
    for yy in [7, 14, 21, 28]:
        fill = (45, 31, 23, 115) if not wet else (25, 22, 21, 135)
        draw.line((3, yy + r.randrange(-1, 2), 29, yy + r.randrange(-1, 2)), fill=fill, width=1)
    if furrows:
        for xx in [8, 16, 24]:
            draw.line((xx, 3, xx - 2, 29), fill=(42, 28, 20, 110), width=1)
    return img


def water(name, key="water", foam=False, diagonal=False):
    img = base_tile(name, key)
    draw = ImageDraw.Draw(img)
    r = rng_for(name + "water")
    for yy in [8, 17, 25]:
        xoff = r.randrange(-2, 3)
        draw.arc((3 + xoff, yy - 5, 28 + xoff, yy + 4), 180, 360, fill=(182, 224, 236, 100), width=1)
    if foam:
        for yy in [10, 19]:
            draw.line((4, yy, 14, yy - 2, 24, yy + 1, 29, yy - 1), fill=(218, 238, 235, 135), width=1)
    if diagonal:
        draw.line((0, 26, 32, 8), fill=(202, 231, 237, 70), width=2)
    return img


def sand(name, key="sand", pebbles=False):
    img = base_tile(name, key)
    draw = ImageDraw.Draw(img)
    r = rng_for(name + "sand")
    for _ in range(10 if pebbles else 5):
        x, y = r.randrange(4, 29), r.randrange(4, 29)
        rad = 1 if not pebbles else r.choice([1, 1, 2])
        fill = (245, 229, 177, 80) if not pebbles else (92, 90, 86, 95)
        draw.ellipse((x, y, x + rad, y + rad), fill=fill)
    return img


def stone(name, key="stone", cracks=True):
    img = base_tile(name, key)
    draw = ImageDraw.Draw(img)
    r = rng_for(name + "stone")
    if cracks:
        for _ in range(3):
            x, y = r.randrange(4, 24), r.randrange(4, 24)
            draw.line((x, y, x + r.randrange(4, 10), y + r.randrange(2, 9)), fill=(35, 34, 32, 85), width=1)
    return img


def wood(name, key="wood"):
    img = base_tile(name, key)
    draw = ImageDraw.Draw(img)
    for xx in [6, 16, 26]:
        draw.line((xx, 0, xx, 31), fill=(69, 40, 24, 120), width=1)
        draw.line((xx + 1, 0, xx + 1, 31), fill=(199, 130, 69, 55), width=1)
    for yy in [10, 21]:
        draw.line((0, yy, 32, yy), fill=(73, 42, 25, 95), width=1)
    return img


def bridge(name):
    img = wood(name, "wood")
    draw = ImageDraw.Draw(img)
    draw.line((0, 7, 31, 7), fill=(62, 38, 24, 150), width=2)
    draw.line((0, 24, 31, 24), fill=(62, 38, 24, 150), width=2)
    return img


def crop(name):
    img = soil(name, "tilled", True)
    draw = ImageDraw.Draw(img)
    for x, y, s in [(9, 22, 4), (16, 18, 5), (23, 21, 4)]:
        draw.ellipse((x - s, y - s, x + s, y + s), fill=(65, 154, 68, 210))
        draw.ellipse((x - s + 2, y - s - 2, x + 1, y + 1), fill=(132, 203, 87, 160))
    return img


def greenhouse(name):
    img = grass(name, "greenhouse", False, False)
    draw = ImageDraw.Draw(img)
    for x in range(4, 30, 7):
        draw.line((x, 2, x - 5, 30), fill=(188, 241, 197, 80), width=1)
    draw.rectangle((2, 2, 29, 29), outline=(198, 245, 202, 90))
    return img


def wall(name, key="wall"):
    img = stone(name, key)
    draw = ImageDraw.Draw(img)
    for yy in [8, 16, 24]:
        draw.line((0, yy, 31, yy), fill=(24, 20, 18, 85), width=1)
    return img


def make_tile(tile_id: str, family: str) -> Image.Image:
    mapping = {
        "grass": lambda: grass(tile_id, "grass"),
        "grass_02": lambda: grass(tile_id, "grass"),
        "meadow_grass": lambda: grass(tile_id, "meadow", flowers=True),
        "flower_grass": lambda: grass(tile_id, "flower", flowers=True),
        "tall_grass": lambda: grass(tile_id, "tall_grass"),
        "clover_patch": lambda: grass(tile_id, "clover", flowers=True),
        "autumn_grass": lambda: grass(tile_id, "autumn_grass"),
        "snow_grass": lambda: grass(tile_id, "snow_grass", False),
        "dirt": lambda: soil(tile_id, "dirt"),
        "tilled_soil": lambda: soil(tile_id, "tilled", True),
        "tilled_soil_watered": lambda: soil(tile_id, "wet_soil", True, wet=True),
        "rich_soil": lambda: soil(tile_id, "rich_soil", True),
        "mud": lambda: soil(tile_id, "mud"),
        "composted_soil": lambda: soil(tile_id, "rich_soil", True),
        "sand": lambda: sand(tile_id, "sand"),
        "wet_sand": lambda: sand(tile_id, "wet_sand"),
        "pebble_shore": lambda: sand(tile_id, "pebble", True),
        "shallow_water": lambda: water(tile_id, "shallow_water"),
        "water": lambda: water(tile_id, "water"),
        "deep_water": lambda: water(tile_id, "deep_water"),
        "river_water": lambda: water(tile_id, "river", diagonal=True),
        "river_foam": lambda: water(tile_id, "foam", foam=True),
        "road": lambda: soil(tile_id, "road"),
        "dirt_road": lambda: soil(tile_id, "road"),
        "stone_path": lambda: stone(tile_id, "stone"),
        "cobble_path": lambda: stone(tile_id, "stone"),
        "mountain_path": lambda: stone(tile_id, "mountain_path"),
        "bridge": lambda: bridge(tile_id),
        "wood_floor": lambda: wood(tile_id, "wood"),
        "plank_floor": lambda: wood(tile_id, "dark_wood"),
        "stone_floor": lambda: stone(tile_id, "stone"),
        "brick_floor": lambda: stone(tile_id, "brick"),
        "cellar_floor": lambda: stone(tile_id, "cave_floor"),
        "wall": lambda: wall(tile_id, "wall"),
        "cliff": lambda: wall(tile_id, "cliff"),
        "cliff_top": lambda: stone(tile_id, "cliff"),
        "mountain_rock": lambda: wall(tile_id, "rock"),
        "cave_floor": lambda: stone(tile_id, "cave_floor"),
        "cave_wall": lambda: wall(tile_id, "cave_wall"),
        "cave_water": lambda: water(tile_id, "deep_water"),
        "ore_floor": lambda: stone(tile_id, "cave_floor"),
        "crop": lambda: crop(tile_id),
        "greenhouse_zone": lambda: greenhouse(tile_id),
        "herb_patch": lambda: grass(tile_id, "meadow", flowers=True),
        "reed_bank": lambda: grass(tile_id, "tall_grass"),
        "snow_path": lambda: stone(tile_id, "snow_grass"),
        "lava_crack": lambda: stone(tile_id, "lava"),
        "interior_void": lambda: base_tile(tile_id, "void"),
    }
    return mapping.get(tile_id, lambda: base_tile(tile_id, family))()


def tile_entry(tile_id, label, category, family, **kw):
    entry = {
        "id": tile_id,
        "label": label,
        "tile_size": [32, 32],
        "category": category,
        "family": family,
        "walkable": kw.get("walkable", True),
        "buildable": kw.get("buildable", True),
        "blocks_building": kw.get("blocks_building", False),
        "fertile": kw.get("fertile", False),
        "liquid": kw.get("liquid", False),
        "fishable": kw.get("fishable", False),
        "forageable": kw.get("forageable", False),
        "interior_only": kw.get("interior_only", False),
        "autotile_group": kw.get("autotile_group"),
        "height_band": kw.get("height_band"),
        "biomes": kw.get("biomes", []),
        "variants": kw.get("variants", 1),
        "notes": kw.get("notes", ""),
    }
    return entry


code_tiles = [
    tile_entry("grass", "Grass", "terrain", "grass", forageable=True, autotile_group="grass", height_band="land", biomes=["temperate", "farm", "woods"], variants=3),
    tile_entry("tall_grass", "Tall Grass", "terrain", "grass", forageable=True, autotile_group="grass", height_band="land", biomes=["temperate", "woods"], variants=3),
    tile_entry("sand", "Sand", "terrain", "shore", forageable=True, autotile_group="shore", height_band="beach", biomes=["coastal"], variants=3),
    tile_entry("wet_sand", "Wet Sand", "terrain", "shore", forageable=True, buildable=False, autotile_group="shore", height_band="waterline", biomes=["coastal"], variants=2),
    tile_entry("pebble_shore", "Pebble Shore", "terrain", "shore", forageable=True, autotile_group="shore", height_band="shore", biomes=["coastal", "highlands"], variants=3),
    tile_entry("road", "Dirt Road", "terrain", "road", autotile_group="road", height_band="land", biomes=["farm", "town", "woods"], variants=2),
    tile_entry("stone_path", "Stone Path", "terrain", "road", autotile_group="road", height_band="land", biomes=["town", "highlands"], variants=2),
    tile_entry("mountain_path", "Mountain Path", "terrain", "road", autotile_group="road", height_band="slope", biomes=["highlands", "mountain"], variants=2),
    tile_entry("wood_floor", "Wood Floor", "interior_floor", "wood", interior_only=True, autotile_group="wood_floor", height_band="interior", biomes=["tavern", "house"], variants=2),
    tile_entry("plank_floor", "Plank Floor", "interior_floor", "wood", interior_only=True, autotile_group="wood_floor", height_band="interior", biomes=["tavern", "dock"], variants=2),
    tile_entry("stone_floor", "Stone Floor", "interior_floor", "stone", interior_only=True, autotile_group="stone_floor", height_band="interior", biomes=["cellar", "cave", "town"], variants=2),
    tile_entry("brick_floor", "Brick Floor", "interior_floor", "stone", interior_only=True, autotile_group="stone_floor", height_band="interior", biomes=["kitchen", "town"], variants=2),
    tile_entry("wall", "Wall", "wall", "wall", walkable=False, buildable=False, blocks_building=True, interior_only=True, autotile_group="wall", height_band="blocked", biomes=["tavern", "house"], variants=2),
    tile_entry("cliff", "Cliff Face", "wall", "cliff", walkable=False, buildable=False, blocks_building=True, autotile_group="cliff", height_band="cliff", biomes=["highlands", "mountain"], variants=3),
    tile_entry("mountain_rock", "Mountain Rock", "wall", "rock", walkable=False, buildable=False, blocks_building=True, autotile_group="cliff", height_band="mountain", biomes=["highlands", "mountain"], variants=3),
    tile_entry("dirt", "Dirt", "terrain", "dirt", fertile=True, autotile_group="dirt", height_band="land", biomes=["farm", "woods", "temperate"], variants=3),
    tile_entry("bridge", "Bridge", "terrain", "wood", autotile_group="road", height_band="over_water", biomes=["coastal", "river", "town"], variants=2),
    tile_entry("cave_floor", "Cave Floor", "cave", "cave_floor", forageable=True, autotile_group="cave_floor", height_band="cave_floor", biomes=["cave"], variants=3),
    tile_entry("cave_wall", "Cave Wall", "cave", "cave_wall", walkable=False, buildable=False, blocks_building=True, autotile_group="cave_wall", height_band="cave_wall", biomes=["cave"], variants=3),
    tile_entry("tilled_soil", "Tilled Soil", "farm", "tilled", fertile=True, buildable=False, autotile_group="farm_soil", height_band="field", biomes=["farm"], variants=3),
    tile_entry("crop", "Crop", "farm", "crop", fertile=True, buildable=False, autotile_group="crop", height_band="field", biomes=["farm"], variants=4),
    tile_entry("greenhouse_zone", "Greenhouse Zone", "farm", "greenhouse", fertile=True, buildable=False, autotile_group="greenhouse", height_band="field", biomes=["farm", "greenhouse"], variants=1),
    tile_entry("water", "Water", "water", "water", walkable=False, buildable=False, liquid=True, fishable=True, autotile_group="water", height_band="water", biomes=["river", "coastal", "lake"], variants=3),
    tile_entry("shallow_water", "Shallow Water", "water", "shallow_water", walkable=False, buildable=False, liquid=True, fishable=True, autotile_group="water", height_band="shallow_water", biomes=["river", "coastal", "lake"], variants=3),
    tile_entry("deep_water", "Deep Water", "water", "deep_water", walkable=False, buildable=False, liquid=True, fishable=True, autotile_group="water", height_band="deep_water", biomes=["river", "coastal", "lake", "sea"], variants=3),
]

expanded_ids = [
    ("grass", "Grass", "terrain", "grass"), ("grass_02", "Grass Variant", "terrain", "grass"),
    ("meadow_grass", "Meadow Grass", "terrain", "meadow"), ("flower_grass", "Flower Grass", "terrain", "flower"),
    ("tall_grass", "Tall Grass", "terrain", "tall_grass"), ("clover_patch", "Clover Patch", "terrain", "clover"),
    ("autumn_grass", "Autumn Grass", "terrain", "autumn_grass"), ("snow_grass", "Snow Grass", "terrain", "snow_grass"),
    ("dirt", "Dirt", "terrain", "dirt"), ("tilled_soil", "Tilled Soil", "farm", "tilled"),
    ("tilled_soil_watered", "Watered Soil", "farm", "wet_soil"), ("rich_soil", "Rich Soil", "farm", "rich_soil"),
    ("mud", "Mud", "terrain", "mud"), ("composted_soil", "Composted Soil", "farm", "rich_soil"),
    ("herb_patch", "Herb Patch", "terrain", "meadow"), ("reed_bank", "Reed Bank", "terrain", "tall_grass"),
    ("sand", "Sand", "terrain", "sand"), ("wet_sand", "Wet Sand", "terrain", "wet_sand"),
    ("pebble_shore", "Pebble Shore", "terrain", "pebble"), ("shallow_water", "Shallow Water", "water", "shallow_water"),
    ("water", "Water", "water", "water"), ("deep_water", "Deep Water", "water", "deep_water"),
    ("river_water", "River Water", "water", "river"), ("river_foam", "River Foam", "water", "foam"),
    ("road", "Dirt Road", "terrain", "road"), ("dirt_road", "Worn Road", "terrain", "road"),
    ("stone_path", "Stone Path", "terrain", "stone"), ("cobble_path", "Cobble Path", "terrain", "stone"),
    ("mountain_path", "Mountain Path", "terrain", "mountain_path"), ("bridge", "Bridge", "terrain", "wood"),
    ("snow_path", "Snow Path", "terrain", "snow_grass"), ("cliff_top", "Cliff Top", "terrain", "cliff"),
    ("wood_floor", "Wood Floor", "interior_floor", "wood"), ("plank_floor", "Plank Floor", "interior_floor", "dark_wood"),
    ("stone_floor", "Stone Floor", "interior_floor", "stone"), ("brick_floor", "Brick Floor", "interior_floor", "brick"),
    ("cellar_floor", "Cellar Floor", "interior_floor", "cave_floor"), ("wall", "Wall", "wall", "wall"),
    ("cliff", "Cliff Face", "wall", "cliff"), ("mountain_rock", "Mountain Rock", "wall", "rock"),
    ("cave_floor", "Cave Floor", "cave", "cave_floor"), ("cave_wall", "Cave Wall", "cave", "cave_wall"),
    ("cave_water", "Cave Water", "water", "deep_water"), ("ore_floor", "Ore Floor", "cave", "cave_floor"),
    ("lava_crack", "Lava Crack", "cave", "lava"), ("interior_void", "Interior Void", "special", "void"),
    ("crop", "Crop", "farm", "crop"), ("greenhouse_zone", "Greenhouse Zone", "farm", "greenhouse"),
]

# Pad to a 8x6/48-tile expanded atlas already exactly 48.
expanded_tiles = []
for tid, label, cat, fam in expanded_ids:
    liquid = cat == "water"
    wall_cat = cat == "wall"
    farm = cat == "farm"
    expanded_tiles.append(tile_entry(
        tid, label, cat, fam,
        walkable=not wall_cat and not liquid,
        buildable=not wall_cat and not liquid and cat not in {"farm", "water"},
        blocks_building=wall_cat or liquid,
        fertile=(farm or tid in {"dirt", "rich_soil", "composted_soil"}),
        liquid=liquid,
        fishable=liquid and tid != "lava_crack",
        forageable=cat == "terrain" and tid not in {"road", "dirt_road", "stone_path", "cobble_path", "mountain_path", "bridge", "snow_path", "cliff_top"},
        interior_only=cat in {"interior_floor"} or tid in {"wall", "interior_void"},
        autotile_group=("water" if liquid else "wall" if wall_cat else "farm_soil" if farm else "road" if "path" in tid or "road" in tid or tid == "bridge" else tid.split("_")[0]),
        height_band=("deep_water" if tid == "deep_water" else "shallow_water" if tid == "shallow_water" else "water" if liquid else "cliff" if wall_cat else "land"),
        biomes=["temperate", "coastal", "highlands", "cave", "farm"],
        variants=3,
    ))


def write_sheet(tiles, columns, filename, manifest_id, notes):
    rows = math.ceil(len(tiles) / columns)
    img = Image.new("RGBA", (columns * TILE, rows * TILE), (0, 0, 0, 0))
    for idx, entry in enumerate(tiles):
        tile_img = make_tile(entry["id"], entry["family"])
        x = (idx % columns) * TILE
        y = (idx // columns) * TILE
        img.alpha_composite(tile_img, (x, y))
    png_path = OUT / f"{filename}.png"
    img.save(png_path)
    for idx, entry in enumerate(tiles):
        entry["atlas"] = {
            "sheet": f"assets/generated/{filename}.png",
            "index": idx,
            "x": (idx % columns) * TILE,
            "y": (idx // columns) * TILE,
            "w": TILE,
            "h": TILE,
        }
    manifest = {
        "id": manifest_id,
        "kind": "tilesheet",
        "tile_size": 32,
        "columns": columns,
        "rows": rows,
        "tile_count": len(tiles),
        "output": f"assets/generated/{filename}.png",
        "license": "project-generated-placeholder-original",
        "style": "warm-earth cozy pixel terrain placeholders",
        "notes": notes,
        "tiles": tiles,
    }
    json_path = OUT / f"{filename}.json"
    json_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return png_path, json_path


write_sheet(code_tiles, 5, "prototype_terrain_tiles", "prototype_terrain_tiles", "Drop-in replacement for the current clean source TileKind::ALL ordering. 25 tiles, 5 columns, 5 rows.")
write_sheet(expanded_tiles, 8, "havenwild_world_tiles_expanded_v1", "havenwild_world_tiles_expanded_v1", "Forward-looking worldgen tilesheet for Havenwild biomes, seasons, farming, shorelines, rivers, caves, and scene interiors.")
print("Generated Havenwild world tile replacements.")
