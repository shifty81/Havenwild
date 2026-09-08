#!/usr/bin/env python3
"""Promote LPC terrain pond families as expandable 9-slice stamp definitions.

The LPC terrain sheet stores expandable families as a 3x3 outer block plus a
2x2 inner-corner block. This pass preserves that source structure instead of
stretching a complete 3x3 pond image or treating its cells as unrelated tiles.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
COMPLETE_MAP_PATH = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_terrain_summer_complete_map_32.json"
CONTRACT_PATH = ROOT / "content/assets/intake/lpc_expandable_terrain_families_v0_1.json"
OUTPUT_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_expandable_ponds_32.json"
PREVIEW_PATH = ROOT / "docs/assets/previews/havenwild_lpc_expandable_ponds_pass87.png"


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
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cell_rect(column: int, row: int, cell_size: int) -> list[int]:
    return [column * cell_size, row * cell_size, cell_size, cell_size]


def crop_cell(source: Image.Image, column: int, row: int, cell_size: int) -> Image.Image:
    return source.crop(
        (
            column * cell_size,
            row * cell_size,
            (column + 1) * cell_size,
            (row + 1) * cell_size,
        )
    )


def validate_block(block: list[int], expected: tuple[int, int], grid: list[int], label: str) -> None:
    x, y, width, height = block
    if (width, height) != expected:
        raise ValueError(f"{label} must be {expected[0]}x{expected[1]}, found {width}x{height}")
    if x < 0 or y < 0 or x + width > grid[0] or y + height > grid[1]:
        raise ValueError(f"{label} {block} lies outside grid {grid}")


def choose_outer_cell(cell_x: int, cell_y: int, width: int, height: int) -> tuple[int, int]:
    source_x = 0 if cell_x == 0 else 2 if cell_x == width - 1 else 1
    source_y = 0 if cell_y == 0 else 2 if cell_y == height - 1 else 1
    return source_x, source_y


def render_rectangle(
    source: Image.Image,
    outer_block: list[int],
    base_fill_cell: list[int],
    size: tuple[int, int],
    cell_size: int,
) -> Image.Image:
    width, height = size
    output = Image.new("RGBA", (width * cell_size, height * cell_size), (0, 0, 0, 0))
    origin_x, origin_y, _, _ = outer_block
    base_tile = crop_cell(source, base_fill_cell[0], base_fill_cell[1], cell_size)
    for y in range(height):
        for x in range(width):
            output.alpha_composite(base_tile, (x * cell_size, y * cell_size))
            source_x, source_y = choose_outer_cell(x, y, width, height)
            tile = crop_cell(source, origin_x + source_x, origin_y + source_y, cell_size)
            output.alpha_composite(tile, (x * cell_size, y * cell_size))
    return output


def checkerboard(size: tuple[int, int], scale: int = 16) -> Image.Image:
    output = Image.new("RGBA", size, (26, 31, 35, 255))
    draw = ImageDraw.Draw(output)
    colors = ((37, 44, 49, 255), (48, 56, 62, 255))
    for y in range(0, size[1], scale):
        for x in range(0, size[0], scale):
            draw.rectangle(
                [x, y, min(size[0], x + scale) - 1, min(size[1], y + scale) - 1],
                fill=colors[((x // scale) + (y // scale)) % 2],
            )
    return output


def build_preview(source: Image.Image, contract: dict) -> None:
    exposed = [family for family in contract["families"] if family.get("exposeAsStamp")]
    sizes = [(3, 3), (5, 4), (8, 6)]
    cell_size = contract["cellSize"]
    padding = 18
    label_height = 28
    row_height = max(height for _, height in sizes) * cell_size + label_height + padding
    column_widths = [width * cell_size + padding for width, _ in sizes]
    width = 260 + sum(column_widths)
    height = padding + len(exposed) * row_height
    canvas = checkerboard((width, height))
    draw = ImageDraw.Draw(canvas)
    y = padding
    for family in exposed:
        draw.text((12, y + 8), family["label"], fill=(235, 239, 242, 255))
        draw.text((12, y + 26), family["id"], fill=(158, 178, 190, 255))
        x = 260
        for size, column_width in zip(sizes, column_widths):
            draw.text((x, y + 4), f"{size[0]}x{size[1]}", fill=(255, 213, 112, 255))
            preview = render_rectangle(
                source,
                family["outerBlock"],
                family["baseFillCell"],
                size,
                cell_size,
            )
            canvas.alpha_composite(preview, (x, y + label_height))
            x += column_width
        y += row_height
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PREVIEW_PATH, optimize=False, compress_level=9)


def main() -> None:
    verify_complete_summer_map()
    lock = read_json(LOCK_PATH)
    contract = read_json(CONTRACT_PATH)
    source_path = ROOT / contract["source"]
    locked = next(
        entry for entry in lock["lockedFiles"] if entry["projectPath"] == contract["source"]
    )
    if not source_path.is_file():
        raise FileNotFoundError(f"locked LPC source missing: {source_path}")
    actual_hash = sha256(source_path)
    if actual_hash != locked["sha256"]:
        raise ValueError(
            f"LPC source hash mismatch for {source_path}: {actual_hash} != {locked['sha256']}"
        )
    source = Image.open(source_path).convert("RGBA")
    expected_size = (locked["width"], locked["height"])
    if source.size != expected_size:
        raise ValueError(f"LPC source size {source.size} != locked size {expected_size}")

    grid = contract["grid"]
    cell_size = contract["cellSize"]
    objects = []
    for family in contract["families"]:
        validate_block(family["outerBlock"], (3, 3), grid, f"{family['id']} outerBlock")
        validate_block(
            family["innerCornerBlock"],
            (2, 2),
            grid,
            f"{family['id']} innerCornerBlock",
        )
        if not family.get("exposeAsStamp"):
            continue
        outer_x, outer_y, _, _ = family["outerBlock"]
        minimum = [max(3, value) for value in family["minimumSize"]]
        objects.append(
            {
                "id": family["id"],
                "label": family["label"],
                "category": "terrain/ponds",
                "objectType": "terrain_stamp",
                "rect": [
                    outer_x * cell_size,
                    outer_y * cell_size,
                    3 * cell_size,
                    3 * cell_size,
                ],
                "visualFootprint": minimum,
                "collisionFootprint": minimum,
                "origin": [minimum[0] // 2, minimum[1] - 1],
                "occludesPlayer": False,
                "fadeWhenPlayerBehind": False,
                "expandable": {
                    "cellSize": cell_size,
                    "outerBlock": family["outerBlock"],
                    "innerCornerBlock": family["innerCornerBlock"],
                    "baseFillCell": family["baseFillCell"],
                    "minimumSize": minimum,
                    "supportsFreeform": bool(family.get("supportsFreeform")),
                },
            }
        )

    manifest = {
        "schema": "havenwild.stamp_manifest.v0_2",
        "manifestId": "lpc_expandable_ponds_32",
        "source": contract["source"],
        "sourceLock": str(LOCK_PATH.relative_to(ROOT)).replace("\\", "/"),
        "output": contract["source"],
        "tileSize": cell_size,
        "license": contract["license"],
        "attribution": contract["attribution"],
        "notes": [
            "LPC pond families preserve their authored 3x3 outer block and 2x2 inner-corner block.",
            "Runtime and editor rectangle expansion repeats center and cardinal edges without scaling pixels.",
            "Inner-corner cells are cataloged now for the later freeform/blob footprint resolver.",
            "Placed instances persist their resized visual/collision footprint in world.tworld.",
        ],
        "objects": objects,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    build_preview(source, contract)
    print(f"Promoted {len(objects)} expandable LPC pond stamp families")
    print(f"Wrote {OUTPUT_MANIFEST.relative_to(ROOT)}")
    print(f"Wrote {PREVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
