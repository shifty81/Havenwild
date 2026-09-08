#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageStat

ROOT = Path(__file__).resolve().parents[3]
BASE_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"
BASE_TEXTURE = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png"
OUTPUT_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json"
OUTPUT_TEXTURE = ROOT / "assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.png"

TILE_SIZE = 32
PADDING = 2
COLUMNS = 16
GROUPS = [
    ("road", "road"),
    ("wood_floor", "wood_floor"),
    ("stone_floor", "stone_floor"),
    ("water", "water"),
    ("wall", "wall"),
    ("cliff", "cliff"),
    ("cave_wall", "cave_wall"),
]


def contrast_colors(tile: Image.Image, group: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    mean = ImageStat.Stat(tile.convert("RGB")).mean
    base = tuple(int(value) for value in mean)
    dark = tuple(max(0, int(value * 0.38)) for value in base) + (230,)
    light = tuple(min(255, int(value * 1.35 + 18)) for value in base) + (220,)
    if group == "water":
        dark = (8, 59, 96, 235)
        light = (82, 187, 225, 225)
    elif group == "road":
        dark = (74, 45, 28, 235)
        light = (181, 137, 83, 215)
    elif group in {"wall", "stone_floor"}:
        dark = (48, 51, 49, 235)
        light = (161, 166, 155, 210)
    elif group in {"cliff", "cave_wall"}:
        dark = (37, 37, 42, 240)
        light = (126, 130, 116, 205)
    return dark, light


def render_mask(source: Image.Image, group: str, mask: int) -> Image.Image:
    tile = source.copy().convert("RGBA")
    # Slightly normalize each source tile so the topology overlay stays readable.
    tile = ImageEnhance.Contrast(tile).enhance(1.04)
    draw = ImageDraw.Draw(tile, "RGBA")
    dark, light = contrast_colors(tile, group)

    north = bool(mask & 1)
    east = bool(mask & 2)
    south = bool(mask & 4)
    west = bool(mask & 8)
    center = TILE_SIZE // 2
    arm_half = 3

    # Closed edges are explicit; open edges preserve a centered connection aperture.
    if not north:
        draw.line((0, 1, TILE_SIZE - 1, 1), fill=dark, width=2)
    else:
        draw.line((center - arm_half, 0, center - arm_half, center), fill=dark, width=1)
        draw.line((center + arm_half, 0, center + arm_half, center), fill=light, width=1)
    if not east:
        draw.line((TILE_SIZE - 2, 0, TILE_SIZE - 2, TILE_SIZE - 1), fill=dark, width=2)
    else:
        draw.line((center, center - arm_half, TILE_SIZE - 1, center - arm_half), fill=dark, width=1)
        draw.line((center, center + arm_half, TILE_SIZE - 1, center + arm_half), fill=light, width=1)
    if not south:
        draw.line((0, TILE_SIZE - 2, TILE_SIZE - 1, TILE_SIZE - 2), fill=dark, width=2)
    else:
        draw.line((center - arm_half, center, center - arm_half, TILE_SIZE - 1), fill=dark, width=1)
        draw.line((center + arm_half, center, center + arm_half, TILE_SIZE - 1), fill=light, width=1)
    if not west:
        draw.line((1, 0, 1, TILE_SIZE - 1), fill=dark, width=2)
    else:
        draw.line((0, center - arm_half, center, center - arm_half), fill=dark, width=1)
        draw.line((0, center + arm_half, center, center + arm_half), fill=light, width=1)

    # A compact hub makes isolated/end/corner/tee/cross variants distinguishable at editor zoom.
    draw.rectangle((center - 3, center - 3, center + 3, center + 3), outline=dark, width=1)
    if mask:
        draw.point((center, center), fill=light)
    else:
        draw.rectangle((center - 1, center - 1, center + 1, center + 1), fill=dark)
    return tile


def extrude_padding(atlas: Image.Image, rect: tuple[int, int, int, int]) -> None:
    x, y, w, h = rect
    # One-pixel edge extrusion into available padding; the second pixel remains transparent.
    if x > 0:
        atlas.paste(atlas.crop((x, y, x + 1, y + h)), (x - 1, y))
    if y > 0:
        atlas.paste(atlas.crop((x, y, x + w, y + 1)), (x, y - 1))
    if x + w < atlas.width:
        atlas.paste(atlas.crop((x + w - 1, y, x + w, y + h)), (x + w, y))
    if y + h < atlas.height:
        atlas.paste(atlas.crop((x, y + h - 1, x + w, y + h)), (x, y + h))


def main() -> None:
    base_manifest = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    bindings = {entry["id"]: entry["rect"] for entry in base_manifest["tiles"]}
    base = Image.open(BASE_TEXTURE).convert("RGBA")

    rows = len(GROUPS)
    width = COLUMNS * (TILE_SIZE + PADDING)
    height = rows * (TILE_SIZE + PADDING)
    atlas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    variants: list[dict[str, object]] = []
    groups: list[dict[str, object]] = []

    for row, (group, tile_kind) in enumerate(GROUPS):
        source_rect = bindings[tile_kind]
        sx, sy, sw, sh = source_rect
        if (sw, sh) != (TILE_SIZE, TILE_SIZE):
            raise ValueError(f"{tile_kind} source must remain {TILE_SIZE}x{TILE_SIZE}")
        source = base.crop((sx, sy, sx + sw, sy + sh))
        groups.append({"id": group, "tileKind": tile_kind, "row": row})
        for mask in range(16):
            col = mask
            x = PADDING + col * (TILE_SIZE + PADDING)
            y = PADDING + row * (TILE_SIZE + PADDING)
            rendered = render_mask(source, group, mask)
            atlas.alpha_composite(rendered, (x, y))
            extrude_padding(atlas, (x, y, TILE_SIZE, TILE_SIZE))
            variants.append(
                {
                    "id": f"{group}_{mask:02d}",
                    "group": group,
                    "tileKind": tile_kind,
                    "mask4": mask,
                    "shapeIndex": mask,
                    "col": col,
                    "row": row,
                    "rect": [x, y, TILE_SIZE, TILE_SIZE],
                }
            )

    OUTPUT_TEXTURE.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(OUTPUT_TEXTURE, optimize=True)
    manifest = {
        "id": "live_autotile_16_32",
        "kind": "live_autotile_sheet",
        "version": "0.1.0",
        "tile_size": TILE_SIZE,
        "padding": PADDING,
        "columns": COLUMNS,
        "rows": rows,
        "mask_format": "cardinal NESW bits 1/2/4/8; one atlas cell for every 4-way mask",
        "source": "Pass52 generated from common_base_terrain_32 project-owned source art",
        "generator": "tools/automation/terrain/Generate-LiveAutotileAtlas.py",
        "output": OUTPUT_TEXTURE.relative_to(ROOT).as_posix(),
        "license": "project-generated-placeholder",
        "groups": groups,
        "variants": variants,
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT_TEXTURE.relative_to(ROOT)} ({atlas.width}x{atlas.height})")
    print(f"Generated {OUTPUT_MANIFEST.relative_to(ROOT)} ({len(variants)} bindings)")


if __name__ == "__main__":
    main()
