#!/usr/bin/env python3
"""Build small runtime item icons from the exact pinned Universal LPC source layers.

The atlas is generated content. It is intentionally excluded from lean source rollups and
is rebuilt after the pinned Universal LPC repository is mounted. Every icon records the
source definition and source PNG used so player-facing UI never substitutes hand-drawn
placeholder glyphs for equipped LPC items.
"""
from __future__ import annotations

import gzip
import json
import math
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = ROOT / "assets/source/licensed/universal_lpc_generator"
NORMALIZED = ROOT / "content/assets/lpc/universal_lpc_normalized_character_catalog_v1.json.gz"
SEEDS = ROOT / "content/gameplay/universal_lpc_equipment_item_seed_catalog_v0_1.json"
OUT_DIR = ROOT / "assets/generated/lpc/item_icons"
OUT_ATLAS = OUT_DIR / "universal_lpc_item_icons_v1.png"
OUT_MANIFEST = OUT_DIR / "universal_lpc_item_icons_v1.json"
CELL = 64
COLS = 16
PADDING = 5


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalized_catalog():
    with gzip.open(NORMALIZED, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def iter_layer_prefixes(definition: dict):
    preferred = ("male", "female", "thin", "universal", "teen", "muscular", "pregnant")
    seen = set()
    for index in range(1, 10):
        layer = definition.get(f"layer_{index}")
        if not isinstance(layer, dict):
            continue
        for key in preferred:
            value = layer.get(key)
            if isinstance(value, str) and value.strip() and value not in seen:
                seen.add(value)
                yield value.strip("/")
        for value in layer.values():
            if isinstance(value, str) and "/" in value and value not in seen:
                seen.add(value)
                yield value.strip("/")


def candidate_pngs(prefix: str):
    root = SOURCE_ROOT / "spritesheets"
    exact = root / prefix
    candidates = []
    if exact.suffix.lower() == ".png" and exact.is_file():
        candidates.append(exact)
    if exact.is_file() and exact.suffix.lower() == ".png":
        candidates.append(exact)
    if exact.is_dir():
        candidates.extend(exact.rglob("*.png"))
    else:
        parent = exact.parent
        stem = exact.name
        if parent.is_dir():
            candidates.extend(parent.glob(stem + "*.png"))
            candidates.extend(parent.glob(stem + "/**/*.png"))
    # Stable preference: idle/walk first, foreground/tool body before background layers.
    def score(path: Path):
        name = path.as_posix().lower()
        s = 0
        if "/idle" in name or name.endswith("idle.png"):
            s += 50
        if "/walk" in name or name.endswith("walk.png"):
            s += 40
        if "/fg" in name or name.endswith("fg.png"):
            s += 20
        if "/bg" in name or name.endswith("bg.png"):
            s -= 8
        if "behind" in name:
            s -= 5
        return (-s, name)
    return sorted({p.resolve() for p in candidates if p.is_file()}, key=score)


def best_frame_crop(path: Path) -> Image.Image | None:
    try:
        image = Image.open(path).convert("RGBA")
    except Exception:
        return None
    if image.getbbox() is None:
        return None

    frame_sizes = [(64, 64), (64, 96), (128, 128), (128, 192), (192, 192), (96, 96)]
    best = None
    best_score = -1.0
    for fw, fh in frame_sizes:
        if image.width % fw or image.height % fh:
            continue
        for y in range(0, image.height, fh):
            for x in range(0, image.width, fw):
                cell = image.crop((x, y, x + fw, y + fh))
                alpha = cell.getchannel("A")
                bbox = alpha.getbbox()
                if bbox is None:
                    continue
                crop = cell.crop(bbox)
                # Favor visible, compact item shapes without preferring enormous sheet-wide boxes.
                nonzero = sum(1 for px in alpha.getdata() if px)
                score = nonzero + crop.width * crop.height * 0.25
                if score > best_score:
                    best_score = score
                    best = crop
    if best is None:
        bbox = image.getchannel("A").getbbox()
        best = image.crop(bbox) if bbox else None
    return best


def fit_icon(crop: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    max_side = CELL - PADDING * 2
    scale = min(max_side / max(1, crop.width), max_side / max(1, crop.height), 4.0)
    size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    resized = crop.resize(size, Image.Resampling.NEAREST)
    x = (CELL - resized.width) // 2
    y = (CELL - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def safe_name(item_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", item_id)


def main() -> int:
    required = [SOURCE_ROOT, NORMALIZED, SEEDS]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing Universal LPC item icon inputs: " + ", ".join(str(p.relative_to(ROOT)) for p in missing))

    normalized = normalized_catalog()
    definitions = {row.get("itemId"): row for row in normalized.get("sheetDefinitions", []) if row.get("itemId")}
    seed_catalog = load_json(SEEDS)
    items = list(seed_catalog.get("items", []))
    if not items:
        raise SystemExit("Universal LPC equipment item seed catalog is empty")

    entries = []
    icon_images = []
    missing_ids = []
    for item in items:
        item_id = item["itemId"]
        definition_id = item.get("equipmentSourceId", "")
        normalized_definition_id = definition_id.removeprefix("ulpc.")
        row = definitions.get(normalized_definition_id)
        chosen_path = None
        crop = None
        if row:
            definition = row.get("definition") or {}
            for prefix in iter_layer_prefixes(definition):
                for path in candidate_pngs(prefix):
                    crop = best_frame_crop(path)
                    if crop is not None and crop.getbbox() is not None:
                        chosen_path = path
                        break
                if crop is not None:
                    break
        if crop is None:
            missing_ids.append(item_id)
            crop = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        icon_images.append(fit_icon(crop))
        entries.append({
            "itemId": item_id,
            "displayName": item.get("displayName", item_id),
            "equipmentSourceId": definition_id,
            "normalizedEquipmentSourceId": normalized_definition_id,
            "sourceDefinition": row.get("sourcePath") if row else None,
            "sourcePng": chosen_path.relative_to(ROOT).as_posix() if chosen_path else None,
        })

    resolved_definition_count = sum(1 for entry in entries if entry.get("sourceDefinition"))
    if resolved_definition_count == 0:
        raise SystemExit(
            "Universal LPC item icon catalog resolved zero equipment definitions; "
            "check equipmentSourceId normalization against the pinned normalized catalog"
        )

    rows = math.ceil(len(entries) / COLS)
    atlas = Image.new("RGBA", (COLS * CELL, rows * CELL), (0, 0, 0, 0))
    for index, icon in enumerate(icon_images):
        col = index % COLS
        row = index // COLS
        atlas.alpha_composite(icon, (col * CELL, row * CELL))
        entries[index]["rect"] = [col * CELL, row * CELL, CELL, CELL]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT_ATLAS, optimize=True)
    manifest = {
        "schema": "havenwild.universal_lpc.item_icon_atlas.v1",
        "sourceCommit": normalized.get("sourceCommit"),
        "sourceAuthority": "assets/source/licensed/universal_lpc_generator",
        "atlas": OUT_ATLAS.relative_to(ROOT).as_posix(),
        "cellSize": CELL,
        "itemCount": len(entries),
        "resolvedIconCount": len(entries) - len(missing_ids),
        "missingItemIds": missing_ids,
        "entries": entries,
        "policy": "generated from exact pinned LPC item/equipment source layers; never hand-drawn placeholder glyphs",
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: Universal LPC item icon atlas: {len(entries) - len(missing_ids)}/{len(entries)} resolved -> {OUT_ATLAS.relative_to(ROOT)}")
    if missing_ids:
        print("INFO unresolved icons remain label-fallback only: " + ", ".join(missing_ids[:12]) + (" ..." if len(missing_ids) > 12 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
