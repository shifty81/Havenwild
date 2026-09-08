#!/usr/bin/env python3
"""Promote reviewed LPC grid cells into Havenwild's stable padded terrain atlas."""

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PROMOTION = ROOT / "content/assets/intake/lpc_terrain_promotion_v0_1.json"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"


def paste_extruded(atlas, tile, rect):
    x, y, width, height = rect
    if (width, height) != tile.size:
        raise ValueError(f"manifest rect {rect} does not match {tile.size}")
    atlas.paste(tile, (x, y))
    atlas.paste(tile.crop((0, 0, width, 1)), (x, y - 1))
    atlas.paste(tile.crop((0, height - 1, width, height)), (x, y + height))
    atlas.paste(tile.crop((0, 0, 1, height)), (x - 1, y))
    atlas.paste(tile.crop((width - 1, 0, width, height)), (x + width, y))
    atlas.putpixel((x - 1, y - 1), tile.getpixel((0, 0)))
    atlas.putpixel((x + width, y - 1), tile.getpixel((width - 1, 0)))
    atlas.putpixel((x - 1, y + height), tile.getpixel((0, height - 1)))
    atlas.putpixel((x + width, y + height), tile.getpixel((width - 1, height - 1)))


def main():
    promotion = json.loads(PROMOTION.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = Image.open(ROOT / promotion["source"]).convert("RGBA")
    output = ROOT / manifest["output"]
    atlas = Image.open(output).convert("RGBA")
    cell_size = promotion["cellSize"]
    entries = {entry["id"]: entry for entry in manifest["tiles"]}
    promoted = 0
    for tile_id, cells in promotion["baseTileCells"].items():
        entry = entries.get(tile_id)
        if entry is None:
            continue
        destinations = entry.get("variantRects") or [entry["rect"]]
        for index, destination in enumerate(destinations):
            column, row = cells[index % len(cells)]
            crop = source.crop((
                column * cell_size,
                row * cell_size,
                (column + 1) * cell_size,
                (row + 1) * cell_size,
            ))
            paste_extruded(atlas, crop, destination)
            promoted += 1
    atlas.save(output, optimize=False, compress_level=9)
    manifest["source"] = "tools/automation/terrain/Promote-LpcTerrainV84.py"
    manifest["license"] = promotion["license"]
    manifest["notes"] = [
        "Reviewed LPC Revised summer terrain cells promoted by stable semantic TileKind.",
        "Exact zero-based source coordinates are recorded in lpc_terrain_promotion_v0_1.json.",
        "Lanea Zimmerman (Sharm) and Eliza Wyatt (DeathsDarling); OGA-BY 3.0.",
        "Atlas padding and edge extrusion are preserved for seamless runtime sampling."
    ]
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Promoted {promoted} LPC terrain variants into {output}")


if __name__ == "__main__":
    main()
