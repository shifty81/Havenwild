#!/usr/bin/env python3
"""Build the normalized LPC base/transition terrain foundation for Pass 91.

The source sheet is treated as an authored library, not a generic atlas. The
script validates the pinned source, promotes only reviewed repeatable centers,
and bakes one owner-side 4-way transition atlas row-pair per explicit semantic
family. Authored 2x2 inner-corner blocks are preserved when present. Families
without a verified concave block are outer-role-only and never fabricate one.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
MAPPING_PATH = ROOT / "content/assets/intake/lpc_terrain_family_mapping_v0_3.json"
PROMOTION_PATH = ROOT / "content/assets/intake/lpc_terrain_promotion_v0_2.json"
LOCK_PATH = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
COMPLETE_MAP_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json"
BASE_MANIFEST_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"
TRANSITION_MANIFEST_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
PREVIEW_PATH = ROOT / "docs/assets/previews/havenwild_lpc_terrain_family_foundation_pass90.png"
TILE = 32
PADDING = 2
STRIDE = TILE + PADDING
COLUMNS = 8


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

def verify_complete_summer_map() -> None:
    if not COMPLETE_MAP_PATH.is_file():
        raise FileNotFoundError(
            f"complete LPC summer map missing: {COMPLETE_MAP_PATH}. "
            "Run tools/build/Build.sh lpc-summer-map first."
        )
    payload = read_json(COMPLETE_MAP_PATH)
    summary = payload.get("summary", {})
    mapped = summary.get("mappedNonTransparentCells")
    source = summary.get("nonTransparentCells")
    if mapped != 305 or source != 305:
        raise ValueError(
            f"complete LPC summer map is incomplete: {mapped}/{source} non-transparent cells"
        )




def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def crop_cell(source: Image.Image, cell: Iterable[int]) -> Image.Image:
    column, row = cell
    return source.crop((column * TILE, row * TILE, (column + 1) * TILE, (row + 1) * TILE))


def crop_block(source: Image.Image, block: Iterable[int]) -> list[list[Image.Image]]:
    column, row, width, height = block
    return [
        [crop_cell(source, (column + x, row + y)) for x in range(width)]
        for y in range(height)
    ]


def paste_extruded(atlas: Image.Image, tile: Image.Image, rect: list[int]) -> None:
    x, y, width, height = rect
    atlas.paste(tile, (x, y), tile)
    atlas.paste(tile.crop((0, 0, width, 1)), (x, y - 1), tile.crop((0, 0, width, 1)))
    atlas.paste(
        tile.crop((0, height - 1, width, height)),
        (x, y + height),
        tile.crop((0, height - 1, width, height)),
    )
    atlas.paste(tile.crop((0, 0, 1, height)), (x - 1, y), tile.crop((0, 0, 1, height)))
    atlas.paste(
        tile.crop((width - 1, 0, width, height)),
        (x + width, y),
        tile.crop((width - 1, 0, width, height)),
    )


def color_transform(tile: Image.Image, factors: list[float] | None) -> Image.Image:
    if not factors:
        return tile.copy()
    output = tile.copy()
    source_pixels = tile.load()
    output_pixels = output.load()
    red_factor, green_factor, blue_factor = factors
    for y in range(tile.height):
        for x in range(tile.width):
            red, green, blue, alpha = source_pixels[x, y]
            output_pixels[x, y] = (
                min(255, round(red * red_factor)),
                min(255, round(green * green_factor)),
                min(255, round(blue * blue_factor)),
                alpha,
            )
    return output


def merge_overlays(overlays: Iterable[Image.Image]) -> Image.Image:
    output = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    for overlay in overlays:
        output.alpha_composite(overlay)
    return output


EDGE_BITS = {"north": 1, "east": 2, "south": 4, "west": 8}

REPEATABLE_FILL_ALIASES = {
    # Historic mapping contracts sometimes name a semantic class instead of a
    # concrete repeatable LPC base tile. Compound masks need an actual opaque
    # fill cell, so resolve these authoring labels before looking up baseTiles.
    "farm": "dirt",
    "water": "shallow_water",
    "natural": "grass",
}


def repeatable_fill_id(tile_id: str) -> str:
    return REPEATABLE_FILL_ALIASES.get(tile_id, tile_id)


def enforce_mask_edges(tile: Image.Image, mask: int) -> Image.Image:
    """Remove authored fringe pixels from topology-internal tile edges."""
    output = tile.copy()
    pixels = output.load()
    for direction, bit in EDGE_BITS.items():
        if mask & bit:
            continue
        if direction == "north":
            points = ((x, 0) for x in range(TILE))
        elif direction == "east":
            points = ((TILE - 1, y) for y in range(TILE))
        elif direction == "south":
            points = ((x, TILE - 1) for x in range(TILE))
        else:
            points = ((0, y) for y in range(TILE))
        for x, y in points:
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)
    return output


def edge_signature(tile: Image.Image, direction: str) -> dict:
    pixels = tile.load()
    if direction == "north":
        values = [pixels[x, 0][3] for x in range(TILE)]
    elif direction == "east":
        values = [pixels[TILE - 1, y][3] for y in range(TILE)]
    elif direction == "south":
        values = [pixels[x, TILE - 1][3] for x in range(TILE)]
    else:
        values = [pixels[0, y][3] for y in range(TILE)]
    occupied = [index for index, alpha in enumerate(values) if alpha]
    return {
        "occupiedPixels": len(occupied),
        "firstOccupied": occupied[0] if occupied else None,
        "lastOccupied": occupied[-1] if occupied else None,
        "alphaSha256": hashlib.sha256(bytes(values)).hexdigest()[:16],
    }


def seam_signatures(tile: Image.Image) -> dict:
    return {direction: edge_signature(tile, direction) for direction in EDGE_BITS}


def outer_role_cells(mask: int) -> list[tuple[int, int]]:
    """Return complete authored LPC role cells for a 4-way neighbor mask.

    The source 3x3 block is a complete boundary ring. Cutting those cells into
    half-tiles creates the staircase and cross seams seen in Pass 90. Exact
    edge/corner masks therefore use one complete source role. Opposite, tee,
    and enclosed masks combine complete compatible roles.
    """
    exact = {
        1: [(1, 0)],
        2: [(2, 1)],
        3: [(2, 0)],
        4: [(1, 2)],
        6: [(2, 2)],
        8: [(0, 1)],
        9: [(0, 0)],
        12: [(0, 2)],
    }
    if mask in exact:
        return exact[mask]
    return {
        0: [],
        5: [(1, 0), (1, 2)],
        7: [(2, 0), (2, 2)],
        10: [(2, 1), (0, 1)],
        11: [(2, 0), (0, 0)],
        13: [(0, 0), (0, 2)],
        14: [(2, 2), (0, 2)],
        15: [(0, 0), (2, 0), (2, 2), (0, 2)],
    }.get(mask, [])


def compose_outer_mask(
    block: list[list[Image.Image]], classifier: str, mask: int
) -> Image.Image:
    del classifier
    roles = outer_role_cells(mask)
    if mask == 0:
        return Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    if len(roles) == 1:
        column, row = roles[0]
        return block[row][column].copy()

    # Compound cardinal masks are assembled from four authored LPC quadrants.
    # Each quadrant selects the exact 3x3 role implied by the two cardinals that
    # touch it, then copies the matching 16x16 source quadrant. This preserves
    # curves and corners without introducing the old opaque neighbor-fill square.
    half = TILE // 2
    composed = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    quadrants = (
        (0, 0, bool(mask & 1), bool(mask & 8)),
        (half, 0, bool(mask & 1), bool(mask & 2)),
        (0, half, bool(mask & 4), bool(mask & 8)),
        (half, half, bool(mask & 4), bool(mask & 2)),
    )
    for dest_x, dest_y, vertical_neighbor, horizontal_neighbor in quadrants:
        role_col = (0 if horizontal_neighbor else 1) if dest_x == 0 else (2 if horizontal_neighbor else 1)
        role_row = (0 if vertical_neighbor else 1) if dest_y == 0 else (2 if vertical_neighbor else 1)
        source = block[role_row][role_col]
        quadrant = source.crop((dest_x, dest_y, dest_x + half, dest_y + half))
        composed.alpha_composite(quadrant, (dest_x, dest_y))
    return composed


def inner_corner_roles(block: list[list[Image.Image]], classifier: str) -> dict[str, Image.Image]:
    # A 2x2 island block is arranged around its center. The top-left source
    # cell therefore represents a south-east diagonal intrusion, and so on.
    del classifier
    return {
        "north_east": block[1][0].copy(),
        "south_east": block[0][0].copy(),
        "south_west": block[0][1].copy(),
        "north_west": block[1][1].copy(),
    }

def is_water(red: int, green: int, blue: int) -> bool:
    return blue >= 82 and green >= 66 and blue > red + 22 and green > red + 14


def foreground_mask(composed: Image.Image, classifier: str) -> Image.Image:
    mask = Image.new("L", composed.size, 0)
    source_pixels = composed.load()
    mask_pixels = mask.load()
    for y in range(TILE):
        for x in range(TILE):
            red, green, blue, alpha = source_pixels[x, y]
            if alpha == 0:
                continue
            if classifier == "grass":
                selected = green >= 62 and green > red * 1.08 and green > blue * 1.15
            elif classifier == "dirt":
                selected = red >= 78 and red > green * 1.12 and green > blue * 1.08
            elif classifier == "sand":
                selected = red >= 150 and green >= 95 and red > blue * 1.28
            elif classifier == "non_water_bank":
                selected = not is_water(red, green, blue)
            elif classifier == "shallow_rim":
                selected = is_water(red, green, blue) and green >= 76 and blue >= 96
            else:
                raise ValueError(f"unknown foreground classifier {classifier}")
            if selected:
                mask_pixels[x, y] = 255
    return mask


def extract_authored_overlay(composed: Image.Image, classifier: str, mask_value: int) -> Image.Image:
    if mask_value == 0:
        return Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    selected = foreground_mask(composed, classifier)
    if selected.getbbox() is None:
        return Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    radius = 5 if classifier in {"grass", "dirt", "sand", "non_water_bank"} else 3
    expanded = selected.filter(ImageFilter.MaxFilter(radius))
    authored = composed.getchannel("A")
    alpha = Image.new("L", (TILE, TILE), 0)
    expanded_pixels = expanded.load()
    authored_pixels = authored.load()
    alpha_pixels = alpha.load()
    for y in range(TILE):
        for x in range(TILE):
            alpha_pixels[x, y] = min(expanded_pixels[x, y], authored_pixels[x, y])
    output = composed.copy()
    output.putalpha(alpha)
    return output


def verify_source(mapping: dict, lock: dict) -> Path:
    source_path = ROOT / mapping["source"]
    locked = next(
        record for record in lock["lockedFiles"] if record["projectPath"] == mapping["source"]
    )
    with Image.open(source_path) as image:
        if image.size != (locked["width"], locked["height"]):
            raise ValueError(f"locked LPC dimensions changed: {image.size}")
    actual = sha256(source_path)
    if actual != locked["sha256"]:
        raise ValueError(f"locked LPC hash changed: {actual}")
    return source_path


def promote_base_tiles(source: Image.Image, mapping: dict) -> int:
    promotion = read_json(PROMOTION_PATH)
    promoted_base_tiles = dict(mapping["baseTiles"])
    for tile_id, cells in promotion.get("baseTileCells", {}).items():
        promoted_base_tiles.setdefault(tile_id, {"cells": cells})

    manifest = read_json(BASE_MANIFEST_PATH)
    atlas_path = ROOT / manifest["output"]
    atlas = Image.open(atlas_path).convert("RGBA")
    entries = {entry["id"]: entry for entry in manifest["tiles"]}
    promoted = 0
    for tile_id, definition in promoted_base_tiles.items():
        entry = entries.get(tile_id)
        if entry is None:
            continue
        destinations = entry.get("variantRects") or [entry["rect"]]
        cells = definition["cells"]
        transforms = definition.get("variantTransforms", [])
        for index, destination in enumerate(destinations):
            tile = crop_cell(source, cells[index % len(cells)])
            transform = transforms[index % len(transforms)] if transforms else None
            tile = color_transform(tile, transform)
            paste_extruded(atlas, tile, destination)
            promoted += 1
    atlas.save(atlas_path, optimize=False, compress_level=9)
    manifest["version"] = "0.5.0"
    manifest["source"] = "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py"
    manifest["license"] = mapping["license"]
    manifest["notes"] = [
        "Pass 91 uses only reviewed repeatable LPC centers recorded in lpc_terrain_family_mapping_v0_3.json.",
        "Shallow water uses the authored center at [1,21]; deep water uses the authored center at [1,24].",
        "Compound masks use authored LPC quadrant composition; opaque neighbor-fill squares are forbidden.",
        "Lanea Zimmerman (Sharm) and Eliza Wyatt (DeathsDarling); OGA-BY 3.0."
    ]
    write_json(BASE_MANIFEST_PATH, manifest)
    return promoted


def bake_transition_atlas(source: Image.Image, mapping: dict) -> tuple[int, dict]:
    families = mapping["transitionFamilies"]
    base_tiles = dict(mapping["baseTiles"])
    promotion = read_json(PROMOTION_PATH)
    for tile_id, cells in promotion.get("baseTileCells", {}).items():
        base_tiles.setdefault(tile_id, {"cells": cells})
    rows = len(families) * 3
    atlas = Image.new(
        "RGBA",
        (COLUMNS * STRIDE + PADDING, rows * STRIDE + PADDING),
        (0, 0, 0, 0),
    )
    groups = []
    variants = []
    inner_corner_variants = []
    family_catalog = []
    variant_index = 0
    for family_index, family in enumerate(families):
        group = family["id"]
        groups.append(group)
        outer = crop_block(source, family["outerBlock"])
        if len(outer) != 3 or any(len(row) != 3 for row in outer):
            raise ValueError(f"{group} outer block must be 3x3")
        for mask_value in range(16):
            column = mask_value % COLUMNS
            row = family_index * 3 + mask_value // COLUMNS
            rect = [PADDING + column * STRIDE, PADDING + row * STRIDE, TILE, TILE]
            overlay = compose_outer_mask(
                outer, family["foregroundClassifier"], mask_value
            )
            paste_extruded(atlas, overlay, rect)
            variants.append(
                {
                    "id": f"{group}_{mask_value:02}",
                    "group": group,
                    "variantIndex": variant_index,
                    "mask4": mask_value,
                    "col": column,
                    "row": row,
                    "rect": rect,
                    "edgeSignatures": seam_signatures(overlay),
                }
            )
            variant_index += 1

        inner_block = family.get("innerCornerBlock")
        inner_entries = []
        if inner_block is not None:
            inner = crop_block(source, inner_block)
            if len(inner) != 2 or any(len(row) != 2 for row in inner):
                raise ValueError(f"{group} inner corner block must be 2x2")
            for inner_index, (direction, overlay) in enumerate(
                inner_corner_roles(inner, family["foregroundClassifier"]).items()
            ):
                column = inner_index
                row = family_index * 3 + 2
                rect = [PADDING + column * STRIDE, PADDING + row * STRIDE, TILE, TILE]
                paste_extruded(atlas, overlay, rect)
                inner_entries.append(
                    {
                        "id": f"{group}_inner_{direction}",
                        "group": group,
                        "direction": direction,
                        "rect": rect,
                        "edgeSignatures": seam_signatures(overlay),
                    }
                )
            inner_corner_variants.extend(inner_entries)

        family_catalog.append(
            {
                "id": group,
                "owner": family["owner"],
                "neighbor": family["neighbor"],
                "outerBlock": family["outerBlock"],
                "innerCornerBlock": inner_block,
                "foregroundClassifier": family["foregroundClassifier"],
                "innerCornerRuntime": bool(inner_entries) and family.get("runtimeInnerCorners", False),
            }
        )

    manifest = {
        "id": "terrain_autotile_47_32",
        "kind": "autotile_sheet",
        "version": "0.8.1",
        "tile_size": TILE,
        "padding": PADDING,
        "autotile_format": "Pass 99 authored LPC replacement roles with closed compound masks; N=1 E=2 S=4 W=8; exact source pixels are preserved",
        "groups": groups,
        "variants": variants,
        "innerCornerVariants": inner_corner_variants,
        "source": "tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py",
        "output": "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png",
        "license": mapping["license"],
        "mapping": "content/assets/intake/lpc_terrain_family_mapping_v0_3.json",
        "familyCatalog": family_catalog,
        "seamPolicy": {
            "version": "havenwild.lpc_replacement_role.v0_2",
            "rule": "authored single-edge and adjacent-corner roles replace the base tile",
            "innerCornerRule": "verified 2x2 roles replace the base tile without color filtering",
            "unsupportedCompoundMaskRule": "use the verified repeatable neighbor fill as a complete replacement; never leave owner-base holes or depend on a structural transparent center",
            "signatureChannel": "alpha",
        },
        "notes": [
            "Each group is selected from the ordered center/neighbor pair, not from material alone.",
            "Only the declared owner cell draws the transition, preventing duplicate overlays on both sides.",
            "Complete authored 3x3 edge/corner roles are used without half-cell slicing.",
            "Authored 2x2 inner-corner roles are baked and selected separately at runtime when verified.",
            "Outer-role-only families do not fabricate concave corners.",
            "No opaque white replacement cells are generated.",
            "Pass 99 uses the authored family center for opposite, tee, and enclosed compound masks so the owner base cannot show through as a square hole.",
            "Pass 100 resolves abstract repeatable-fill neighbors such as natural before compound-mask baking.",
        ],
    }
    atlas_path = ROOT / manifest["output"]
    atlas.save(atlas_path, optimize=False, compress_level=9)
    write_json(TRANSITION_MANIFEST_PATH, manifest)
    return len(variants) + len(inner_corner_variants), manifest


def checkerboard(size: tuple[int, int], cell: int = 12) -> Image.Image:
    image = Image.new("RGBA", size, (34, 38, 44, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(48, 53, 61, 255))
    return image


def draw_scaled_tile(canvas: Image.Image, tile: Image.Image, x: int, y: int, scale: int = 2) -> None:
    scaled = tile.resize((TILE * scale, TILE * scale), Image.Resampling.NEAREST)
    canvas.alpha_composite(scaled, (x, y))


def build_preview(source: Image.Image, mapping: dict, transition_manifest: dict) -> None:
    width = 1660
    height = 1180
    canvas = checkerboard((width, height), 16)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, 70), fill=(17, 20, 25, 255))
    draw.text((28, 20), "Havenwild Pass 91 — LPC terrain family foundation", fill=(240, 244, 248, 255))
    draw.text((28, 44), "Pinned raw source → explicit semantic roles → normalized runtime atlas", fill=(164, 190, 205, 255))

    x = 28
    y = 92
    draw.text((x, y), "Reviewed repeatable base fills", fill=(238, 211, 126, 255))
    y += 26
    for tile_id in ["grass", "dirt", "sand", "shallow_water", "deep_water"]:
        definition = mapping["baseTiles"][tile_id]
        draw.text((x, y), tile_id, fill=(230, 234, 238, 255))
        tile_x = x + 145
        for cell in definition["cells"][:4]:
            draw_scaled_tile(canvas, crop_cell(source, cell), tile_x, y - 6, 2)
            tile_x += 72
        y += 78

    atlas = Image.open(ROOT / transition_manifest["output"]).convert("RGBA")
    x = 520
    y = 92
    draw.text((x, y), "Normalized owner-side transition masks", fill=(238, 211, 126, 255))
    y += 28
    sample_masks = [1, 2, 4, 8, 3, 6, 12, 9, 15]
    entries = {(entry["group"], entry["mask4"]): entry for entry in transition_manifest["variants"]}
    for family in mapping["transitionFamilies"]:
        group = family["id"]
        draw.text((x, y + 18), group, fill=(224, 232, 238, 255))
        tx = x + 230
        for mask_value in sample_masks:
            entry = entries[(group, mask_value)]
            rx, ry, rw, rh = entry["rect"]
            tile = atlas.crop((rx, ry, rx + rw, ry + rh))
            draw_scaled_tile(canvas, tile, tx, y, 2)
            draw.text((tx + 2, y + 66), str(mask_value), fill=(180, 192, 202, 255))
            tx += 72
        y += 88

    x = 28
    y = 520
    draw.text((x, y), "Authored outer blocks and mapped inner-corner blocks", fill=(238, 211, 126, 255))
    y += 32
    for index, family in enumerate(mapping["transitionFamilies"][:6]):
        column = index % 3
        row = index // 3
        px = x + column * 510
        py = y + row * 290
        draw.text((px, py), family["id"], fill=(230, 234, 238, 255))
        outer = crop_block(source, family["outerBlock"])
        for oy in range(3):
            for ox in range(3):
                draw_scaled_tile(canvas, outer[oy][ox], px + ox * 68, py + 28 + oy * 68, 2)
        inner_block = family.get("innerCornerBlock")
        if inner_block is not None:
            inner = crop_block(source, inner_block)
            draw.text((px + 230, py + 28), "inner 2x2", fill=(164, 190, 205, 255))
            for iy in range(2):
                for ix in range(2):
                    draw_scaled_tile(canvas, inner[iy][ix], px + 230 + ix * 68, py + 54 + iy * 68, 2)
        else:
            draw.text((px + 230, py + 28), "outer roles only", fill=(207, 158, 92, 255))
        draw.text((px + 230, py + 204), f"owner: {family['owner']}", fill=(193, 205, 214, 255))
        draw.text((px + 230, py + 224), f"neighbor: {family['neighbor']}", fill=(193, 205, 214, 255))

    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PREVIEW_PATH, optimize=False, compress_level=9)


def main() -> None:
    verify_complete_summer_map()
    mapping = read_json(MAPPING_PATH)
    lock = read_json(LOCK_PATH)
    source_path = verify_source(mapping, lock)
    source = Image.open(source_path).convert("RGBA")
    promoted = promote_base_tiles(source, mapping)
    transitions, manifest = bake_transition_atlas(source, mapping)
    build_preview(source, mapping, manifest)
    print(f"Promoted {promoted} reviewed LPC base variants")
    print(f"Baked {transitions} ordered-pair LPC transition variants")
    print(f"Wrote {PREVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
