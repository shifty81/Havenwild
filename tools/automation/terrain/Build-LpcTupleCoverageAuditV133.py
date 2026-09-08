#!/usr/bin/env python3
"""Build a visual terrain-v7 tuple coverage audit board."""
from __future__ import annotations

import json
from collections import Counter
from itertools import combinations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png"
OUT_JSON = ROOT / "content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json"
OUT_MD = ROOT / "docs/assets/LPC_TUPLE_COVERAGE_AUDIT_PASS133.md"
OUT_PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_tuple_coverage_pass133.png"

TILE = 32
PAD = 8
LABEL_W = 210
CELL_STEP = 38
ROW_H = 54

MATERIALS = [
    "Grass",
    "Grass_Dark",
    "Dirt_Brown",
    "Sand",
    "Stone_Tan",
    "Dirt_Tan",
    "Dirt_Roots",
    "Mudstone_Brown",
    "Soil",
    "Mud_Brown",
    "Water_Shallows_Sand",
    "Water_Deep",
    "Water",
    "Water_Shallows_Dirt",
]

PRODUCTION_PAIRS = [
    ("Grass", "Sand"),
    ("Grass", "Dirt_Brown"),
    ("Sand", "Dirt_Brown"),
    ("Sand", "Water"),
    ("Sand", "Water_Deep"),
    ("Sand", "Water_Shallows_Sand"),
    ("Grass", "Water"),
    ("Grass", "Water_Deep"),
    ("Dirt_Brown", "Water"),
    ("Dirt_Brown", "Water_Deep"),
    ("Water", "Water_Deep"),
    ("Water", "Water_Shallows_Sand"),
    ("Water_Deep", "Water_Shallows_Sand"),
    ("Dirt_Brown", "Water_Shallows_Dirt"),
    ("Water", "Water_Shallows_Dirt"),
    ("Dirt_Brown", "Dirt_Tan"),
    ("Grass", "Dirt_Tan"),
    ("Sand", "Dirt_Tan"),
    ("Dirt_Brown", "Dirt_Roots"),
    ("Grass", "Dirt_Roots"),
    ("Sand", "Dirt_Roots"),
    ("Grass", "Stone_Tan"),
    ("Sand", "Stone_Tan"),
    ("Dirt_Brown", "Stone_Tan"),
    ("Grass", "Mudstone_Brown"),
    ("Water", "Mudstone_Brown"),
]


def all_audit_pairs() -> list[tuple[str, str]]:
    pairs = list(PRODUCTION_PAIRS)
    seen = set(pairs)
    for pair in combinations(MATERIALS, 2):
        if pair not in seen:
            pairs.append(pair)
            seen.add(pair)
    return pairs

WATER_MATERIALS = {
    "Water",
    "Water_Deep",
    "Water_Shallows_Sand",
    "Water_Shallows_Dirt",
}

DIRT_OR_STONE_SHORE = {
    "Dirt_Brown",
    "Dirt_Roots",
    "Dirt_Tan",
    "Mud_Brown",
    "Mudstone_Brown",
    "Stone_Tan",
    "Rock_Gray",
    "Rock_Dark",
}


def corner_key(corners: tuple[str, str, str, str]) -> str:
    return "|".join(corners)


def binary_corner_patterns(a: str, b: str) -> list[tuple[str, str, str, str]]:
    patterns = []
    for mask in range(16):
        corners = tuple(b if mask & (1 << bit) else a for bit in range(4))
        patterns.append(corners)  # top-left, top-right, bottom-left, bottom-right
    return patterns


def fallback_material(corners: tuple[str, str, str, str]) -> str:
    if "Water_Shallows_Sand" in corners:
        return "Water_Shallows_Sand"
    if "Water_Shallows_Dirt" in corners:
        return "Water_Shallows_Dirt"
    has_water = any(corner in WATER_MATERIALS for corner in corners)
    has_land = any(corner not in WATER_MATERIALS for corner in corners)
    if has_water and has_land:
        if "Sand" in corners:
            return "Water_Shallows_Sand"
        if any(corner in DIRT_OR_STONE_SHORE for corner in corners):
            return "Water_Shallows_Dirt"
        return "Water"

    counts = Counter(corners)
    priority = {
        "Water_Shallows_Sand": 100,
        "Water_Shallows_Dirt": 100,
        "Water": 90,
        "Water_Deep": 80,
        "Sand": 70,
        "Grass": 60,
        "Grass_Dark": 60,
        "Dirt_Brown": 50,
        "Dirt_Roots": 50,
        "Dirt_Tan": 50,
        "Stone_Tan": 40,
        "Rock_Gray": 40,
        "Rock_Dark": 40,
        "Mudstone_Brown": 40,
        "Soil": 30,
        "Mud_Brown": 30,
    }
    return max(counts, key=lambda material: (counts[material], priority.get(material, 0)))


def crop_entry(atlas: Image.Image, entry: dict) -> Image.Image:
    x, y, w, h = entry["rect"]
    return atlas.crop((x, y, x + w, y + h))


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    atlas = Image.open(ATLAS).convert("RGBA")

    lookup: dict[str, dict] = {}
    pure_lookup: dict[str, dict] = {}
    for entry in manifest["entries"]:
        corners = entry["corners"]
        key = corner_key(
            (
                corners["topLeft"],
                corners["topRight"],
                corners["bottomLeft"],
                corners["bottomRight"],
            )
        )
        lookup.setdefault(key, entry)
        values = key.split("|")
        if len(set(values)) == 1:
            pure_lookup.setdefault(values[0], entry)

    rows = []
    counts = Counter()
    pair_counts = {}
    audit_pairs = all_audit_pairs()
    for pair in audit_pairs:
        pair_key = f"{pair[0]}__{pair[1]}"
        pair_counter = Counter()
        pattern_records = []
        for corners in binary_corner_patterns(*pair):
            key = corner_key(corners)
            if key in lookup:
                status = "exact"
                entry = lookup[key]
                fallback = None
            else:
                fallback = fallback_material(corners)
                if fallback in pure_lookup:
                    status = "fallback"
                    entry = pure_lookup[fallback]
                else:
                    status = "missing"
                    entry = None
            counts[status] += 1
            pair_counter[status] += 1
            pattern_records.append(
                {
                    "corners": {
                        "topLeft": corners[0],
                        "topRight": corners[1],
                        "bottomLeft": corners[2],
                        "bottomRight": corners[3],
                    },
                    "status": status,
                    "fallbackMaterial": fallback,
                    "tileId": entry.get("tileId") if entry else None,
                }
            )
        pair_counts[pair_key] = dict(pair_counter)
        rows.append({"pair": list(pair), "patterns": pattern_records})

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "id": "lpc_tuple_coverage_audit_v0_1",
        "kind": "terrain_tuple_coverage_audit",
        "sourceManifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "sourceAtlas": str(ATLAS.relative_to(ROOT)).replace("\\", "/"),
        "materials": MATERIALS,
        "productionPairs": [list(pair) for pair in PRODUCTION_PAIRS],
        "auditPairs": [list(pair) for pair in audit_pairs],
        "totals": dict(counts),
        "pairTotals": pair_counts,
        "rows": rows,
        "policy": {
            "exact": "Authored terrain-v7 tuple exists.",
            "fallback": "Known materials use terrain-v7 pure fallback and suppress legacy draw.",
            "missing": "No exact tuple or pure fallback exists; must be authored before production.",
        },
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    font = load_font(12)
    small = load_font(10)
    width = LABEL_W + 16 * CELL_STEP + PAD * 2
    height = 72 + len(rows) * ROW_H + 70
    board = Image.new("RGBA", (width, height), (20, 24, 27, 255))
    draw = ImageDraw.Draw(board)
    draw.text((PAD, PAD), "Havenwild LPC Terrain Tuple Coverage - Pass 133", fill=(238, 241, 231), font=font)
    draw.text(
        (PAD, 28),
        f"patterns: {sum(counts.values())}  exact: {counts['exact']}  fallback: {counts['fallback']}  missing: {counts['missing']}",
        fill=(172, 190, 181),
        font=small,
    )
    draw.text((PAD, 48), "green border=exact  amber=fallback  magenta=missing", fill=(198, 166, 88), font=small)

    colors = {
        "exact": (84, 178, 105, 255),
        "fallback": (218, 163, 63, 255),
        "missing": (233, 72, 158, 255),
    }
    y = 72
    for row in rows:
        pair = row["pair"]
        label = f"{pair[0]} <-> {pair[1]}"
        draw.text((PAD, y + 10), label, fill=(228, 229, 213), font=small)
        for i, pattern in enumerate(row["patterns"]):
            x = LABEL_W + i * CELL_STEP
            status = pattern["status"]
            if pattern["tileId"] is not None:
                entry = next(e for e in manifest["entries"] if e["tileId"] == pattern["tileId"])
                tile = crop_entry(atlas, entry)
                board.alpha_composite(tile, (x, y))
            else:
                draw.rectangle((x, y, x + TILE, y + TILE), fill=(64, 24, 70, 255))
            draw.rectangle((x, y, x + TILE - 1, y + TILE - 1), outline=colors[status], width=2)
        y += ROW_H

    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    board.save(OUT_PREVIEW)

    top_fallback = sorted(
        ((pair, totals.get("fallback", 0)) for pair, totals in pair_counts.items()),
        key=lambda item: item[1],
        reverse=True,
    )[:12]
    md_lines = [
        "# LPC Tuple Coverage Audit - Pass 133",
        "",
        "This audit enumerates 16 binary 4-corner tuple patterns for every current terrain material pair.",
        "",
        f"- Exact tuples: {counts['exact']}",
        f"- Terrain-v7 fallback tuples: {counts['fallback']}",
        f"- Missing tuples: {counts['missing']}",
        "",
        "Fallback is acceptable as a temporary safety net because it keeps rendering inside terrain-v7 and suppresses stale legacy atlas draw. Production polish still means converting high-frequency fallback pairs into exact authored tuple art.",
        "",
        "## Highest Fallback Pairs",
        "",
        "| Pair | Fallback Patterns |",
        "|---|---:|",
    ]
    for pair, total in top_fallback:
        md_lines.append(f"| `{pair}` | {total} |")
    md_lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- JSON: `{OUT_JSON.relative_to(ROOT)}`",
            f"- Preview: `{OUT_PREVIEW.relative_to(ROOT)}`",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(
        "Wrote LPC tuple coverage audit: "
        f"{counts['exact']} exact, {counts['fallback']} fallback, {counts['missing']} missing"
    )
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_PREVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
