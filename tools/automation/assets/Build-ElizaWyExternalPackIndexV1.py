#!/usr/bin/env python3
"""Rebuild the generated ElizaWy/LPC external-pack index from the pinned source mount.

Normal Havenwild source rollups intentionally omit the large generated
``elizawy_lpc_main.json`` inventory.  ``Ensure-LpcDependency.py`` restores the
pinned ElizaWy repository first; this script then reconstructs the historical
external-pack index deterministically enough for foundation validation and
source-record lookups without carrying a 40+ MB generated JSON file in every
source handoff.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - build doctor surfaces this
    raise SystemExit("Pillow is required. Install it with: python -m pip install pillow") from exc

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/source/licensed/lpc_revised"
LOCK = ROOT / "content/assets/intake/lpc_source_lock_v0_1.json"
OUTPUT = ROOT / "content/assets/intake/external_pack_indexes/elizawy_lpc_main.json"
IMAGE_EXTENSIONS = {".png", ".gif", ".jpg", ".jpeg", ".bmp", ".webp"}
GRID_CANDIDATES = (8, 16, 24, 32, 40, 48, 64, 72, 96, 128, 192)
EXCLUDED_PARTS = {".git", "__pycache__", "node_modules"}
EXPECTED_FILES = 64365
EXPECTED_IMAGES = 64325


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(relative: Path) -> list[str]:
    text = relative.as_posix().lower()
    groups: list[str] = []
    keywords = {
        "terrain": "terrain", "tile": "tile", "grass": "terrain.grass",
        "water": "terrain.water", "shore": "terrain.coast", "coast": "terrain.coast",
        "sand": "terrain.coast", "cliff": "terrain.cliff", "cave": "environment.cave",
        "dungeon": "environment.dungeon", "house": "structure.building",
        "building": "structure.building", "castle": "structure.building",
        "roof": "structure.roof", "wall": "structure.wall", "door": "structure.door",
        "fence": "structure.fence", "bridge": "structure.bridge", "tree": "foliage.tree",
        "bush": "foliage.bush", "flower": "foliage.flower", "farm": "farming",
        "crop": "farming.crop", "animal": "character.animal", "chicken": "character.animal",
        "pig": "character.animal", "horse": "character.animal", "llama": "character.animal",
        "cat": "character.animal", "character": "character", "player": "character",
        "npc": "character", "walk": "animation.walk", "idle": "animation.idle",
        "eat": "animation.eat", "shadow": "animation.shadow", "icon": "ui.icon",
        "inventory": "ui.icon", "ui": "ui", "effect": "effect", "weapon": "equipment",
        "tool": "equipment", "armor": "equipment.armor", "clothing": "equipment.clothing",
        "hair": "character.hair", "interior": "environment.interior",
        "inside": "environment.interior", "furniture": "environment.furniture",
    }
    for key, group in keywords.items():
        if key in text and group not in groups:
            groups.append(group)
    return groups or ["unclassified"]


def inspect_image(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        width, height = image.size
        frame_count = int(getattr(image, "n_frames", 1))
        return {
            "width": width,
            "height": height,
            "mode": image.mode,
            "frameCount": frame_count,
            "gridCandidates": [size for size in GRID_CANDIDATES if width % size == 0 and height % size == 0],
            "likelySpriteSheet": bool(frame_count > 1 or width >= 64 or height >= 64),
            "likelyMultiTile": bool(width > 32 or height > 32),
        }


def source_files() -> list[Path]:
    return sorted(
        p for p in SOURCE.rglob("*")
        if p.is_file() and not any(part in EXCLUDED_PARTS for part in p.relative_to(SOURCE).parts)
    )


def main() -> int:
    if not SOURCE.is_dir():
        print(f"ERROR: pinned ElizaWy/LPC source mount is missing: {SOURCE}", file=sys.stderr)
        return 2
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    paths = source_files()
    records: list[dict[str, Any]] = []
    counts = {"files": 0, "images": 0, "unreadableImages": 0}
    category_counts: dict[str, int] = {}
    for index, path in enumerate(paths, start=1):
        relative = path.relative_to(SOURCE)
        # Preserve the stable historical external-index path shape even though
        # the pinned git mount itself has no LPC-main wrapper directory.
        index_relative = Path("LPC-main") / relative
        counts["files"] += 1
        record: dict[str, Any] = {
            "relativePath": index_relative.as_posix(),
            "extension": path.suffix.lower(),
            "sizeBytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "promotionState": "cataloged_source_only",
        }
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            counts["images"] += 1
            classes = classify(index_relative)
            record["classes"] = classes
            for category in classes:
                category_counts[category] = category_counts.get(category, 0) + 1
            try:
                record.update(inspect_image(path))
            except Exception as error:
                counts["unreadableImages"] += 1
                record["imageError"] = str(error)
        records.append(record)
        if index % 5000 == 0:
            print(f"  indexed {index:,}/{len(paths):,} ElizaWy/LPC files", flush=True)

    if counts["files"] != EXPECTED_FILES or counts["images"] != EXPECTED_IMAGES:
        raise SystemExit(
            "Pinned ElizaWy inventory count mismatch: "
            f"files={counts['files']} images={counts['images']} "
            f"expected={EXPECTED_FILES}/{EXPECTED_IMAGES}. Re-run dependency verification."
        )
    payload = {
        "schema": "havenwild.external_asset_pack_index.v0_1",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "pack": {
            "id": "elizawy_lpc_main",
            "displayName": "ElizaWy LPC Revised",
            "archiveName": "pinned-git-checkout",
            "archiveSha256": None,
            "sourceCommit": lock["commit"],
            "externalRawRoot": "assets/source/licensed/lpc_revised",
            "licenseStatus": "allowed_with_attribution",
            "attribution": "Per-asset authors and licenses are recorded in the pinned repository Credits.txt and directory credit files.",
            "sourceUrl": lock["repository"],
            "rawFilesCommitted": False,
            "rawFilesPackaged": False,
        },
        "summary": {**counts, "categoryCounts": dict(sorted(category_counts.items()))},
        "records": records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ElizaWy external-pack index rebuilt: {OUTPUT.relative_to(ROOT)} ({len(records):,} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
