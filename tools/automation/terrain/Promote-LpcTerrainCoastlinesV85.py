#!/usr/bin/env python3
"""Promote corrected LPC base terrain and contour-backed transition overlays.

The LPC sheet contains complete material-pair transition blocks. Havenwild renders
transitions over semantic base tiles, so this baker extracts the exact LPC edge
contours as transparent masks instead of stamping an incompatible full tile over
both sides of a material boundary.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PROMOTION = ROOT / "content/assets/intake/lpc_terrain_promotion_v0_2.json"
BASE_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"
TRANSITION_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
TILE = 32
PADDING = 2
CELL_STRIDE = TILE + PADDING
ATLAS_COLUMNS = 8


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def crop_cell(source: Image.Image, column: int, row: int, cell_size: int) -> Image.Image:
    return source.crop(
        (
            column * cell_size,
            row * cell_size,
            (column + 1) * cell_size,
            (row + 1) * cell_size,
        )
    )


def paste_extruded(atlas: Image.Image, tile: Image.Image, rect: list[int]) -> None:
    x, y, width, height = rect
    if (width, height) != tile.size:
        raise ValueError(f"manifest rect {rect} does not match tile size {tile.size}")
    atlas.paste(tile, (x, y))
    atlas.paste(tile.crop((0, 0, width, 1)), (x, y - 1))
    atlas.paste(tile.crop((0, height - 1, width, height)), (x, y + height))
    atlas.paste(tile.crop((0, 0, 1, height)), (x - 1, y))
    atlas.paste(tile.crop((width - 1, 0, width, height)), (x + width, y))
    atlas.putpixel((x - 1, y - 1), tile.getpixel((0, 0)))
    atlas.putpixel((x + width, y - 1), tile.getpixel((width - 1, 0)))
    atlas.putpixel((x - 1, y + height), tile.getpixel((0, height - 1)))
    atlas.putpixel((x + width, y + height), tile.getpixel((width - 1, height - 1)))


def compose_transition(block: list[list[Image.Image]], mask: int) -> Image.Image:
    center = block[1][1].copy()
    north = bool(mask & 1)
    east = bool(mask & 2)
    south = bool(mask & 4)
    west = bool(mask & 8)

    if north:
        center.paste(block[0][1].crop((0, 0, TILE, TILE // 2)), (0, 0))
    if south:
        center.paste(block[2][1].crop((0, TILE // 2, TILE, TILE)), (0, TILE // 2))
    if west:
        center.paste(block[1][0].crop((0, 0, TILE // 2, TILE)), (0, 0))
    if east:
        center.paste(block[1][2].crop((TILE // 2, 0, TILE, TILE)), (TILE // 2, 0))

    if north and west:
        center.paste(block[0][0].crop((0, 0, TILE // 2, TILE // 2)), (0, 0))
    if north and east:
        center.paste(
            block[0][2].crop((TILE // 2, 0, TILE, TILE // 2)),
            (TILE // 2, 0),
        )
    if south and west:
        center.paste(
            block[2][0].crop((0, TILE // 2, TILE // 2, TILE)),
            (0, TILE // 2),
        )
    if south and east:
        center.paste(
            block[2][2].crop((TILE // 2, TILE // 2, TILE, TILE)),
            (TILE // 2, TILE // 2),
        )
    return center


def material_difference_mask(composed: Image.Image, center: Image.Image, mask: int) -> Image.Image:
    if mask == 0:
        return Image.new("RGBA", (TILE, TILE), (255, 255, 255, 0))
    output = Image.new("RGBA", (TILE, TILE), (255, 255, 255, 0))
    source_pixels = composed.load()
    center_pixels = center.load()
    output_pixels = output.load()
    for y in range(TILE):
        for x in range(TILE):
            sr, sg, sb, sa = source_pixels[x, y]
            cr, cg, cb, ca = center_pixels[x, y]
            if sa == 0:
                continue
            difference = abs(sr - cr) + abs(sg - cg) + abs(sb - cb) + abs(sa - ca)
            # Ignore normal texture variation inside the center material while
            # preserving the authored fringe and neighboring material contour.
            alpha = max(0, min(255, int((difference - 42) * 2.35)))
            if alpha:
                output_pixels[x, y] = (255, 255, 255, alpha)
    return output


def promote_base_tiles(source: Image.Image, promotion: dict) -> int:
    manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    output = ROOT / manifest["output"]
    atlas = Image.open(output).convert("RGBA")
    entries = {entry["id"]: entry for entry in manifest["tiles"]}
    promoted = 0
    for tile_id, cells in promotion["baseTileCells"].items():
        entry = entries.get(tile_id)
        if entry is None:
            continue
        destinations = entry.get("variantRects") or [entry["rect"]]
        for index, destination in enumerate(destinations):
            column, row = cells[index % len(cells)]
            tile = crop_cell(source, column, row, promotion["cellSize"])
            paste_extruded(atlas, tile, destination)
            promoted += 1
    atlas.save(output, optimize=False, compress_level=9)
    manifest["source"] = "tools/automation/terrain/Promote-LpcTerrainCoastlinesV85.py"
    manifest["license"] = promotion["license"]
    manifest["notes"] = [
        "Corrected reviewed LPC Revised summer terrain coordinates by semantic TileKind.",
        "Grass, dirt, pale sand, wet sand, shallow water, and deep water now use opaque repeatable interior cells rather than transition or transparent cells.",
        "Exact zero-based coordinates are recorded in lpc_terrain_promotion_v0_2.json.",
        "Lanea Zimmerman (Sharm) and Eliza Wyatt (DeathsDarling); OGA-BY 3.0.",
        "Atlas padding and edge extrusion remain stable for save and renderer compatibility."
    ]
    write_json(BASE_MANIFEST, manifest)
    return promoted


def promote_transition_masks(source: Image.Image, promotion: dict) -> int:
    manifest = json.loads(TRANSITION_MANIFEST.read_text(encoding="utf-8"))
    variants = manifest["variants"]
    rows = max(variant["row"] for variant in variants) + 1
    atlas = Image.new(
        "RGBA",
        (ATLAS_COLUMNS * CELL_STRIDE + PADDING, rows * CELL_STRIDE + PADDING),
        (0, 0, 0, 0),
    )
    blocks: dict[str, list[list[Image.Image]]] = {}
    for group, (column, row, width, height) in promotion["transitionMaskBlocks"].items():
        if (width, height) != (3, 3):
            raise ValueError(f"{group} must be a 3x3 LPC transition block")
        blocks[group] = [
            [
                crop_cell(source, column + dx, row + dy, promotion["cellSize"])
                for dx in range(3)
            ]
            for dy in range(3)
        ]

    baked = 0
    for variant in variants:
        group = variant["group"]
        block = blocks[group]
        mask = int(variant["mask4"])
        composed = compose_transition(block, mask)
        overlay = material_difference_mask(composed, block[1][1], mask)
        paste_extruded(atlas, overlay, variant["rect"])
        baked += 1

    output = ROOT / manifest["output"]
    atlas.save(output, optimize=False, compress_level=9)
    manifest["version"] = "0.2.0"
    manifest["autotile_format"] = (
        "4-way transparent LPC contour overlay masks; N=1 E=2 S=4 W=8; "
        "full semantic base textures remain visible beneath the transition"
    )
    manifest["source"] = "tools/automation/terrain/Promote-LpcTerrainCoastlinesV85.py"
    manifest["license"] = promotion["license"]
    manifest["notes"] = [
        "Transition geometry is extracted from reviewed LPC 3x3 material-pair blocks.",
        "The atlas stores transparent contour masks so one semantic group can tint correctly for either side of a boundary.",
        "Mask 0 is transparent; mask bits follow north=1, east=2, south=4, west=8.",
        "Lanea Zimmerman (Sharm) and Eliza Wyatt (DeathsDarling); OGA-BY 3.0."
    ]
    write_json(TRANSITION_MANIFEST, manifest)
    return baked


def main() -> None:
    promotion = json.loads(PROMOTION.read_text(encoding="utf-8"))
    source = Image.open(ROOT / promotion["source"]).convert("RGBA")
    promoted = promote_base_tiles(source, promotion)
    transitions = promote_transition_masks(source, promotion)
    print(f"Promoted {promoted} corrected LPC base variants")
    print(f"Baked {transitions} LPC contour-backed transition masks")


if __name__ == "__main__":
    main()
