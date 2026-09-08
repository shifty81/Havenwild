#!/usr/bin/env python3
"""Promote corrected LPC base terrain and narrow contour-backed transitions.

Pass 86 fixes two production errors from Pass 85:
- multi-tile circular pond pieces are no longer repeated as deep-water cells;
- transition atlases contain narrow alpha contours rather than opaque white
  replacement regions.

The source contour geometry still comes from reviewed LPC 3x3 edge/corner
blocks, while the semantic base atlas remains responsible for full terrain
fills.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

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


def apply_color_transform(tile: Image.Image, transform: dict | None) -> Image.Image:
    if not transform:
        return tile
    multiply = transform.get("multiply", [1.0, 1.0, 1.0])
    add = transform.get("add", [0, 0, 0])
    output = tile.copy()
    source_pixels = tile.load()
    output_pixels = output.load()
    for y in range(tile.height):
        for x in range(tile.width):
            red, green, blue, alpha = source_pixels[x, y]
            output_pixels[x, y] = (
                max(0, min(255, round(red * multiply[0] + add[0]))),
                max(0, min(255, round(green * multiply[1] + add[1]))),
                max(0, min(255, round(blue * multiply[2] + add[2]))),
                alpha,
            )
    return output


def compose_transition(block: list[list[Image.Image]], mask: int) -> Image.Image:
    """Compose target-material intrusions using direction-correct LPC pieces.

    The reviewed 3x3 blocks follow the common RPG convention:
      NW, N, NE
       W, _, E
      SW, S, SE

    A north mask therefore uses the *south-edge* source tile because that tile
    contains target material on its north half. Equivalent opposite-source
    selections are used for the other directions and corners.
    """
    output = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    north = bool(mask & 1)
    east = bool(mask & 2)
    south = bool(mask & 4)
    west = bool(mask & 8)

    if north:
        output.paste(block[2][1].crop((0, 0, TILE, TILE // 2)), (0, 0))
    if south:
        output.paste(block[0][1].crop((0, TILE // 2, TILE, TILE)), (0, TILE // 2))
    if west:
        output.paste(block[1][2].crop((0, 0, TILE // 2, TILE)), (0, 0))
    if east:
        output.paste(block[1][0].crop((TILE // 2, 0, TILE, TILE)), (TILE // 2, 0))

    if north and west:
        output.paste(block[2][2].crop((0, 0, TILE // 2, TILE // 2)), (0, 0))
    if north and east:
        output.paste(
            block[2][0].crop((TILE // 2, 0, TILE, TILE // 2)),
            (TILE // 2, 0),
        )
    if south and west:
        output.paste(
            block[0][2].crop((0, TILE // 2, TILE // 2, TILE)),
            (0, TILE // 2),
        )
    if south and east:
        output.paste(
            block[0][0].crop((TILE // 2, TILE // 2, TILE, TILE)),
            (TILE // 2, TILE // 2),
        )
    return output


def target_material_mask(composed: Image.Image, group: str) -> Image.Image:
    """Classify the authored material region used to derive the contour shape."""
    mask = Image.new("L", (TILE, TILE), 0)
    source_pixels = composed.load()
    mask_pixels = mask.load()
    for y in range(TILE):
        for x in range(TILE):
            red, green, blue, alpha = source_pixels[x, y]
            if alpha == 0:
                continue
            if group == "grass_to_dirt":
                is_target = green >= 72 and green > red * 1.12 and green > blue * 1.15
            else:
                # LPC summer water is cyan/blue and separates cleanly from the
                # brown bank colors used by the canonical riverbank block.
                is_target = blue >= 92 and green >= 80 and blue > red + 28 and green > red + 24
            if is_target:
                mask_pixels[x, y] = 255
    return mask


def narrow_contour_overlay(composed: Image.Image, group: str, mask_value: int) -> Image.Image:
    if mask_value == 0:
        return Image.new("RGBA", (TILE, TILE), (255, 255, 255, 0))

    region = target_material_mask(composed, group)
    if region.getbbox() is None:
        return Image.new("RGBA", (TILE, TILE), (255, 255, 255, 0))

    expanded = region.filter(ImageFilter.MaxFilter(7))
    contracted = region.filter(ImageFilter.MinFilter(5))
    contour = ImageChops.subtract(expanded, contracted)

    # Limit the contour to authored source coverage plus a small expansion.
    # This prevents tile-border rectangles from appearing where quadrants were
    # intentionally transparent during composition.
    authored_coverage = composed.getchannel("A").filter(ImageFilter.MaxFilter(5))
    contour = ImageChops.multiply(contour, authored_coverage)

    # Keep contours readable but translucent; runtime/editor tinting provides
    # the semantic material color.
    contour = contour.point(lambda value: min(208, round(value * 0.82)))
    output = Image.new("RGBA", (TILE, TILE), (255, 255, 255, 0))
    output.putalpha(contour)
    return output


def promote_base_tiles(source: Image.Image, promotion: dict) -> int:
    manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    output = ROOT / manifest["output"]
    atlas = Image.open(output).convert("RGBA")
    entries = {entry["id"]: entry for entry in manifest["tiles"]}
    transforms = promotion.get("baseTileTransforms", {})
    promoted = 0
    for tile_id, cells in promotion["baseTileCells"].items():
        entry = entries.get(tile_id)
        if entry is None:
            continue
        destinations = entry.get("variantRects") or [entry["rect"]]
        for index, destination in enumerate(destinations):
            column, row = cells[index % len(cells)]
            tile = crop_cell(source, column, row, promotion["cellSize"])
            tile = apply_color_transform(tile, transforms.get(tile_id))
            paste_extruded(atlas, tile, destination)
            promoted += 1
    atlas.save(output, optimize=False, compress_level=9)
    manifest["source"] = "tools/automation/terrain/Promote-LpcTerrainCoastlinesV86.py"
    manifest["license"] = promotion["license"]
    manifest["notes"] = [
        "Reviewed LPC Revised summer terrain cells promoted by semantic TileKind.",
        "Deep water uses repeatable open-water cells with deterministic color grading; circular pond stamp pieces are excluded from repeatable terrain.",
        "Exact zero-based coordinates and color transforms are recorded in lpc_terrain_promotion_v0_2.json.",
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
        mask_value = int(variant["mask4"])
        composed = compose_transition(blocks[group], mask_value)
        overlay = narrow_contour_overlay(composed, group, mask_value)
        paste_extruded(atlas, overlay, variant["rect"])
        baked += 1

    output = ROOT / manifest["output"]
    atlas.save(output, optimize=False, compress_level=9)
    manifest["version"] = "0.3.0"
    manifest["autotile_format"] = (
        "4-way narrow transparent LPC contour overlays; N=1 E=2 S=4 W=8; "
        "semantic base textures remain visible and no opaque replacement fills are stored"
    )
    manifest["source"] = "tools/automation/terrain/Promote-LpcTerrainCoastlinesV86.py"
    manifest["license"] = promotion["license"]
    manifest["notes"] = [
        "Direction-correct contours are derived from reviewed LPC 3x3 material-pair blocks.",
        "The sand/ocean contour uses the standard LPC riverbank block; rows 20-25 are multi-tile pond stamps and are not valid 4-way shoreline cells.",
        "Mask 0 is transparent and every non-zero mask is a narrow alpha contour rather than a white replacement tile.",
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
    print(f"Baked {transitions} narrow LPC contour transition masks")


if __name__ == "__main__":
    main()
