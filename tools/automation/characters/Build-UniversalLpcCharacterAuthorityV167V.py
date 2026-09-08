#!/usr/bin/env python3
"""Build Havenwild's local Universal LPC character/NPC authority.

This scans the mounted generator source, selects the preferred commercial license
for each credited source family, indexes source-native animation paths, and writes
local generated artifacts. It never copies the 88k+ spritesheet files into content.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/source/licensed/universal_lpc_generator"
OUTPUT = ROOT / "WORKSPACE/generated/universal_lpc_character_authority_v167v.json"
CREDITS_OUTPUT = ROOT / "WORKSPACE/generated/universal_lpc_selected_credits_v167v.csv"


def choose_license(raw: str) -> tuple[str | None, str]:
    licenses = [item.strip() for item in raw.split(",") if item.strip()]
    if "CC0" in licenses:
        return "CC0", "preferred"
    for item in licenses:
        if item.startswith("OGA-BY") or item == "OGA-BY-3.0":
            return item, "preferred"
    for item in licenses:
        if (item.startswith("CC-BY ") or item.startswith("CC-BY-") or item == "CC-BY") and "SA" not in item:
            return item, "preferred"
    for item in licenses:
        if item.startswith("CC-BY-SA"):
            return item, "conditional"
    return None, "rejected"


def tags_for(path: str) -> list[str]:
    lowered = path.lower()
    tags = {path.split("/")[0]}
    for tag in (
        "male", "female", "teen", "child", "elderly", "pregnant", "muscular",
        "zombie", "skeleton", "lizard", "wings", "tail", "wheelchair", "prosthesis",
        "hair", "beards", "eyes", "hat", "torso", "legs", "feet", "weapon", "shield", "tools",
    ):
        if tag in lowered:
            tags.add(tag)
    return sorted(tags)


def main() -> int:
    if not SOURCE.is_dir():
        raise SystemExit("Universal LPC source is not mounted; run tools/automation/characters/Ensure-UniversalLpcGenerator.py")
    credits_path = SOURCE / "CREDITS.csv"
    with credits_path.open(encoding="utf-8", newline="") as stream:
        credits = list(csv.DictReader(stream))

    records = []
    tier_counts = Counter()
    category_counts = Counter()
    selected_rows = []
    for row in credits:
        selected, tier = choose_license(row["licenses"])
        category = row["filename"].split("/")[0]
        tier_counts[tier] += 1
        category_counts[category] += 1
        records.append({
            "source": row["filename"],
            "category": category,
            "tags": tags_for(row["filename"]),
            "authors": [item.strip() for item in row["authors"].split(",") if item.strip()],
            "licenses": [item.strip() for item in row["licenses"].split(",") if item.strip()],
            "selected_license": selected,
            "license_tier": tier,
            "urls": [item.strip() for item in row["urls"].split(",") if item.strip()],
        })
        if selected is not None:
            selected_rows.append({
                "filename": row["filename"],
                "authors": row["authors"],
                "selected_license": selected,
                "urls": row["urls"],
            })

    animation_paths = defaultdict(int)
    sprites = SOURCE / "spritesheets"
    for path in sprites.rglob("*.png"):
        relative = path.relative_to(sprites).as_posix()
        animation_paths[path.stem] += 1

    authority = {
        "schema": "havenwild.universal_lpc_character_authority.v167v",
        "source_commit": "0f898bb675a1abe16ce430e82e3bf9daed278690",
        "sex_values": ["Male", "Female"],
        "age_groups": ["Child", "Teen", "Adult", "Elder"],
        "credit_record_count": len(records),
        "license_tier_counts": dict(tier_counts),
        "category_counts": dict(category_counts),
        "animation_filename_counts": dict(sorted(animation_paths.items())),
        "records": records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(authority, indent=2) + "\n", encoding="utf-8")
    with CREDITS_OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["filename", "authors", "selected_license", "urls"])
        writer.writeheader()
        writer.writerows(selected_rows)
    print(f"Wrote {OUTPUT} with {len(records):,} credited source records")
    print(f"Wrote {CREDITS_OUTPUT} with {len(selected_rows):,} commercially selectable records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
