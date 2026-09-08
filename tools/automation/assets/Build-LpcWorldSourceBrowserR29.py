#!/usr/bin/env python3
"""Build the compact W81R29 LPC world-source browser projection.

The full LPC slice catalog remains authoritative.  This projection exposes one
read-only card per non-character LPC source sheet so the native editor can show
what is available before a runtime binding exists.  Raw licensed images remain
in the verified machine-local LPC mount; no artwork is copied into source.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "content/assets/lpc/lpc_slice_catalog_v0_1.json"
OUTPUT = ROOT / "content/editor/assets/lpc_world_source_browser_v1.json"
SOURCE_COMMIT = "f07f7f5892e67c932c68f70bb04472f2c64e46bc"
WORLD_TOP_LEVEL = {"Objects", "Structure", "Terrain", "FX"}

REFERENCE_ONLY_WORDS = {
    "christmas", "copy machine", "copymachine", "fridge", "office", "photocopier",
    "printer", "telephone", "traffic", "vending", "washing machine",
}


def words(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def classify(relative: str) -> tuple[str, str, str]:
    low = relative.lower().replace("\\", "/")

    if low.startswith("fx/"):
        return "effects", "Effects", "Effects"

    if low.startswith("terrain/"):
        if any(token in low for token in ("waterfall", "water", "river", "ocean", "shore", "wave", "ice-shallows")):
            return "water", "Water", "Terrain"
        if any(token in low for token in ("cliff", "mountain", "ridge", "ramp", "ledge", "rocks, cliffs")):
            return "elevation", "Elevation & Cliffs", "Terrain"
        if any(token in low for token in ("road", "path", "trail")):
            return "paths", "Paths & Roads", "Terrain"
        if any(token in low for token in ("tree", "flower", "plant", "mushroom", "wildflower", "rocks, grasslands")):
            return "nature", "Trees & Flora", "Nature & Resources"
        if "tilled_soil" in low or "tilled soil" in low:
            return "farm", "Farming", "Nature & Resources"
        return "terrain", "Ground", "Terrain"

    if low.startswith("structure/"):
        if "/roofing/" in low or any(token in low for token in ("roof", "thatch")):
            return "roof", "Roofs", "Structures"
        if any(token in low for token in ("/doors/", "/stairs/", "/bridges/", "door", "gate", "stair", "bridge", "ladder", "entrance")):
            return "access", "Doors & Access", "Structures"
        if "/floor/" in low or any(token in low for token in ("floor", "carpet", "rug")):
            return "floor", "Floors", "Structures"
        if any(token in low for token in ("/walls/", "wall border", "/windows/", "wall", "window", "column", "pillar")):
            return "wall", "Walls", "Structures"
        if "/fences/" in low:
            return "farm", "Farming", "Nature & Resources"
        if "/signs/" in low:
            return "decor", "Decor", "Interiors"
        return "props", "Structure Parts & Props", "Interiors"

    # Objects: preserve the source's useful semantic subfolders, then refine by item name.
    if "/small items/food/" in low:
        return "food", "Food & Kitchen", "Food & Workshops"
    if any(token in low for token in ("ores & ingots", "ore, ", "/lumber", "/sawdust")):
        return "resources", "Rocks & Resources", "Nature & Resources"
    if any(token in low for token in ("smithing", "sewing & weaving", "tools, carpentry", "tools, sewing", "tools, smithing", "workbench", "sawhorse", "shavehorse", "grindstone", "anvil", "forge", "smelter", "furnace", "bellows", "fabric/")):
        return "crafting", "Workshops & Crafting", "Food & Workshops"
    if any(token in low for token in ("barrel", "crate", "chest", "basket", "sack", "bin", "box", "bucket", "shelf")):
        return "storage", "Storage", "Interiors"
    if any(token in low for token in ("lighting", "lamp", "lantern", "torch", "candle", "fireplace", "brazier", "fire, camp", "fire, fireplace")):
        return "lighting", "Lighting", "Interiors"
    if any(token in low for token in ("flowers", "planter", "mushroom")):
        return "nature", "Trees & Flora", "Nature & Resources"
    if any(token in low for token in ("hay & straw", "trough", "farm", "scarecrow", "beehive", "apiary")):
        return "farm", "Farming", "Nature & Resources"
    if low.startswith("objects/wall items/") or any(token in low for token in ("painting", "poster", "curtain", "mirror", "portrait", "pride flag", "graffiti", "wall decor")):
        return "decor", "Decor", "Interiors"
    if low.startswith("objects/furniture/"):
        if "/rugs/" in low or "rug" in low:
            return "floor", "Floors", "Structures"
        if "ladder" in low:
            return "access", "Doors & Access", "Structures"
        return "furniture", "Furniture", "Interiors"
    if low.startswith("objects/moveable/"):
        return "props", "Structure Parts & Props", "Interiors"
    return "props", "Structure Parts & Props", "Interiors"


def production_state(relative: str) -> str:
    low = relative.lower()
    return "reference_only" if any(word in low for word in REFERENCE_ONLY_WORDS) else "needs_binding"


def stable_id(sheet_id: str) -> str:
    value = sheet_id.removeprefix("lpc/").replace("_", " ")
    tokens = words(value)
    return "lpc.source." + ".".join(tokens)


def main() -> int:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    entries: list[dict] = []
    for sheet in data.get("sheets", []):
        source = str(sheet.get("source", "")).replace("\\", "/")
        marker = "/lpc_revised/"
        if marker not in source:
            continue
        relative = source.split(marker, 1)[1]
        top = relative.split("/", 1)[0]
        if top not in WORLD_TOP_LEVEL:
            continue
        semantic = relative[:-4] if relative.lower().endswith(".png") else relative
        category, category_label, group = classify(semantic)
        display_name = semantic.replace("_", " ").split("/", 1)[-1]
        display_name = display_name.replace("/", " · ")
        keyword_set = [category, group.lower(), *words(semantic)]
        # Stable order without losing first occurrence.
        keywords = list(dict.fromkeys(keyword_set))
        entries.append(
            {
                "stableId": stable_id(str(sheet.get("id", semantic))),
                "displayName": display_name,
                "semanticPath": semantic,
                "category": category,
                "categoryLabel": category_label,
                "group": group,
                "sourcePath": source,
                "imageSize": sheet.get("imageSize", [0, 0]),
                "sliceSize": sheet.get("sliceSize", [32, 32]),
                "sliceCount": int(sheet.get("sliceCount", 0)),
                "nonEmptySliceCount": int(sheet.get("nonEmptySliceCount", 0)),
                "likelyTileable": bool(sheet.get("likelyTileable", False)),
                "productionState": production_state(semantic),
                "keywords": keywords,
            }
        )

    entries.sort(key=lambda entry: (entry["group"], entry["category"], entry["semanticPath"].lower()))
    payload = {
        "schema": "havenwild.editor.lpc_world_source_browser.v1",
        "sourceCatalog": "content/assets/lpc/lpc_slice_catalog_v0_1.json",
        "sourceCommit": SOURCE_COMMIT,
        "purpose": "Expose exact LPC Revised world/terrain/object/structure/FX source sheets in the editor before runtime promotion without copying licensed source images into the repository.",
        "rules": [
            "Source sheets are read-only catalog references until promoted/bound.",
            "Character sheets remain owned by Character Studio and ULPC definition authority.",
            "Raw source images stay in the verified LPC mount and are loaded lazily for thumbnails.",
            "Reference-only themed assets remain browseable but are not production defaults.",
        ],
        "entryCount": len(entries),
        "entries": entries,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"W81R29 LPC world-source browser: {OUTPUT.relative_to(ROOT)}")
    print(f"- entries: {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
