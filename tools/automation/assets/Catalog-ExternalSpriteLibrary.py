"""Inventory external sprite sheets and infer review-only tiles, stamps, and LPC layers."""
from __future__ import annotations

import json
import re
from collections import deque
from datetime import date
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
ROOTS_FILES = [
    ROOT / "content/assets/intake/external_asset_roots_v0_1.json",
    ROOT / ".local/havenwild_external_asset_roots.json",
]
OUTPUT = ROOT / "content/assets/intake/external_sprite_library_catalog_v0_1.json"
IMAGE_EXTENSIONS = {".png", ".gif", ".jpg", ".jpeg"}


def load_roots() -> list[dict]:
    merged: dict[str, dict] = {}
    for roots_file in ROOTS_FILES:
        if not roots_file.is_file():
            continue
        payload = json.loads(roots_file.read_text(encoding="utf-8"))
        for root in payload.get("roots", []):
            if root.get("enabled", True):
                merged[root["id"]] = root
    return list(merged.values())


def classify(path: Path) -> list[str]:
    text = path.as_posix().lower()
    classes: list[str] = []
    keywords = {
        "roof": "roof", "house": "building", "castle": "building",
        "tree": "tree", "forest": "tree", "fence": "fence",
        "water": "coastline", "coast": "coastline", "shore": "coastline", "sand": "coastline",
        "icon": "inventory_icon", "inventory": "inventory_icon", "food": "inventory_icon",
        "weapon": "tool_animation", "sword": "tool_animation", "bow": "tool_animation",
        "magic": "effect_animation", "effect": "effect_animation", "explosion": "effect_animation",
        "ui": "ui_element", "window": "ui_element",
    }
    for key, value in keywords.items():
        if key in text and value not in classes:
            classes.append(value)
    if "/lpc_entry/" in text and "/png/" in text:
        classes.append("character_layer")
    if not classes:
        classes.append("tile")
    return classes


def occupied_grid_components(image: Image.Image, cell: int = 32) -> list[dict]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    cols = (rgba.width + cell - 1) // cell
    rows = (rgba.height + cell - 1) // cell
    occupied = set()
    for gy in range(rows):
        for gx in range(cols):
            crop = alpha.crop((gx * cell, gy * cell, min((gx + 1) * cell, rgba.width), min((gy + 1) * cell, rgba.height)))
            if crop.getbbox() is not None:
                occupied.add((gx, gy))
    components = []
    while occupied:
        start = occupied.pop()
        queue = deque([start])
        points = [start]
        while queue:
            x, y = queue.popleft()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in occupied:
                    occupied.remove(neighbor)
                    queue.append(neighbor)
                    points.append(neighbor)
        min_x = min(x for x, _ in points)
        max_x = max(x for x, _ in points)
        min_y = min(y for _, y in points)
        max_y = max(y for _, y in points)
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        if width > 1 or height > 1:
            components.append({
                "sourceRect": [min_x * cell, min_y * cell, min(width * cell, rgba.width - min_x * cell), min(height * cell, rgba.height - min_y * cell)],
                "gridWidth": width,
                "gridHeight": height,
                "reviewState": "inferred_draft"
            })
    return components[:128]


def lpc_layer(relative: Path) -> dict | None:
    parts = [part.lower() for part in relative.parts]
    if "lpc_entry" not in parts or "png" not in parts:
        return None
    try:
        png_index = parts.index("png")
        animation = relative.parts[png_index + 1]
    except (ValueError, IndexError):
        return None
    match = re.match(r"([A-Z]+)_(.+)\.(?:png|gif)$", relative.name, re.IGNORECASE)
    if not match:
        return None
    return {
        "animation": animation,
        "slot": match.group(1).lower(),
        "variant": match.group(2),
        "frameWidth": 64,
        "frameHeight": 64,
        "directions": ["back", "left", "front", "right"],
        "framesPerDirection": 9 if animation == "walkcycle" else None,
        "reviewState": "source_layout_known"
    }


def main() -> None:
    roots = load_roots()
    records = []
    for source_root in roots:
        base = Path(source_root["path"])
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS):
            relative = path.relative_to(base)
            try:
                with Image.open(path) as image:
                    width, height = image.size
                    frames = getattr(image, "n_frames", 1)
                    record = {
                        "id": f"{source_root['id']}/{relative.as_posix().lower()}",
                        "sourceRoot": source_root["id"],
                        "sourceDisplayName": source_root.get("displayName", source_root["id"]),
                        "licenseStatus": source_root.get("licenseStatus", "unknown_requires_review"),
                        "relativePath": relative.as_posix(),
                        "width": width,
                        "height": height,
                        "frames": frames,
                        "gridCandidates": [size for size in (16, 32, 64) if width % size == 0 and height % size == 0],
                        "classes": classify(relative),
                        "stampCandidates32": occupied_grid_components(image),
                        "promotionState": "draft_reference_only"
                    }
                    layer = lpc_layer(relative)
                    if layer:
                        record["characterLayer"] = layer
                    records.append(record)
            except Exception as error:
                records.append({
                    "id": f"{source_root['id']}/{relative.as_posix().lower()}",
                    "sourceRoot": source_root["id"],
                    "relativePath": relative.as_posix(),
                    "error": str(error),
                    "promotionState": "unreadable"
                })
    payload = {
        "schema": "havenwild.external_sprite_library_catalog.v0_1",
        "generated": str(date.today()),
        "records": records
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Cataloged {len(records)} external sprite sheets -> {OUTPUT}")


if __name__ == "__main__":
    main()
