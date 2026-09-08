#!/usr/bin/env python3
"""Build the exhaustive coordinate-level map for LPC terrain_summer.png.

This pass does not remap active runtime atlases. It freezes a complete source
census so every authored cell has one primary role before further PCG,
seasonal, stamp, or runtime promotion work occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json"
LOCK_PATH = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"

OUTER_ROLES = (
    "outer_north_west",
    "outer_north",
    "outer_north_east",
    "outer_west",
    "center",
    "outer_east",
    "outer_south_west",
    "outer_south",
    "outer_south_east",
)
INNER_ROLES = {
    (0, 0): "inner_south_east",
    (1, 0): "inner_south_west",
    (0, 1): "inner_north_east",
    (1, 1): "inner_north_west",
}
CLASS_COLORS = {
    "RepeatableFill": (74, 171, 92, 220),
    "TerrainTransitionFamily": (235, 170, 55, 220),
    "ExpandableStampFamily": (65, 156, 214, 220),
    "HorizontalStrip": (171, 111, 219, 220),
    "VerticalStrip": (171, 111, 219, 220),
    "ObjectSprite": (219, 90, 100, 220),
    "Decoration": (219, 90, 100, 220),
    "unused_transparent": (78, 84, 92, 210),
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cells_for_rect(rect: Iterable[int]) -> list[tuple[int, int]]:
    x, y, width, height = [int(v) for v in rect]
    return [(column, row) for row in range(y, y + height) for column in range(x, x + width)]


def validate_cell(cell: tuple[int, int], grid: list[int], label: str) -> None:
    x, y = cell
    if x < 0 or y < 0 or x >= grid[0] or y >= grid[1]:
        raise ValueError(f"{label} cell {cell} lies outside grid {grid}")


def add_membership(
    memberships: dict[tuple[int, int], dict],
    cell: tuple[int, int],
    record: dict,
    grid: list[int],
) -> None:
    validate_cell(cell, grid, record["groupId"])
    if cell in memberships:
        previous = memberships[cell]["groupId"]
        raise ValueError(f"source cell {cell} is assigned to both {previous} and {record['groupId']}")
    memberships[cell] = record


def outer_role(index: int) -> str:
    return OUTER_ROLES[index]


def build_memberships(contract: dict) -> dict[tuple[int, int], dict]:
    grid = contract["grid"]
    memberships: dict[tuple[int, int], dict] = {}

    for family in contract["fillFamilies"]:
        for index, raw_cell in enumerate(family["cells"]):
            add_membership(
                memberships,
                tuple(raw_cell),
                {
                    "groupId": family["id"],
                    "groupLabel": family["label"],
                    "classification": family["classification"],
                    "role": f"variant_{index:02d}",
                    "runtimeStatus": family["runtimeStatus"],
                    "runtimeIds": family.get("runtimeIds", []),
                    "pcgUse": family.get("pcgUse", []),
                },
                grid,
            )

    for family in contract["transitionFamilies"]:
        outer = family["outerBlock"]
        for index, cell in enumerate(cells_for_rect(outer)):
            add_membership(
                memberships,
                cell,
                {
                    "groupId": family["id"],
                    "groupLabel": family["label"],
                    "classification": family["classification"],
                    "role": outer_role(index),
                    "component": "outerBlock",
                    "owner": family["owner"],
                    "neighbor": family["neighbor"],
                    "runtimeStatus": family["runtimeStatus"],
                    "runtimeIds": family.get("runtimeIds", []),
                    "stampIds": family.get("stampIds", []),
                    "pcgUse": family.get("pcgUse", []),
                },
                grid,
            )
        inner = family.get("innerCornerBlock")
        if inner:
            x, y, width, height = inner
            if [width, height] != [2, 2]:
                raise ValueError(f"{family['id']} innerCornerBlock must be 2x2")
            for dy in range(2):
                for dx in range(2):
                    add_membership(
                        memberships,
                        (x + dx, y + dy),
                        {
                            "groupId": family["id"],
                            "groupLabel": family["label"],
                            "classification": family["classification"],
                            "role": INNER_ROLES[(dx, dy)],
                            "component": "innerCornerBlock",
                            "owner": family["owner"],
                            "neighbor": family["neighbor"],
                            "runtimeStatus": family["runtimeStatus"],
                            "runtimeIds": family.get("runtimeIds", []),
                            "stampIds": family.get("stampIds", []),
                            "pcgUse": family.get("pcgUse", []),
                        },
                        grid,
                    )

    for strip in contract["modularStrips"]:
        for index, cell in enumerate(cells_for_rect(strip["sourceRect"])):
            add_membership(
                memberships,
                cell,
                {
                    "groupId": strip["id"],
                    "groupLabel": strip["label"],
                    "classification": strip["classification"],
                    "role": f"{strip['orientation']}_variant_{index:02d}",
                    "runtimeStatus": strip["runtimeStatus"],
                    "pcgUse": strip.get("pcgUse", []),
                },
                grid,
            )

    for decoration in contract["decorations"]:
        add_membership(
            memberships,
            tuple(decoration["cell"]),
            {
                "groupId": decoration["id"],
                "groupLabel": decoration["label"],
                "classification": decoration["classification"],
                "role": "sprite",
                "runtimeStatus": decoration["runtimeStatus"],
                "stampIds": [decoration["stampId"]],
                "pcgUse": decoration.get("pcgUse", []),
            },
            grid,
        )
    return memberships


def alpha_occupancy(tile: Image.Image) -> tuple[bool, int, list[int] | None]:
    alpha = tile.getchannel("A")
    bbox = alpha.getbbox()
    histogram = alpha.histogram()
    count = tile.width * tile.height - histogram[0]
    return bbox is not None, count, list(bbox) if bbox else None


def locked_source(contract: dict) -> Path:
    lock = read_json(LOCK_PATH)
    source = ROOT / contract["source"]
    locked = next(
        item for item in lock["lockedFiles"] if item["projectPath"] == contract["source"]
    )
    if not source.is_file():
        raise FileNotFoundError(f"locked LPC source missing: {source}")
    with Image.open(source) as image:
        if image.size != (locked["width"], locked["height"]):
            raise ValueError(f"locked LPC source dimensions changed: {image.size}")
    actual_hash = sha256(source)
    if actual_hash != locked["sha256"]:
        raise ValueError(f"locked LPC source hash changed: {actual_hash}")
    return source


def validate_seasonal_parity(contract: dict, summer_nonempty: set[tuple[int, int]]) -> list[dict]:
    results = []
    tile_size = contract["cellSize"]
    grid = contract["grid"]
    for sibling in contract.get("seasonalLayoutParity", []):
        path = ROOT / sibling["source"]
        if not path.is_file():
            raise FileNotFoundError(f"seasonal sibling missing: {path}")
        image = Image.open(path).convert("RGBA")
        expected_size = (grid[0] * tile_size, grid[1] * tile_size)
        if image.size != expected_size:
            raise ValueError(f"{sibling['season']} dimensions {image.size} != {expected_size}")
        nonempty = set()
        for row in range(grid[1]):
            for column in range(grid[0]):
                tile = image.crop(
                    (
                        column * tile_size,
                        row * tile_size,
                        (column + 1) * tile_size,
                        (row + 1) * tile_size,
                    )
                )
                if tile.getchannel("A").getbbox():
                    nonempty.add((column, row))
        if len(nonempty) != sibling["expectedNonTransparentCells"]:
            raise ValueError(
                f"{sibling['season']} has {len(nonempty)} non-transparent cells, "
                f"expected {sibling['expectedNonTransparentCells']}"
            )
        extras = sorted(nonempty - summer_nonempty)
        missing = sorted(summer_nonempty - nonempty)
        expected_extras = sorted(tuple(cell) for cell in sibling.get("additionalCells", []))
        if extras != expected_extras:
            raise ValueError(
                f"{sibling['season']} additional cells {extras} != declared {expected_extras}"
            )
        if missing:
            raise ValueError(f"{sibling['season']} is missing summer cells: {missing}")
        results.append(
            {
                "season": sibling["season"],
                "source": sibling["source"],
                "nonTransparentCells": len(nonempty),
                "additionalCells": [list(cell) for cell in extras],
                "layoutCompatible": True,
            }
        )
    return results


def build_payload(contract: dict) -> tuple[dict, Image.Image]:
    source_path = locked_source(contract)
    source = Image.open(source_path).convert("RGBA")
    memberships = build_memberships(contract)
    grid = contract["grid"]
    tile_size = contract["cellSize"]
    expected_size = (grid[0] * tile_size, grid[1] * tile_size)
    if source.size != expected_size:
        raise ValueError(f"source size {source.size} != contract size {expected_size}")

    cells = []
    summer_nonempty = set()
    uncovered_nonempty = []
    mapped_nonempty = 0
    structural_transparent = 0
    unused_transparent = 0
    for row in range(grid[1]):
        for column in range(grid[0]):
            tile = source.crop(
                (
                    column * tile_size,
                    row * tile_size,
                    (column + 1) * tile_size,
                    (row + 1) * tile_size,
                )
            )
            nonempty, alpha_pixels, bbox = alpha_occupancy(tile)
            if nonempty:
                summer_nonempty.add((column, row))
            mapping = memberships.get((column, row))
            if nonempty and mapping is None:
                uncovered_nonempty.append((column, row))
            if mapping is not None:
                classification = mapping["classification"]
                role = mapping["role"]
                if nonempty:
                    mapped_nonempty += 1
                else:
                    structural_transparent += 1
            else:
                classification = "unused_transparent"
                role = "unused_transparent"
                unused_transparent += 1
            record = {
                "cell": [column, row],
                "pixelRect": [column * tile_size, row * tile_size, tile_size, tile_size],
                "nonTransparent": nonempty,
                "alphaPixelCount": alpha_pixels,
                "alphaBounds": bbox,
                "classification": classification,
                "role": role,
            }
            if mapping:
                record.update(mapping)
            cells.append(record)

    if uncovered_nonempty:
        raise ValueError(f"non-transparent cells lack primary mappings: {uncovered_nonempty}")
    if mapped_nonempty != len(summer_nonempty):
        raise ValueError(
            f"mapped non-transparent count {mapped_nonempty} != source count {len(summer_nonempty)}"
        )

    seasonal = validate_seasonal_parity(contract, summer_nonempty)
    summary = {
        "totalCells": grid[0] * grid[1],
        "nonTransparentCells": len(summer_nonempty),
        "mappedNonTransparentCells": mapped_nonempty,
        "transparentCells": grid[0] * grid[1] - len(summer_nonempty),
        "structuralTransparentCells": structural_transparent,
        "unusedTransparentCells": unused_transparent,
        "primaryGroups": len(
            contract["fillFamilies"]
            + contract["transitionFamilies"]
            + contract["modularStrips"]
            + contract["decorations"]
        ),
        "allNonTransparentCellsMapped": True,
        "noPrimaryGroupOverlap": True,
    }
    payload = {
        "schema": "havenwild.lpc_terrain_summer_complete_map.generated.v0_1",
        "sourceContract": str(CONTRACT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "source": contract["source"],
        "sourceSha256": sha256(source_path),
        "season": contract["season"],
        "cellSize": tile_size,
        "grid": grid,
        "license": contract["license"],
        "attribution": contract["attribution"],
        "summary": summary,
        "seasonalLayoutParity": seasonal,
        "cells": cells,
    }
    return payload, source


def short_label(group_id: str) -> str:
    pieces = [piece for piece in group_id.replace("summer_", "").split("_") if piece]
    return "".join(piece[0].upper() for piece in pieces[:4])[:5] or "MAP"


def render_preview(payload: dict, source: Image.Image, output_path: Path) -> None:
    grid = payload["grid"]
    tile_size = payload["cellSize"]
    scale = 2
    cell_px = tile_size * scale
    label_height = 18
    legend_width = 380
    canvas_width = grid[0] * cell_px + legend_width
    canvas_height = grid[1] * (cell_px + label_height)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (23, 28, 32, 255))
    draw = ImageDraw.Draw(canvas)
    try:
        tiny = ImageFont.truetype("DejaVuSansMono.ttf", 10)
        body = ImageFont.truetype("DejaVuSansMono.ttf", 14)
        title = ImageFont.truetype("DejaVuSansMono-Bold.ttf", 18)
    except OSError:
        tiny = body = title = None

    for record in payload["cells"]:
        column, row = record["cell"]
        x = column * cell_px
        y = row * (cell_px + label_height)
        tile = source.crop(
            (
                column * tile_size,
                row * tile_size,
                (column + 1) * tile_size,
                (row + 1) * tile_size,
            )
        ).resize((cell_px, cell_px), Image.Resampling.NEAREST)
        canvas.alpha_composite(tile, (x, y))
        color = CLASS_COLORS.get(record["classification"], (115, 125, 135, 220))
        draw.rectangle((x, y, x + cell_px - 1, y + cell_px - 1), outline=color, width=2)
        draw.rectangle(
            (x, y + cell_px, x + cell_px - 1, y + cell_px + label_height - 1),
            fill=(4, 7, 10, 235),
        )
        group_id = record.get("groupId", "unused")
        draw.text(
            (x + 2, y + cell_px + 2),
            f"{column},{row} {short_label(group_id)}",
            fill=(236, 239, 241, 255),
            font=tiny,
        )

    legend_x = grid[0] * cell_px + 18
    draw.text((legend_x, 18), "LPC Summer Complete Map", fill=(255, 222, 120, 255), font=title)
    summary = payload["summary"]
    lines = [
        f"Cells: {summary['totalCells']}",
        f"Non-transparent: {summary['nonTransparentCells']}",
        f"Mapped non-transparent: {summary['mappedNonTransparentCells']}",
        f"Structural transparent: {summary['structuralTransparentCells']}",
        f"Unused transparent: {summary['unusedTransparentCells']}",
        f"Primary groups: {summary['primaryGroups']}",
        "",
        "Classification colors:",
    ]
    y = 52
    for line in lines:
        draw.text((legend_x, y), line, fill=(220, 226, 230, 255), font=body)
        y += 20
    for classification, color in CLASS_COLORS.items():
        draw.rectangle((legend_x, y + 2, legend_x + 14, y + 16), fill=color)
        draw.text((legend_x + 22, y), classification, fill=(220, 226, 230, 255), font=body)
        y += 22
    y += 12
    draw.text((legend_x, y), "Runtime status", fill=(255, 222, 120, 255), font=title)
    y += 28
    status_counts: dict[str, int] = {}
    seen_groups = set()
    for record in payload["cells"]:
        group = record.get("groupId")
        if not group or group in seen_groups:
            continue
        seen_groups.add(group)
        status = record.get("runtimeStatus", "n/a")
        status_counts[status] = status_counts.get(status, 0) + 1
    for status, count in sorted(status_counts.items()):
        draw.text((legend_x, y), f"{status}: {count}", fill=(220, 226, 230, 255), font=body)
        y += 20
    y += 12
    draw.text((legend_x, y), "Season layout parity", fill=(255, 222, 120, 255), font=title)
    y += 28
    for season in payload["seasonalLayoutParity"]:
        draw.text(
            (legend_x, y),
            f"{season['season']}: {season['nonTransparentCells']} cells",
            fill=(220, 226, 230, 255),
            font=body,
        )
        y += 20
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, optimize=False, compress_level=9)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated files are current")
    args = parser.parse_args()

    contract = read_json(CONTRACT_PATH)
    payload, source = build_payload(contract)
    output_path = ROOT / contract["generatedOutputs"]["cellLedger"]
    preview_path = ROOT / contract["generatedOutputs"]["preview"]

    if args.check:
        if not output_path.is_file():
            raise FileNotFoundError(f"generated ledger missing: {output_path}")
        existing = read_json(output_path)
        if existing != payload:
            raise ValueError(f"generated ledger is stale: {output_path}")
        if not preview_path.is_file():
            raise FileNotFoundError(f"generated preview missing: {preview_path}")
        print(
            "LPC summer complete map valid: "
            f"{payload['summary']['mappedNonTransparentCells']}/"
            f"{payload['summary']['nonTransparentCells']} non-transparent cells mapped"
        )
        return 0

    write_json(output_path, payload)
    render_preview(payload, source, preview_path)
    print(
        "Mapped LPC terrain_summer.png completely: "
        f"{payload['summary']['mappedNonTransparentCells']} non-transparent cells, "
        f"{payload['summary']['structuralTransparentCells']} structural transparent cells, "
        f"{payload['summary']['unusedTransparentCells']} unused transparent cells"
    )
    print(f"Wrote {output_path.relative_to(ROOT)}")
    print(f"Wrote {preview_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
