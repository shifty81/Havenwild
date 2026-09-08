from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
WG = ROOT / "assets/generated/worldgen_v0_1"
TILE = 32
PAD = 2
CELL = TILE + PAD
OBJECT_CELL_W = 32
OBJECT_CELL_H = 64

# Original Havenwild palette. Uploaded examples are coverage/style references only;
# no source pixels, tracing, or palette sampling are used here.
PAL = {
    "grass": ((68, 112, 60), (87, 139, 70), (116, 164, 82), (42, 73, 44)),
    "tall_grass": ((58, 104, 52), (76, 131, 64), (110, 160, 77), (35, 68, 40)),
    "sand": ((202, 179, 121), (226, 204, 149), (241, 223, 174), (142, 116, 76)),
    "wet_sand": ((153, 132, 94), (178, 154, 110), (202, 180, 132), (101, 84, 63)),
    "pebble": ((126, 124, 116), (153, 149, 138), (181, 176, 160), (78, 79, 78)),
    "dirt": ((108, 73, 47), (136, 91, 55), (162, 108, 62), (66, 43, 30)),
    "road": ((130, 99, 64), (159, 126, 79), (184, 150, 95), (82, 59, 41)),
    "stone": ((108, 108, 103), (137, 135, 126), (166, 162, 147), (66, 68, 68)),
    "mountain": ((84, 87, 90), (110, 111, 110), (139, 139, 133), (46, 50, 54)),
    "water": ((42, 101, 154), (58, 127, 178), (95, 168, 201), (23, 61, 108)),
    "shallow": ((67, 141, 175), (92, 175, 198), (138, 205, 216), (37, 94, 136)),
    "deep": ((24, 63, 110), (35, 83, 135), (62, 116, 160), (12, 36, 74)),
    "wood": ((118, 75, 42), (149, 95, 52), (181, 118, 65), (68, 40, 25)),
    "brick": ((118, 70, 60), (148, 88, 73), (178, 110, 89), (70, 42, 40)),
    "cave": ((61, 59, 58), (82, 78, 74), (107, 100, 90), (33, 33, 34)),
    "cave_wall": ((32, 35, 39), (50, 53, 57), (75, 76, 75), (17, 19, 22)),
    "soil": ((77, 48, 30), (101, 63, 37), (127, 80, 45), (42, 28, 21)),
    "wet_soil": ((56, 42, 32), (76, 56, 41), (98, 71, 49), (30, 24, 21)),
    "mud": ((83, 66, 49), (107, 85, 60), (133, 106, 72), (51, 41, 32)),
}


def rng(name: str, variant: int = 0) -> random.Random:
    value = sum((i + 17) * ord(ch) for i, ch in enumerate(name)) + variant * 7919
    return random.Random(value)


def clamp(v: int) -> int:
    return max(0, min(255, int(v)))


def shade(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return tuple(clamp(channel + delta) for channel in color)


def rect(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, color) -> None:
    draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)


def base_tile(key: str, variant: int) -> Image.Image:
    base, mid, hi, low = PAL[key]
    image = Image.new("RGBA", (TILE, TILE), base + (255,))
    draw = ImageDraw.Draw(image)
    r = rng(key, variant)
    # Quiet centers and clustered edge/detail pixels reduce visual noise in large fields.
    for _ in range(28):
        x = r.randrange(1, 31)
        y = r.randrange(1, 31)
        if 8 < x < 24 and 8 < y < 24 and r.random() < 0.68:
            continue
        color = r.choice((mid, hi, low)) + (r.choice((40, 55, 72, 88)),)
        rect(draw, x, y, r.choice((1, 1, 2, 3)), r.choice((1, 1, 2)), color)
    return image


def grass(tile_id: str, variant: int, tall: bool = False) -> Image.Image:
    key = "tall_grass" if tall else "grass"
    image = base_tile(key, variant)
    draw = ImageDraw.Draw(image)
    r = rng(tile_id, variant)
    count = 12 if tall else 7
    for _ in range(count):
        x = r.randrange(3, 29)
        y = r.randrange(10, 29)
        height = r.randrange(4, 9 if tall else 6)
        color = PAL[key][2] + (175,)
        draw.line((x, y, x + r.choice((-1, 0, 1)), y - height), fill=color)
        if r.random() < 0.45:
            draw.point((x + 1, y - max(2, height // 2)), fill=PAL[key][1] + (155,))
    if tile_id == "greenhouse_zone":
        draw.rectangle((3, 3, 28, 28), outline=(178, 229, 191, 95))
        for x in (8, 16, 24):
            draw.line((x, 3, x - 4, 28), fill=(200, 242, 207, 55))
    return image


def soil(tile_id: str, variant: int, key: str = "dirt", furrow: bool = False) -> Image.Image:
    image = base_tile(key, variant)
    draw = ImageDraw.Draw(image)
    r = rng(tile_id, variant)
    if furrow:
        offset = variant % 2
        for y in (5, 11, 17, 23, 29):
            draw.line((1, y + offset, 30, y + offset), fill=PAL[key][3] + (175,))
            draw.line((2, y - 1 + offset, 29, y - 1 + offset), fill=PAL[key][1] + (95,))
    else:
        for _ in range(5):
            x, y = r.randrange(2, 29), r.randrange(2, 29)
            draw.point((x, y), fill=PAL[key][2] + (115,))
    return image


def sand(tile_id: str, variant: int, wet: bool = False, pebble: bool = False) -> Image.Image:
    key = "pebble" if pebble else ("wet_sand" if wet else "sand")
    image = base_tile(key, variant)
    draw = ImageDraw.Draw(image)
    r = rng(tile_id, variant)
    for _ in range(12 if pebble else 6):
        x, y = r.randrange(3, 29), r.randrange(3, 29)
        if pebble:
            color = r.choice((PAL[key][2], PAL[key][3])) + (185,)
            rect(draw, x, y, r.choice((1, 2, 3)), r.choice((1, 2)), color)
        else:
            draw.point((x, y), fill=PAL[key][2] + (130,))
    return image


def stone(tile_id: str, variant: int, key: str = "stone", brick: bool = False) -> Image.Image:
    image = base_tile(key, variant)
    draw = ImageDraw.Draw(image)
    r = rng(tile_id, variant)
    row_height = 8 if brick else 10
    for y in range(0, TILE, row_height):
        draw.line((0, y, 31, y), fill=PAL[key][3] + (145 if brick else 100,))
        offset = 0 if ((y // row_height + variant) % 2 == 0) else (7 if brick else 8)
        spacing = 14 if brick else 16
        for x in range(offset, TILE, spacing):
            draw.line((x, y, x, min(31, y + row_height - 1)), fill=PAL[key][3] + (125 if brick else 90,))
    for _ in range(5):
        x, y = r.randrange(2, 29), r.randrange(2, 29)
        draw.point((x, y), fill=PAL[key][2] + (90,))
    return image


def wood(tile_id: str, variant: int, dark: bool = False, bridge: bool = False) -> Image.Image:
    image = Image.new("RGBA", (TILE, TILE), ((96, 59, 38) if dark else PAL["wood"][0]) + (255,))
    draw = ImageDraw.Draw(image)
    r = rng(tile_id, variant)
    spacing = 8
    for x in range((variant % 2) * 4, TILE, spacing):
        draw.line((x, 0, x, 31), fill=(63, 39, 27, 160))
        if x + 1 < 32:
            draw.line((x + 1, 0, x + 1, 31), fill=(187, 122, 66, 85))
    for _ in range(6):
        x, y = r.randrange(2, 29), r.randrange(2, 29)
        draw.line((x, y, min(31, x + 3), y), fill=(74, 45, 28, 105))
    if bridge:
        draw.rectangle((0, 5, 31, 8), fill=(67, 42, 27, 210))
        draw.rectangle((0, 23, 31, 26), fill=(67, 42, 27, 210))
    return image


def water(tile_id: str, variant: int, key: str = "water", foam: bool = False) -> Image.Image:
    image = base_tile(key, variant)
    draw = ImageDraw.Draw(image)
    for lane, y in enumerate((6, 14, 22, 29)):
        offset = (variant * 3 + lane * 5) % 13 - 5
        color = PAL[key][2] + (105 if lane % 2 else 125,)
        for x in range(-10 + offset, 38, 14):
            draw.line((x, y, x + 5, y), fill=color)
            draw.point((x + 6, y - 1), fill=color)
    if foam:
        for x in range(-4 + (variant * 2) % 7, 35, 8):
            rect(draw, x, 6 + (x % 3), 5, 1, (222, 239, 232, 175))
    return image


def cliff(tile_id: str, variant: int, cave: bool = False, wall_face: bool = False) -> Image.Image:
    key = "cave_wall" if cave else "mountain"
    image = stone(tile_id, variant, key, False)
    draw = ImageDraw.Draw(image)
    if wall_face:
        draw.rectangle((0, 0, 31, 7), fill=PAL[key][1] + (255,))
        draw.line((0, 8, 31, 8), fill=PAL[key][3] + (220,))
        for x in (5 + variant, 15, 25 - variant):
            draw.line((x, 10, max(0, x - 3), 29), fill=PAL[key][3] + (120,))
    return image


def crop(tile_id: str, variant: int) -> Image.Image:
    image = soil(tile_id, variant, "soil", True)
    draw = ImageDraw.Draw(image)
    stage = min(3, variant)
    if stage == 0:
        for x in (7, 16, 25):
            rect(draw, x - 1, 18, 2, 3, (95, 155, 67, 235))
    else:
        height = 5 + stage * 2
        for x in (7, 16, 25):
            draw.line((x, 25, x, 25 - height), fill=(55, 103, 46, 255))
            rect(draw, x - 3, 24 - height, 3, 2, (107, 168, 72, 255))
            rect(draw, x + 1, 22 - height, 3, 2, (126, 182, 77, 255))
    return image


def make_tile(tile_id: str, variant: int) -> Image.Image:
    mapping: dict[str, Callable[[], Image.Image]] = {
        "grass": lambda: grass(tile_id, variant),
        "tall_grass": lambda: grass(tile_id, variant, True),
        "sand": lambda: sand(tile_id, variant),
        "wet_sand": lambda: sand(tile_id, variant, True),
        "pebble_shore": lambda: sand(tile_id, variant, pebble=True),
        "road": lambda: soil(tile_id, variant, "road"),
        "stone_path": lambda: stone(tile_id, variant),
        "mountain_path": lambda: stone(tile_id, variant, "mountain"),
        "water": lambda: water(tile_id, variant),
        "shallow_water": lambda: water(tile_id, variant, "shallow"),
        "deep_water": lambda: water(tile_id, variant, "deep"),
        "dirt": lambda: soil(tile_id, variant),
        "cliff": lambda: cliff(tile_id, variant, wall_face=True),
        "mountain_rock": lambda: cliff(tile_id, variant),
        "bridge": lambda: wood(tile_id, variant, bridge=True),
        "wood_floor": lambda: wood(tile_id, variant),
        "plank_floor": lambda: wood(tile_id, variant, dark=True),
        "stone_floor": lambda: stone(tile_id, variant),
        "brick_floor": lambda: stone(tile_id, variant, "brick", True),
        "wall": lambda: stone(tile_id, variant, "brick", True),
        "cave_floor": lambda: stone(tile_id, variant, "cave"),
        "cave_wall": lambda: cliff(tile_id, variant, cave=True, wall_face=True),
        "tilled_soil": lambda: soil(tile_id, variant, "soil", True),
        "watered_soil": lambda: soil(tile_id, variant, "wet_soil", True),
        "crop_seedling": lambda: crop(tile_id, variant),
        "greenhouse_zone": lambda: grass(tile_id, variant),
        "ocean_deep": lambda: water(tile_id, variant, "deep"),
        "ocean_shallow": lambda: water(tile_id, variant, "shallow"),
        "river_water": lambda: water(tile_id, variant, "water"),
        "river_mouth_blend": lambda: water(tile_id, variant, "shallow", True),
        "shore_foam": lambda: water(tile_id, variant, "shallow", True),
        "mud_bank": lambda: soil(tile_id, variant, "mud"),
    }
    if tile_id not in mapping:
        return grass(tile_id, variant)
    return mapping[tile_id]()


def paste_extruded(atlas: Image.Image, image: Image.Image, x: int, y: int) -> None:
    atlas.alpha_composite(image, (x, y))
    atlas.paste(image.crop((0, 0, TILE, 1)), (x, y - 1))
    atlas.paste(image.crop((0, TILE - 1, TILE, TILE)), (x, y + TILE))
    atlas.paste(image.crop((0, 0, 1, TILE)), (x - 1, y))
    atlas.paste(image.crop((TILE - 1, 0, TILE, TILE)), (x + TILE, y))


def build_tile_variants() -> None:
    path = WG / "terrain/common_base_terrain_32.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    records = manifest["tiles"]
    columns = int(manifest["columns"])
    base_count = len(records)
    total = base_count * 4
    rows = math.ceil(total / columns)
    atlas = Image.new("RGBA", (columns * CELL + 2, rows * CELL + 2), (0, 0, 0, 0))

    # Keep all original base rectangles stable. Additional variants are appended.
    for index, record in enumerate(records):
        base_rect = record["rect"]
        paste_extruded(atlas, make_tile(record["id"], 0), base_rect[0], base_rect[1])
        variant_rects = [base_rect]
        for variant in range(1, 4):
            atlas_index = base_count + index * 3 + (variant - 1)
            col = atlas_index % columns
            row = atlas_index // columns
            x = PAD + col * CELL
            y = PAD + row * CELL
            paste_extruded(atlas, make_tile(record["id"], variant), x, y)
            variant_rects.append([x, y, TILE, TILE])
        record["variantRects"] = variant_rects
        record["variantCount"] = len(variant_rects)

    atlas.save(WG / "terrain/common_base_terrain_32.png")
    manifest["version"] = "0.3.0"
    manifest["rows"] = rows
    manifest["tile_count"] = base_count
    manifest["visual_variant_count"] = total
    manifest["source"] = "tools/automation/worldgen/Generate-HavenwildProductionEnvironmentPass60.py"
    manifest["license"] = "Havenwild project-owned original"
    manifest["notes"] = [
        "Production terrain atlas with four deterministic visual variants per semantic TileKind",
        "Original base rectangles preserved for compatibility and palette thumbnails",
        "Runtime and native editor select the same variant from local scene coordinates",
        "No third-party or uploaded reference pixels are included",
    ]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


# ----- 32x64 production object atlas -----

def canvas_object() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (OBJECT_CELL_W, OBJECT_CELL_H), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def draw_tree_object(kind: str = "oak", fruit: bool = False) -> Image.Image:
    image, draw = canvas_object()
    trunk = (103, 65, 36, 255)
    draw.rectangle((13, 35, 18, 58), fill=trunk)
    draw.rectangle((14, 35, 15, 57), fill=(145, 87, 43, 190))
    leaf_base = (48, 111, 57, 255) if kind != "pine" else (35, 88, 58, 255)
    if kind == "pine":
        for y, width in ((8, 18), (17, 22), (27, 26), (36, 28)):
            draw.polygon(((16, y - 7), (16 - width // 2, y + 8), (16 + width // 2, y + 8)), fill=leaf_base)
            draw.line((16 - width // 2 + 2, y + 7, 16 + width // 2 - 2, y + 7), fill=(24, 62, 43, 180))
    else:
        blobs = [(7, 14, 18, 29), (14, 8, 27, 26), (2, 22, 17, 38), (12, 20, 30, 40), (7, 5, 20, 20)]
        for i, box in enumerate(blobs):
            color = shade(leaf_base[:3], (i % 3 - 1) * 12) + (255,)
            draw.ellipse(box, fill=color)
        draw.arc((4, 7, 27, 36), 205, 335, fill=(103, 164, 82, 170), width=1)
    if fruit:
        for x, y in ((9, 19), (20, 16), (14, 29), (24, 27)):
            draw.rectangle((x, y, x + 2, y + 2), fill=(184, 58, 46, 255))
    return image


def draw_simple_object(name: str) -> Image.Image:
    render_aliases = {
        "shipping_box": "barrel",
        "band_stage_prop": "bench",
        "lute_stand": "tree_stump",
        "dance_lantern": "fallen_log",
    }
    name = render_aliases.get(name, name)
    image, draw = canvas_object()
    wood = (132, 79, 42, 255)
    wood_hi = (179, 111, 58, 255)
    wood_lo = (72, 43, 27, 255)
    stone = (104, 105, 103, 255)
    metal = (71, 77, 82, 255)
    if name == "berry_bush":
        for box, color in [((4, 34, 18, 51), (44, 108, 54, 255)), ((13, 29, 29, 51), (56, 127, 61, 255)), ((7, 26, 23, 45), (67, 142, 66, 255))]:
            draw.ellipse(box, fill=color)
        for x, y in ((9, 37), (16, 32), (22, 41), (13, 45)):
            draw.rectangle((x, y, x + 2, y + 2), fill=(159, 57, 94, 255))
    elif name == "boulder":
        draw.polygon(((5, 53), (8, 38), (15, 31), (25, 36), (29, 52), (23, 58), (10, 58)), fill=stone)
        draw.polygon(((9, 40), (15, 33), (22, 38), (17, 43)), fill=(143, 144, 139, 210))
        draw.line((7, 53, 24, 57), fill=(60, 62, 63, 210), width=2)
    elif name == "ore_node":
        image = draw_simple_object("boulder")
        draw = ImageDraw.Draw(image)
        for x, y, c in ((12, 43, (81, 185, 191, 255)), (21, 48, (197, 142, 72, 255)), (17, 36, (177, 213, 215, 255))):
            draw.rectangle((x, y, x + 3, y + 3), fill=c)
    elif name == "forage_mushroom":
        draw.rectangle((14, 43, 18, 57), fill=(220, 198, 160, 255))
        draw.pieslice((7, 31, 25, 49), 180, 360, fill=(177, 70, 60, 255))
        for x, y in ((12, 37), (19, 35), (16, 41)):
            draw.rectangle((x, y, x + 1, y + 1), fill=(246, 224, 190, 255))
    elif name == "wild_herb":
        for x, top in ((10, 37), (15, 31), (20, 36), (24, 34)):
            draw.line((16, 58, x, top), fill=(58, 123, 60, 255), width=2)
            draw.ellipse((x - 3, top, x + 2, top + 4), fill=(85, 156, 73, 255))
    elif name == "table_round":
        draw.ellipse((4, 28, 28, 43), fill=wood_hi)
        draw.ellipse((4, 28, 28, 43), outline=wood_lo, width=2)
        draw.rectangle((14, 40, 18, 58), fill=wood)
        draw.rectangle((9, 56, 23, 59), fill=wood_lo)
    elif name == "chair_wood":
        draw.rectangle((9, 27, 22, 45), fill=wood)
        draw.rectangle((8, 25, 23, 31), fill=wood_hi)
        draw.rectangle((9, 45, 12, 59), fill=wood_lo)
        draw.rectangle((20, 45, 23, 59), fill=wood_lo)
        draw.line((9, 27, 9, 18), fill=wood_lo, width=3)
        draw.line((22, 27, 22, 18), fill=wood_lo, width=3)
    elif name == "bar_counter":
        draw.rectangle((2, 29, 29, 54), fill=wood)
        draw.rectangle((1, 26, 30, 33), fill=wood_hi)
        draw.rectangle((5, 37, 26, 50), outline=wood_lo, width=2)
        draw.rectangle((8, 53, 11, 60), fill=wood_lo)
        draw.rectangle((21, 53, 24, 60), fill=wood_lo)
    elif name in {"keg", "barrel"}:
        draw.ellipse((8, 24, 24, 31), fill=wood_hi)
        draw.rectangle((8, 27, 24, 54), fill=wood)
        draw.ellipse((8, 49, 24, 58), fill=wood_lo)
        for y in (32, 47):
            draw.line((8, y, 24, y), fill=metal, width=2)
        draw.line((12, 29, 12, 52), fill=(158, 96, 49, 150))
        draw.line((20, 29, 20, 52), fill=(158, 96, 49, 150))
    elif name == "sink":
        draw.rectangle((5, 31, 27, 53), fill=(119, 129, 128, 255))
        draw.rectangle((8, 34, 24, 45), fill=(57, 91, 103, 255))
        draw.line((16, 31, 16, 20), fill=metal, width=2)
        draw.arc((13, 18, 23, 28), 180, 350, fill=metal, width=2)
    elif name == "stove":
        draw.rectangle((5, 27, 27, 57), fill=(56, 59, 62, 255))
        draw.rectangle((9, 33, 23, 47), fill=(28, 30, 32, 255))
        draw.ellipse((11, 35, 21, 45), fill=(155, 59, 32, 255))
        draw.line((20, 27, 20, 17), fill=metal, width=3)
    elif name == "prep_table":
        draw.rectangle((3, 30, 29, 38), fill=wood_hi)
        draw.rectangle((6, 38, 9, 59), fill=wood_lo)
        draw.rectangle((23, 38, 26, 59), fill=wood_lo)
        draw.rectangle((10, 42, 22, 46), fill=wood)
    elif name == "dish_rack":
        draw.rectangle((4, 27, 28, 57), outline=wood_lo, width=2)
        for x in (9, 14, 19, 24):
            draw.arc((x - 3, 35, x + 3, 46), 180, 360, fill=(194, 214, 214, 255), width=1)
    elif name == "bed_basic":
        draw.rectangle((3, 28, 29, 58), fill=(102, 121, 153, 255))
        draw.rectangle((3, 28, 29, 36), fill=wood)
        draw.rectangle((6, 38, 26, 55), fill=(158, 177, 194, 255))
        draw.rectangle((6, 38, 14, 45), fill=(226, 222, 197, 255))
        draw.rectangle((3, 56, 29, 60), fill=wood_lo)
    elif name == "fireplace":
        draw.rectangle((5, 22, 27, 59), fill=(101, 92, 80, 255))
        for y in (25, 33, 41, 49):
            draw.line((5, y, 27, y), fill=(61, 56, 52, 255))
        draw.arc((9, 33, 23, 55), 180, 360, fill=(31, 29, 29, 255), width=3)
        draw.rectangle((10, 43, 22, 57), fill=(31, 29, 29, 255))
        draw.polygon(((16, 50), (11, 57), (21, 57)), fill=(222, 99, 39, 255))
    elif name == "door":
        draw.rectangle((7, 16, 25, 60), fill=wood)
        draw.rectangle((7, 16, 25, 60), outline=wood_lo, width=2)
        draw.arc((7, 9, 25, 25), 180, 360, fill=wood_lo, width=2)
        draw.ellipse((21, 39, 23, 41), fill=(230, 190, 91, 255))
    elif name == "stairs_up":
        for i in range(6):
            y = 54 - i * 5
            draw.rectangle((5 + i * 2, y, 27, y + 3), fill=shade(wood[:3], i * 4) + (255,))
    elif name == "crate_stack":
        for box in ((3, 36, 18, 55), (15, 30, 29, 53)):
            draw.rectangle(box, fill=wood)
            draw.rectangle(box, outline=wood_lo, width=2)
            x0, y0, x1, y1 = box
            draw.line((x0, y0, x1, y1), fill=wood_lo, width=1)
            draw.line((x1, y0, x0, y1), fill=wood_lo, width=1)
    elif name == "barrel":
        # Pass 60 uses this slot as a distinct barrel object.
        return draw_simple_object("barrel")
    elif name == "well_pump":
        draw.ellipse((5, 39, 27, 58), fill=(89, 91, 89, 255))
        draw.rectangle((5, 42, 27, 54), fill=(102, 103, 99, 255))
        draw.ellipse((8, 39, 24, 49), fill=(31, 48, 54, 255))
        draw.line((24, 40, 24, 22), fill=metal, width=2)
        draw.line((24, 22, 16, 22), fill=metal, width=2)
        draw.line((16, 22, 16, 31), fill=metal, width=2)
    elif name == "scarecrow":
        draw.line((16, 22, 16, 60), fill=wood_lo, width=3)
        draw.line((5, 33, 27, 33), fill=wood_lo, width=3)
        draw.ellipse((11, 17, 21, 28), fill=(211, 167, 91, 255))
        draw.polygon(((8, 19), (16, 12), (24, 19)), fill=(111, 72, 39, 255))
        draw.polygon(((6, 34), (26, 34), (22, 50), (10, 50)), fill=(123, 75, 71, 255))
    elif name == "fence_post":
        draw.rectangle((13, 24, 19, 60), fill=wood)
        draw.rectangle((11, 22, 21, 29), fill=wood_hi)
        draw.line((2, 39, 30, 39), fill=wood, width=4)
        draw.line((2, 50, 30, 50), fill=wood_lo, width=4)
    elif name == "lamp_post":
        draw.line((16, 27, 16, 60), fill=(51, 46, 42, 255), width=3)
        draw.rectangle((10, 14, 22, 30), fill=(61, 53, 45, 255))
        draw.rectangle((12, 16, 20, 27), fill=(230, 181, 82, 230))
        draw.polygon(((9, 14), (16, 8), (23, 14)), fill=(47, 42, 39, 255))
    elif name == "construction_tape":
        draw.rectangle((4, 52, 28, 58), fill=(77, 58, 42, 255))
        draw.line((6, 29, 6, 57), fill=wood_lo, width=3)
        draw.line((26, 29, 26, 57), fill=wood_lo, width=3)
        for x in range(7, 26, 6):
            draw.line((x, 35, min(25, x + 5), 42), fill=(231, 190, 54, 255), width=3)
            draw.line((x + 5, 35, min(25, x + 10), 42), fill=(40, 36, 33, 255), width=3)
    elif name == "scaffold":
        draw.line((6, 18, 6, 60), fill=wood_lo, width=3)
        draw.line((26, 18, 26, 60), fill=wood_lo, width=3)
        for y in (25, 42, 58):
            draw.line((5, y, 27, y), fill=wood, width=3)
        draw.line((6, 22, 26, 57), fill=wood_hi, width=2)
    elif name == "bench":
        # Pass 60 uses this slot as a compact bench.
        draw.rectangle((3, 35, 29, 43), fill=wood_hi)
        draw.rectangle((5, 44, 27, 50), fill=wood)
        draw.rectangle((7, 49, 10, 59), fill=wood_lo)
        draw.rectangle((22, 49, 25, 59), fill=wood_lo)
        draw.line((6, 35, 6, 25), fill=wood_lo, width=3)
        draw.line((26, 35, 26, 25), fill=wood_lo, width=3)
    elif name == "tree_stump":
        # Pass 60 uses this slot as a stump.
        draw.ellipse((7, 39, 25, 58), fill=wood)
        draw.ellipse((8, 36, 24, 47), fill=wood_hi)
        draw.ellipse((11, 38, 21, 45), outline=wood_lo, width=1)
        draw.line((16, 39, 16, 45), fill=wood_lo)
    elif name == "fallen_log":
        # Pass 60 uses this slot as a fallen log.
        draw.rounded_rectangle((2, 40, 29, 55), radius=5, fill=wood)
        draw.ellipse((2, 40, 12, 55), fill=wood_hi)
        draw.ellipse((4, 42, 10, 53), outline=wood_lo, width=1)
        draw.line((13, 47, 26, 47), fill=wood_lo)
    elif name == "signboard":
        draw.line((16, 35, 16, 60), fill=wood_lo, width=3)
        draw.rectangle((4, 21, 28, 40), fill=wood)
        draw.rectangle((4, 21, 28, 40), outline=wood_lo, width=2)
        draw.line((8, 28, 24, 28), fill=wood_hi)
        draw.line((8, 33, 20, 33), fill=wood_hi)
    else:
        draw.rectangle((7, 31, 25, 58), fill=(215, 67, 196, 255))
    return image


def build_object_atlas() -> None:
    manifest_path = ROOT / "assets/generated/havenwild_2p5d_objects_32x64_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    columns = int(manifest["columns"])
    rows = int(manifest["rows"])
    atlas = Image.new("RGBA", (columns * OBJECT_CELL_W, rows * OBJECT_CELL_H), (0, 0, 0, 0))
    semantic_slot_names = {
        "shipping_box": "barrel",
        "band_stage_prop": "bench",
        "lute_stand": "tree_stump",
        "dance_lantern": "fallen_log",
    }
    for record in manifest["objects"]:
        name = record["name"]
        if name == "oak_tree":
            sprite = draw_tree_object("oak")
        elif name == "apple_tree":
            sprite = draw_tree_object("oak", fruit=True)
        elif name == "pine_tree":
            sprite = draw_tree_object("pine")
        else:
            sprite = draw_simple_object(name)
        atlas.alpha_composite(sprite, (record["x"], record["y"]))
        if name in semantic_slot_names:
            record["legacy_name"] = name
            record["name"] = semantic_slot_names[name]
    atlas.save(ROOT / "assets/generated/havenwild_2p5d_objects_32x64_v1.png")
    manifest["version"] = "0.2.0"
    manifest["license"] = "Havenwild project-owned original"
    manifest["source"] = "tools/automation/worldgen/Generate-HavenwildProductionEnvironmentPass60.py"
    manifest["style"] = "cozy fixed-orthographic 32x64 pixel objects"
    manifest["slot_reassignments"] = {
        "shipping_box": "barrel",
        "band_stage_prop": "bench",
        "lute_stand": "tree_stump",
        "dance_lantern": "fallen_log",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


# ----- expanded project-owned reference/authoring atlases -----

def pack_fixed_object_library(path_stem: Path, names: list[str], category: str) -> None:
    columns = 8
    rows = math.ceil(len(names) / columns)
    atlas = Image.new("RGBA", (columns * OBJECT_CELL_W, rows * OBJECT_CELL_H), (0, 0, 0, 0))
    records = []
    occurrences: dict[str, int] = {}
    for index, name in enumerate(names):
        occurrences[name] = occurrences.get(name, 0) + 1
        occurrence = occurrences[name]
        stable_name = name if occurrence == 1 else f"{name}_{occurrence}"
        col, row = index % columns, index // columns
        if name == "oak_tree":
            sprite = draw_tree_object("oak")
        elif name == "apple_tree":
            sprite = draw_tree_object("oak", fruit=True)
        elif name == "pine_tree":
            sprite = draw_tree_object("pine")
        else:
            sprite = draw_simple_object(name)
        x, y = col * OBJECT_CELL_W, row * OBJECT_CELL_H
        atlas.alpha_composite(sprite, (x, y))
        records.append({
            "id": f"havenwild_{category}_{stable_name}",
            "label": name.replace("_", " ").title()
            if occurrence == 1
            else f"{name.replace('_', ' ').title()} {occurrence}",
            "kind": "authoring_stamp",
            "category": category,
            "rect": [x, y, OBJECT_CELL_W, OBJECT_CELL_H],
            "visualFootprint": [1, 2],
            "collisionFootprint": [1, 1],
            "origin": [0, 1],
            "status": "project_owned_generic_stamp_runtime_ready",
        })
    path_stem.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(path_stem.with_suffix(".png"))
    data = {
        "id": path_stem.name,
        "kind": "authoring_stamp_atlas",
        "version": "0.2.0",
        "cell_size": [OBJECT_CELL_W, OBJECT_CELL_H],
        "columns": columns,
        "rows": rows,
        "license": "Havenwild project-owned original",
        "source": "tools/automation/worldgen/Generate-HavenwildProductionEnvironmentPass60.py",
        "runtimeStatus": "generic_stamp_runtime_ready",
        "objects": records,
    }
    path_stem.with_suffix(".json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_authoring_libraries() -> None:
    interior = [
        "table_round", "chair_wood", "bar_counter", "keg", "sink", "stove", "prep_table", "dish_rack",
        "bed_basic", "fireplace", "door", "stairs_up", "crate_stack", "barrel", "lamp_post", "signboard",
        "well_pump", "bench", "tree_stump", "fallen_log", "scarecrow", "fence_post", "wild_herb", "forage_mushroom",
    ]
    town = [
        "crate_stack", "barrel", "well_pump", "scarecrow", "fence_post", "lamp_post", "scaffold", "bench",
        "signboard", "door", "stairs_up", "bar_counter", "keg", "prep_table", "chair_wood", "table_round",
        "boulder", "berry_bush", "oak_tree", "apple_tree", "pine_tree", "wild_herb", "forage_mushroom", "construction_tape",
    ]
    cave = [
        "boulder", "ore_node", "forage_mushroom", "wild_herb", "crate_stack", "barrel", "lamp_post", "signboard",
        "stairs_up", "door", "scaffold", "construction_tape", "tree_stump", "fallen_log", "well_pump", "fireplace",
        "boulder", "ore_node", "boulder", "ore_node", "forage_mushroom", "wild_herb", "crate_stack", "lamp_post",
    ]
    pack_fixed_object_library(WG / "interiors/cozy_interior_stamps_32", interior, "interior")
    pack_fixed_object_library(WG / "town/capital_city_stamps_32", town, "town")
    pack_fixed_object_library(WG / "caves/cave_stamps_32", cave, "cave")


def build_preview() -> None:
    common = Image.open(WG / "terrain/common_base_terrain_32.png").convert("RGBA")
    objects = Image.open(ROOT / "assets/generated/havenwild_2p5d_objects_32x64_v1.png").convert("RGBA")
    preview = Image.new("RGBA", (960, 1060), (24, 27, 31, 255))
    draw = ImageDraw.Draw(preview)
    draw.text((16, 12), "Havenwild Production Environment Library — Pass 60", fill=(232, 236, 228, 255))
    draw.text(
        (16, 34),
        "32 live semantic tiles × 4 deterministic variants; 26 live placeable object kinds",
        fill=(164, 177, 167, 255),
    )

    manifest = json.loads((WG / "terrain/common_base_terrain_32.json").read_text(encoding="utf-8"))
    tile_columns = ((16, 62), (324, 62))
    for index, record in enumerate(manifest["tiles"]):
        column = index // 16
        row = index % 16
        x0, y0 = tile_columns[column]
        y = y0 + row * 34
        draw.text((x0, y + 10), record["id"][:17], fill=(214, 219, 210, 255))
        for variant, source in enumerate(record["variantRects"]):
            tile = common.crop((source[0], source[1], source[0] + 32, source[1] + 32))
            preview.alpha_composite(tile, (138 + column * 308 + variant * 36, y))

    draw.text((640, 62), "Live runtime/editor object atlas", fill=(214, 219, 210, 255))
    scaled = objects.resize((288, 288), Image.Resampling.NEAREST)
    preview.alpha_composite(scaled, (640, 84))
    draw.text((640, 382), "Trees, forage, rocks, tavern props,", fill=(164, 177, 167, 255))
    draw.text((640, 400), "storage, farm, lights, fences, and signs", fill=(164, 177, 167, 255))

    draw.text((16, 632), "Project-owned authoring stamp libraries", fill=(214, 219, 210, 255))
    stamp_specs = [
        ("Interior", WG / "interiors/cozy_interior_stamps_32.png"),
        ("Capital / town", WG / "town/capital_city_stamps_32.png"),
        ("Cave", WG / "caves/cave_stamps_32.png"),
    ]
    for index, (label, path) in enumerate(stamp_specs):
        x = 16 + index * 310
        draw.text((x, 658), label, fill=(191, 159, 99, 255))
        atlas = Image.open(path).convert("RGBA").resize((288, 216), Image.Resampling.NEAREST)
        preview.alpha_composite(atlas, (x, 680))

    draw.text(
        (16, 930),
        "Uploaded sheets are coverage references only; production pixels above are original Havenwild assets.",
        fill=(191, 159, 99, 255),
    )
    draw.text(
        (16, 952),
        "Stamp libraries remain authoring-ready until generic multi-tile stamp placement is bound.",
        fill=(164, 177, 167, 255),
    )
    draw.text(
        (16, 974),
        "Animal sheets remain deferred for a separate original animation rebuild.",
        fill=(164, 177, 167, 255),
    )
    out = ROOT / "docs/assets/previews"
    out.mkdir(parents=True, exist_ok=True)
    preview.save(out / "havenwild_production_environment_library_pass60.png")


def update_manifests() -> None:
    root_path = WG / "worldgen_asset_manifest_v0_1.json"
    root = json.loads(root_path.read_text(encoding="utf-8"))
    for atlas in (
        "interiors/cozy_interior_stamps_32.json",
        "town/capital_city_stamps_32.json",
        "caves/cave_stamps_32.json",
    ):
        if atlas not in root["atlases"]:
            root["atlases"].append(atlas)
    root["version"] = "0.3.0"
    root["pipelineStatus"]["commonBaseTerrain"] = "production_pass_60_four_variants"
    root["pipelineStatus"]["runtimeObjectAtlas"] = "production_pass_60_expanded_palette"
    root["pipelineStatus"]["environmentStampLibraries"] = "production_pass_60_authoring_ready"
    root["referencePolicy"] = "Uploaded mixed-provenance sheets are coverage references only; no pixels are packaged or promoted."
    root_path.write_text(json.dumps(root, indent=2) + "\n", encoding="utf-8")

    coverage_path = ROOT / "content/assets/reference_previews/uploaded_environment_reference_coverage_pass60.json"
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage = {
        "schema": "havenwild.uploaded_environment_reference_coverage.v0_1",
        "updated": "2026-07-11",
        "policy": "metadata_only_reference_coverage_no_raw_image_packaging_no_pixel_copy_no_palette_lift",
        "usage": "References were used for category coverage and sheet organization only. No raw uploaded pixels, tracing, palette lifting, or direct runtime promotion.",
        "familiesObserved": [
            "cozy_interior_furniture_and_walls",
            "castle_and_capital_city_modular_architecture",
            "cave_floor_wall_ledge_and_entrance_kits",
            "farm_ground_water_cliff_and_path_tiles",
            "trees_foliage_fences_wells_crates_and_roofs",
            "four_direction_farm_animal_animation_sheets",
            "base_character_animation_reference",
        ],
        "productionResponse": {
            "liveNow": [
                "four_visual_variants_for_each_existing_semantic_runtime_tile",
                "expanded_runtime_placeable_object_kinds_and_production_32x64_atlas",
            ],
            "authoringReady": [
                "cozy_interior_stamp_atlas",
                "capital_city_stamp_atlas",
                "cave_stamp_atlas",
            ],
            "deferred": [
                "original_farm_animal_sprite_rebuilds",
                "generic_multi_tile_stamp_runtime_binding",
                "full_building_roof_wall_compositor",
            ],
        },
    }
    coverage_path.write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_tile_variants()
    build_object_atlas()
    build_authoring_libraries()
    update_manifests()
    build_preview()
    print("Generated Pass 60 production terrain variants, expanded live objects, and authoring stamp libraries")
