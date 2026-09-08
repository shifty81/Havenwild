#!/usr/bin/env python3
"""Build a complete-tile LPC mapped terrain atlas from terrain-map-v7.tsx."""
from __future__ import annotations

import json
import hashlib
import math
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = ROOT / "content/assets/lpc/source/lpc-terrains-v7"
TSX = SOURCE_DIR / "terrain-map-v7.tsx"
PNG = SOURCE_DIR / "terrain-map-v7.png"
VARIANT_TSX = SOURCE_DIR / "terrain-v7.tsx"
VARIANT_PNG = SOURCE_DIR / "terrain-v7.png"
CREDITS = SOURCE_DIR / "CREDITS-terrain.txt"
OUT_DIR = ROOT / "assets/generated/worldgen_v0_1/terrain"
OUT_PNG = OUT_DIR / "lpc_mapped_terrain_v7_32.png"
OUT_JSON = OUT_DIR / "lpc_mapped_terrain_v7_32.json"
PREVIEW = ROOT / "docs/audits/generated/havenwild_terrain_standard_v1_runtime_atlas_preview.png"
DEPENDENCY_RESTORER = ROOT / "tools/automation/dependencies/Ensure-LpcTerrainV7Dependency.py"


def ensure_lpc_terrain_v7_source() -> None:
    required = (TSX, PNG, VARIANT_TSX, VARIANT_PNG, CREDITS)
    if all(path.is_file() for path in required):
        return
    if not DEPENDENCY_RESTORER.is_file():
        raise FileNotFoundError(
            f"LPC Terrains V7 dependency restorer is missing: {DEPENDENCY_RESTORER}"
        )
    print("LPC Terrains V7 source is missing; invoking portable dependency restore")
    subprocess.run([sys.executable, str(DEPENDENCY_RESTORER)], cwd=ROOT, check=True)


# Havenwild runtime terrain code -> Tiled terrain name in lpc-terrains v7.
# Structural floors, walls, bridges, and authoring overlays stay on their
# dedicated autotile/object paths. WetSand also remains on the existing coast
# path: Water_Shallows_Sand contains visible water and is not a dry wet-sand
# material. Only true presentation aliases share a source material. Gameplay/topology
# family grouping must never collapse exact visual identity here.
TILE_TO_TERRAIN = OrderedDict([
    ("grass", "Grass"),
    ("tall_grass", "Grass"),
    ("dirt", "Dirt_Brown"),
    ("sand", "Sand"),
    ("wet_sand", "Sand"),
    ("pebble_shore", "Gravel_1"),
    ("road", "Dirt_Tan"),
    ("stone_path", "Stone_Tan"),
    ("mountain_path", "Dirt_Roots"),
    ("mountain_rock", "Rock_Dark"),
    ("cave_floor", "Mudstone_Brown"),
    ("tilled_soil", "Soil"),
    ("watered_soil", "Mud_Brown"),
    ("shallow_water", "Water_Shallows_Dirt"),
    ("deep_water", "Water_Deep"),
    ("water", "Water"),
    ("river_water", "Water"),
    ("river_mouth_blend", "Water_Shallows_Dirt"),
    ("shore_foam", "Water_Shallows_Sand"),
    ("mud_bank", "Mud_Brown"),
    ("ocean_shallow", "Water_Shallows_Sand"),
    ("ocean_deep", "Water_Deep"),
])

KEY_PAIRS = [
    ("Grass", "Grass_Dark"),
    ("Grass", "Sand"),
    ("Dirt_Brown", "Grass"),
    ("Dirt_Tan", "Grass"),
    ("Dirt_Roots", "Grass"),
    ("Grass", "Stone_Tan"),
    ("Dirt_Roots", "Stone_Tan"),
    ("Mud_Brown", "Mudstone_Brown"),
    ("Mudstone_Brown", "Rock_Gray"),
    ("Rock_Dark", "Rock_Gray"),
    ("Sand", "Water_Shallows_Sand"),
    ("Water", "Water_Deep"),
    ("Dirt_Brown", "Water_Shallows_Dirt"),
    ("Sand", "Water"),
    ("Grass", "Water"),
]

CORNER_KEYS = ("topLeft", "topRight", "bottomLeft", "bottomRight")



def topology_for(names: tuple[str, str, str, str]) -> str:
    distinct = list(dict.fromkeys(names))
    if len(distinct) == 1:
        return "fill"
    if len(distinct) >= 3:
        return f"junction_{len(distinct)}_material"
    first = distinct[0]
    bits = tuple(index for index, name in enumerate(names) if name == first)
    if len(bits) in (1, 3):
        return "outer_corner" if len(bits) == 1 else "inner_corner"
    if set(bits) in ({0, 1}, {0, 2}, {1, 3}, {2, 3}):
        return "edge"
    return "diagonal_split"


def read_tileset() -> tuple[list[str], list[dict], int, int, int]:
    if not TSX.is_file() or not PNG.is_file():
        raise FileNotFoundError(
            f"lpc-terrains v7 source missing under {SOURCE_DIR}. Expected terrain-map-v7.tsx/png."
        )
    root = ET.parse(TSX).getroot()
    columns = int(root.attrib["columns"])
    tile_width = int(root.attrib["tilewidth"])
    tile_height = int(root.attrib["tileheight"])
    terrains = [terrain.attrib["name"] for terrain in root.find("terraintypes").findall("terrain")]
    image = Image.open(PNG)
    rows = image.height // tile_height
    entries: list[dict] = []
    chosen: set[tuple[str, str, str, str]] = set()
    allowed = set(TILE_TO_TERRAIN.values())
    for tile in root.findall("tile"):
        terrain = tile.attrib.get("terrain")
        if not terrain:
            continue
        names = tuple(terrains[int(value)] for value in terrain.split(","))
        if any(name not in allowed for name in names):
            continue
        # Use the first occurrence for a tuple; later duplicates are usually decorative alternates.
        if names in chosen:
            continue
        tile_id = int(tile.attrib["id"])
        x = (tile_id % columns) * tile_width
        y = (tile_id // columns) * tile_height
        if x + tile_width > image.width or y + tile_height > image.height:
            raise ValueError(f"tile id {tile_id} rect is outside {PNG.name}")
        chosen.add(names)
        entries.append({
            "tileId": tile_id,
            "corners": {
                "topLeft": names[0],
                "topRight": names[1],
                "bottomLeft": names[2],
                "bottomRight": names[3],
            },
            "topology": topology_for(names),
            "rect": [x, y, tile_width, tile_height],
        })
    entries.sort(key=lambda entry: entry["tileId"])
    return terrains, entries, columns, tile_width, tile_height


def append_pure_fill_variants(
    entries: list[dict], tile_width: int, tile_height: int
) -> tuple[Image.Image, dict[str, int]]:
    """Append every authored pure-fill alternate to the generated runtime atlas.

    terrain-map-v7 contains the complete mixed topology, while terrain-v7 keeps
    the decorative pure-fill alternates. Keeping them in one generated texture
    lets the client and editor use the same deterministic thumbnail/fill path.
    """
    if not VARIANT_TSX.is_file() or not VARIANT_PNG.is_file():
        raise FileNotFoundError("terrain-v7.tsx/png are required for pure-fill variants")
    # V7 lane purity rule: every output pixel must originate from the committed
    # lpc-terrains-v7 source package. Do not replace fills with project atlases,
    # ElizaWy sheets, seasonal sheets, or any other visual family.
    base = Image.open(PNG).convert("RGBA")
    variant_image = Image.open(VARIANT_PNG).convert("RGBA")
    variant_root = ET.parse(VARIANT_TSX).getroot()
    variant_columns = int(variant_root.attrib["columns"])
    variant_names = [
        terrain.attrib["name"]
        for terrain in variant_root.find("terraintypes").findall("terrain")
    ]
    allowed_order = list(dict.fromkeys(TILE_TO_TERRAIN.values()))
    existing_hashes: dict[str, set[str]] = {name: set() for name in allowed_order}
    for entry in entries:
        names = tuple(entry["corners"][key] for key in CORNER_KEYS)
        if len(set(names)) != 1 or names[0] not in existing_hashes:
            continue
        x, y, w, h = entry["rect"]
        digest = hashlib.sha256(base.crop((x, y, x + w, y + h)).tobytes()).hexdigest()
        existing_hashes[names[0]].add(digest)

    authored: list[tuple[str, int, Image.Image]] = []
    for material in allowed_order:
        terrain_index = variant_names.index(material)
        marker = str(terrain_index)
        for tile in variant_root.findall("tile"):
            if tile.attrib.get("terrain", "").split(",") != [marker] * 4:
                continue
            tile_id = int(tile.attrib["id"])
            x = (tile_id % variant_columns) * tile_width
            y = (tile_id // variant_columns) * tile_height
            crop = variant_image.crop((x, y, x + tile_width, y + tile_height))
            if crop.getchannel("A").getbbox() is None:
                continue
            digest = hashlib.sha256(crop.tobytes()).hexdigest()
            if digest in existing_hashes[material]:
                continue
            existing_hashes[material].add(digest)
            authored.append((material, tile_id, crop))

    output_columns = base.width // tile_width
    appended_rows = math.ceil(len(authored) / output_columns)
    atlas = Image.new(
        "RGBA",
        (base.width, base.height + appended_rows * tile_height),
        (0, 0, 0, 0),
    )
    atlas.paste(base, (0, 0), base)
    next_id = max(entry["tileId"] for entry in entries) + 1
    for index, (material, source_tile_id, crop) in enumerate(authored):
        column = index % output_columns
        row = index // output_columns
        x = column * tile_width
        y = base.height + row * tile_height
        atlas.paste(crop, (x, y), crop)
        entries.append({
            "tileId": next_id + index,
            "sourceTileId": source_tile_id,
            "sourceSheet": "terrain-v7.png",
            "corners": {
                "topLeft": material,
                "topRight": material,
                "bottomLeft": material,
                "bottomRight": material,
            },
            "topology": "fill",
            "rect": [x, y, tile_width, tile_height],
        })
    entries.sort(key=lambda entry: entry["tileId"])
    counts = {
        material: sum(
            1
            for entry in entries
            if all(entry["corners"][key] == material for key in CORNER_KEYS)
        )
        for material in allowed_order
    }
    return atlas, counts


def repack_runtime_atlas(
    source: Image.Image, entries: list[dict], tile_width: int, tile_height: int
) -> Image.Image:
    padding = 1
    stride_x = tile_width + padding * 2
    stride_y = tile_height + padding * 2
    columns = 64
    rows = math.ceil(len(entries) / columns)
    atlas = Image.new(
        "RGBA",
        (columns * stride_x + padding, rows * stride_y + padding),
        (0, 0, 0, 0),
    )
    for index, entry in enumerate(entries):
        source_x, source_y, width, height = entry["rect"]
        tile = source.crop((source_x, source_y, source_x + width, source_y + height))
        x = padding + (index % columns) * stride_x
        y = padding + (index // columns) * stride_y
        atlas.paste(tile, (x, y), tile)
        atlas.paste(tile.crop((0, 0, width, 1)), (x, y - 1))
        atlas.paste(tile.crop((0, height - 1, width, height)), (x, y + height))
        atlas.paste(tile.crop((0, 0, 1, height)), (x - 1, y))
        atlas.paste(tile.crop((width - 1, 0, width, height)), (x + width, y))
        atlas.putpixel((x - 1, y - 1), tile.getpixel((0, 0)))
        atlas.putpixel((x + width, y - 1), tile.getpixel((width - 1, 0)))
        atlas.putpixel((x - 1, y + height), tile.getpixel((0, height - 1)))
        atlas.putpixel((x + width, y + height), tile.getpixel((width - 1, height - 1)))
        entry["rect"] = [x, y, width, height]
    return atlas


def write_manifest(
    entries: list[dict], atlas: Image.Image, fill_variant_counts: dict[str, int], tile_width: int, tile_height: int
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT_PNG, optimize=False, compress_level=9)
    topology_counts: dict[str, int] = {}
    pair_shapes: dict[str, set[tuple[str, str, str, str]]] = {}
    for entry in entries:
        topology = entry["topology"]
        topology_counts[topology] = topology_counts.get(topology, 0) + 1
        names = tuple(entry["corners"][key] for key in CORNER_KEYS)
        pair = sorted(set(names))
        if len(pair) == 2:
            pair_shapes.setdefault(" <-> ".join(pair), set()).add(names)
    payload = {
        "id": "lpc_mapped_terrain_v7_32",
        "kind": "lpc_mapped_terrain_corner_tileset",
        "version": "0.4.0",
        "tileSize": [tile_width, tile_height],
        "padding": 1,
        "atlasLayout": "compact_64_column_extruded",
        "output": "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png",
        "source": "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx",
        "license": "OpenGameArt LPC terrain credits in content/assets/lpc/source/lpc-terrains-v7/CREDITS-terrain.txt",
        "runtimePolicy": "pure V7 style-pack atlas: every output pixel comes only from terrain-map-v7.png or terrain-v7.png; no ElizaWy, seasonal, common-base, or cross-family substitutions are permitted",
        "stylePackLane": "lpc_terrain_v7",
        "sourcePurity": {
            "status": "isolated",
            "allowedRoots": ["content/assets/lpc/source/lpc-terrains-v7"],
            "forbiddenFamilies": ["elizawy_lpc_revised", "common_base_terrain_32", "seasonal_terrain"]
        },
        "tileKindTerrainMap": TILE_TO_TERRAIN,
        "coverage": {
            "mappedTileKinds": len(TILE_TO_TERRAIN),
            "mappedSourceMaterials": len(set(TILE_TO_TERRAIN.values())),
            "completeTwoMaterialPairs": sum(len(shapes) == 14 for shapes in pair_shapes.values()),
            "twoMaterialPairShapeTarget": 14,
            "pureFillVariantCounts": fill_variant_counts,
            "topologyCounts": topology_counts,
        },
        "entries": entries,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_preview(entries: list[dict]) -> None:
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(OUT_PNG).convert("RGBA")
    by_pair: dict[tuple[str, str], list[dict]] = {tuple(sorted(pair)): [] for pair in KEY_PAIRS}
    by_fill: dict[str, list[dict]] = {
        material: [] for material in dict.fromkeys(TILE_TO_TERRAIN.values())
    }
    for entry in entries:
        names = tuple(entry["corners"][key] for key in ["topLeft", "topRight", "bottomLeft", "bottomRight"])
        pair = tuple(sorted(set(names)))
        if len(pair) == 1 and pair[0] in by_fill:
            by_fill[pair[0]].append(entry)
        if len(pair) == 2 and pair in by_pair:
            by_pair[pair].append(entry)
    cell = 84
    label_h = 56
    header_h = 42
    width = 14 * cell + 24
    fill_row_h = 86
    fill_rows = math.ceil(len(by_fill) / 4)
    pair_start = header_h + fill_rows * fill_row_h + 16
    height = pair_start + len(KEY_PAIRS) * (cell + label_h) + 24
    canvas = Image.new("RGB", (width, height), (23, 28, 31))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        head = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except OSError:
        font = small = head = None
    draw.text((12, 10), "Pass114 mapped LPC terrain topology + pure-fill variants", fill=(232, 232, 220), font=head)
    for material_index, (material, variants) in enumerate(by_fill.items()):
        group_x = 12 + (material_index % 4) * 294
        group_y = header_h + (material_index // 4) * fill_row_h
        draw.text((group_x, group_y), f"{material} ({len(variants)})", fill=(226, 205, 117), font=font)
        for variant_index, entry in enumerate(variants[:7]):
            rx, ry, rw, rh = entry["rect"]
            tile = image.crop((rx, ry, rx + rw, ry + rh)).resize((36, 36), Image.Resampling.NEAREST)
            x = group_x + variant_index * 40
            canvas.paste(tile, (x, group_y + 20), tile)
            draw.rectangle((x, group_y + 20, x + 35, group_y + 55), outline=(70, 82, 84))
    for row, pair in enumerate(KEY_PAIRS):
        key = tuple(sorted(pair))
        y = pair_start + row * (cell + label_h)
        items = by_pair.get(key, [])[:14]
        draw.text((12, y + 4), f"{pair[0]} <-> {pair[1]} ({len(by_pair.get(key, []))} covered variants)", fill=(226, 205, 117), font=font)
        for index, entry in enumerate(items):
            x = 12 + index * cell
            rx, ry, rw, rh = entry["rect"]
            tile = image.crop((rx, ry, rx + rw, ry + rh)).resize((64, 64), Image.Resampling.NEAREST)
            canvas.paste(tile, (x, y + 24), tile)
            draw.rectangle((x, y + 24, x + 63, y + 87), outline=(70, 82, 84))
            names = [entry["corners"][corner] for corner in ["topLeft", "topRight", "bottomLeft", "bottomRight"]]
            initials = "".join(name[0] for name in names)
            draw.text((x, y + 90), f"{index + 1:02d} id {entry['tileId']}", fill=(210, 218, 210), font=small)
            draw.text((x, y + 104), initials, fill=(156, 178, 186), font=small)
    canvas.save(PREVIEW)


def main() -> int:
    ensure_lpc_terrain_v7_source()
    _, entries, _, tile_width, tile_height = read_tileset()
    if not CREDITS.is_file():
        raise FileNotFoundError(f"missing terrain credits: {CREDITS}")
    source_atlas, fill_variant_counts = append_pure_fill_variants(entries, tile_width, tile_height)
    atlas = repack_runtime_atlas(source_atlas, entries, tile_width, tile_height)
    write_manifest(entries, atlas, fill_variant_counts, tile_width, tile_height)
    write_preview(entries)
    unique_tuples = {
        tuple(entry["corners"][key] for key in CORNER_KEYS) for entry in entries
    }
    print(f"Generated {OUT_PNG.relative_to(ROOT)}")
    print(
        f"Generated {OUT_JSON.relative_to(ROOT)} with {len(unique_tuples)} exact tuples "
        f"and {sum(fill_variant_counts.values())} pure-fill variants"
    )
    print(f"Wrote {PREVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
