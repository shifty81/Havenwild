#!/usr/bin/env python3
"""Build a prioritized plan for promoting fallback-heavy LPC tuples to exact art."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
AUDIT_JSON = ROOT / "content/assets/lpc/lpc_tuple_coverage_audit_v0_1.json"
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png"
OUT_JSON = ROOT / "content/assets/lpc/lpc_tuple_promotion_plan_v0_1.json"
OUT_MD = ROOT / "docs/assets/LPC_TUPLE_PROMOTION_PLAN_PASS134.md"
OUT_PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_tuple_promotion_plan_pass134.png"

TILE = 32
PAD = 8
LABEL_W = 260
CELL_STEP = 38
ROW_H = 58
MAX_PREVIEW_ROWS = 36

WATER_MATERIALS = {
    "Water",
    "Water_Deep",
    "Water_Shallows_Sand",
    "Water_Shallows_Dirt",
}

SHORE_MATERIALS = {
    "Sand",
    "Water_Shallows_Sand",
    "Water_Shallows_Dirt",
    "Dirt_Brown",
    "Dirt_Tan",
    "Dirt_Roots",
    "Mud_Brown",
    "Mudstone_Brown",
    "Stone_Tan",
}


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def crop_entry(atlas: Image.Image, entry: dict) -> Image.Image:
    x, y, w, h = entry["rect"]
    return atlas.crop((x, y, x + w, y + h))


def classify_pair(pair: list[str], production_pairs: set[tuple[str, str]]) -> str:
    a, b = pair
    pair_tuple = (a, b)
    reversed_pair = (b, a)
    if pair_tuple in production_pairs or reversed_pair in production_pairs:
        if a in WATER_MATERIALS or b in WATER_MATERIALS:
            return "production_water_shore"
        return "production_land_edge"
    if a in WATER_MATERIALS and b in WATER_MATERIALS:
        return "water_depth"
    if a in WATER_MATERIALS or b in WATER_MATERIALS:
        if a in SHORE_MATERIALS or b in SHORE_MATERIALS:
            return "advanced_water_shore"
        return "advanced_water_land"
    return "advanced_land_edge"


def priority_for(pair: list[str], fallback_count: int, exact_count: int, category: str) -> int:
    score = fallback_count * 10
    if category == "production_water_shore":
        score += 1000
    elif category == "water_depth":
        score += 850
    elif category == "production_land_edge":
        score += 700
    elif category == "advanced_water_shore":
        score += 500
    elif category == "advanced_water_land":
        score += 300
    else:
        score += 100
    if exact_count <= 2:
        score += 80
    if "Water_Deep" in pair:
        score += 50
    if "Sand" in pair:
        score += 40
    return score


def main() -> int:
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    atlas = Image.open(ATLAS).convert("RGBA")
    entries_by_id = {entry["tileId"]: entry for entry in manifest["entries"]}
    production_pairs = {tuple(pair) for pair in audit["productionPairs"]}

    plan_rows = []
    for row in audit["rows"]:
        pair = row["pair"]
        pair_key = f"{pair[0]}__{pair[1]}"
        totals = audit["pairTotals"].get(pair_key, {})
        fallback_count = int(totals.get("fallback", 0))
        exact_count = int(totals.get("exact", 0))
        if fallback_count <= 0:
            continue
        category = classify_pair(pair, production_pairs)
        fallback_patterns = [
            pattern
            for pattern in row["patterns"]
            if pattern.get("status") == "fallback"
        ]
        plan_rows.append(
            {
                "pair": pair,
                "category": category,
                "priority": priority_for(pair, fallback_count, exact_count, category),
                "exactPatterns": exact_count,
                "fallbackPatterns": fallback_count,
                "fallbackMaterials": sorted(
                    {
                        pattern.get("fallbackMaterial")
                        for pattern in fallback_patterns
                        if pattern.get("fallbackMaterial")
                    }
                ),
                "patterns": fallback_patterns,
            }
        )

    plan_rows.sort(key=lambda row: (row["priority"], row["fallbackPatterns"]), reverse=True)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_PREVIEW.parent.mkdir(parents=True, exist_ok=True)

    category_totals: dict[str, int] = {}
    for row in plan_rows:
        category_totals[row["category"]] = category_totals.get(row["category"], 0) + row["fallbackPatterns"]

    report = {
        "id": "lpc_tuple_promotion_plan_v0_1",
        "kind": "terrain_tuple_promotion_plan",
        "sourceAudit": str(AUDIT_JSON.relative_to(ROOT)).replace("\\", "/"),
        "sourceManifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "policy": {
            "goal": "Convert fallback-heavy terrain-v7 tuples into exact authored tuple art.",
            "priorityOrder": [
                "production_water_shore",
                "water_depth",
                "production_land_edge",
                "advanced_water_shore",
                "advanced_water_land",
                "advanced_land_edge",
            ],
            "fallbackSafety": "Fallback rows are render-safe but visually lower quality than exact tuple art.",
        },
        "categoryFallbackTotals": category_totals,
        "completedPromotionCategories": [
            category
            for category in ("production_water_shore", "water_depth")
            if category_totals.get(category, 0) == 0
        ],
        "rows": plan_rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    font = load_font(12)
    small = load_font(10)
    visible_rows = plan_rows[:MAX_PREVIEW_ROWS]
    width = LABEL_W + 16 * CELL_STEP + PAD * 2
    height = 76 + len(visible_rows) * ROW_H + 52
    board = Image.new("RGBA", (width, height), (20, 24, 27, 255))
    draw = ImageDraw.Draw(board)
    draw.text((PAD, PAD), "Havenwild LPC Tuple Promotion Plan - Pass 134", fill=(238, 241, 231), font=font)
    draw.text(
        (PAD, 28),
        f"fallback rows: {len(plan_rows)}  fallback patterns: {sum(row['fallbackPatterns'] for row in plan_rows)}",
        fill=(172, 190, 181),
        font=small,
    )
    draw.text((PAD, 48), "Rows are sorted by production/water priority, then fallback count.", fill=(198, 166, 88), font=small)

    y = 76
    for row in visible_rows:
        pair = row["pair"]
        label = f"{pair[0]} <-> {pair[1]}"
        draw.text((PAD, y + 4), label, fill=(228, 229, 213), font=small)
        draw.text(
            (PAD, y + 20),
            f"{row['category']}  exact:{row['exactPatterns']} fallback:{row['fallbackPatterns']}",
            fill=(172, 190, 181),
            font=small,
        )
        for index, pattern in enumerate(row["patterns"][:16]):
            x = LABEL_W + index * CELL_STEP
            tile_id = pattern.get("tileId")
            entry = entries_by_id.get(tile_id) if tile_id else None
            if entry:
                board.alpha_composite(crop_entry(atlas, entry), (x, y))
            else:
                draw.rectangle((x, y, x + TILE, y + TILE), fill=(64, 24, 70, 255))
            draw.rectangle((x, y, x + TILE - 1, y + TILE - 1), outline=(218, 163, 63, 255), width=2)
        y += ROW_H
    board.save(OUT_PREVIEW)

    md_lines = [
        "# LPC Tuple Promotion Plan - Pass 134",
        "",
        "This plan ranks terrain-v7 fallback tuples that should be converted into exact authored tuple art.",
        "",
        "| Category | Fallback Patterns |",
        "|---|---:|",
    ]
    for category, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
        md_lines.append(f"| `{category}` | {total} |")
    md_lines.extend(
        [
            "",
            "## Top Promotion Rows",
            "",
            "| Priority | Pair | Category | Exact | Fallback | Fallback Materials |",
            "|---:|---|---|---:|---:|---|",
        ]
    )
    for row in plan_rows[:24]:
        md_lines.append(
            "| {priority} | `{pair}` | `{category}` | {exact} | {fallback} | `{fallback_materials}` |".format(
                priority=row["priority"],
                pair="__".join(row["pair"]),
                category=row["category"],
                exact=row["exactPatterns"],
                fallback=row["fallbackPatterns"],
                fallback_materials=", ".join(row["fallbackMaterials"]),
            )
        )
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
        "Wrote LPC tuple promotion plan: "
        f"{len(plan_rows)} fallback rows, {sum(row['fallbackPatterns'] for row in plan_rows)} fallback patterns"
    )
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_PREVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
