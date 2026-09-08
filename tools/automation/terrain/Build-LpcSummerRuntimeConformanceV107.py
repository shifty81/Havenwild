#!/usr/bin/env python3
"""Build a compact conformance board for active summer runtime terrain families."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "assets/source/licensed/lpc_revised/Terrain/terrain_summer.png"
MAPPING_PATH = ROOT / "content/assets/intake/lpc_terrain_family_mapping_v0_3.json"
ATLAS_MANIFEST_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
OUTPUT = ROOT / "docs/assets/previews/havenwild_lpc_summer_runtime_conformance_v107.png"
TILE = 32
SCALE = 2


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def crop_cell(image: Image.Image, cell: list[int]) -> Image.Image:
    x, y = cell
    return image.crop((x * TILE, y * TILE, (x + 1) * TILE, (y + 1) * TILE))


def paste_tile(canvas: Image.Image, tile: Image.Image, x: int, y: int) -> None:
    canvas.alpha_composite(tile.resize((TILE * SCALE, TILE * SCALE), Image.Resampling.NEAREST), (x, y))


def checkerboard(size: tuple[int, int], cell: int = 12) -> Image.Image:
    image = Image.new("RGBA", size, (30, 34, 39, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(43, 48, 55, 255))
    return image


def main() -> int:
    source = Image.open(SOURCE_PATH).convert("RGBA")
    mapping = read_json(MAPPING_PATH)
    manifest = read_json(ATLAS_MANIFEST_PATH)
    atlas = Image.open(ROOT / manifest["output"]).convert("RGBA")
    entries = {(entry["group"], entry["mask4"]): entry for entry in manifest["variants"]}
    inner = {(entry["group"], entry["direction"]): entry for entry in manifest["innerCornerVariants"]}

    active = [
        ("grass_over_sand", "Grass over dry sand"),
        ("sand_over_wet_sand", "Dry sand over wet sand"),
        ("pebble_path_over_dirt", "Pebble path over dirt"),
    ]
    family_by_id = {item["id"]: item for item in mapping["transitionFamilies"]}
    masks = [1, 2, 4, 8, 3, 6, 12, 9, 15]
    directions = ["north_west", "north_east", "south_west", "south_east"]

    width = 1240
    height = 170 + len(active) * 250
    canvas = checkerboard((width, height))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, 92), fill=(15, 18, 22, 255))
    draw.text((24, 20), "Havenwild Pass 95 — Active summer runtime terrain conformance", fill=(244, 246, 248, 255))
    draw.text((24, 50), "Distinct wet sand + pebble-path semantics; authored outer roles; verified inner roles only", fill=(173, 196, 210, 255))

    for row_index, (group, label) in enumerate(active):
        y = 112 + row_index * 250
        family = family_by_id[group]
        draw.text((24, y), label, fill=(239, 210, 124, 255))
        draw.text((24, y + 22), f"owner={family['owner']}  neighbor={family['neighbor']}", fill=(196, 205, 212, 255))

        sx = 24
        sy = y + 52
        outer_block = family["outerBlock"]
        ox, oy, _, _ = outer_block
        for yy in range(3):
            for xx in range(3):
                paste_tile(canvas, crop_cell(source, [ox + xx, oy + yy]), sx + xx * 66, sy + yy * 66)
        draw.text((sx, sy + 200), "Authored 3x3 source block", fill=(160, 180, 194, 255))

        ax = 250
        draw.text((ax, y + 28), "Normalized outer masks", fill=(220, 228, 234, 255))
        for index, mask in enumerate(masks):
            entry = entries[(group, mask)]
            rx, ry, rw, rh = entry["rect"]
            tile = atlas.crop((rx, ry, rx + rw, ry + rh))
            paste_tile(canvas, tile, ax + index * 72, sy)
            draw.text((ax + index * 72 + 4, sy + 66), str(mask), fill=(186, 197, 205, 255))

        ix = 250
        iy = sy + 100
        draw.text((ix, iy - 24), "Verified concave roles", fill=(220, 228, 234, 255))
        found = 0
        for index, direction in enumerate(directions):
            entry = inner.get((group, direction))
            if entry is None:
                continue
            rx, ry, rw, rh = entry["rect"]
            paste_tile(canvas, atlas.crop((rx, ry, rx + rw, ry + rh)), ix + index * 118, iy)
            draw.text((ix + index * 118, iy + 66), direction.replace("_", " "), fill=(176, 190, 200, 255))
            found += 1
        if found == 0:
            draw.text((ix, iy + 16), "Outer-role-only: no source-authored 2x2 concave block", fill=(216, 157, 92, 255))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, optimize=False, compress_level=9)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
