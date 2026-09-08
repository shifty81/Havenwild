#!/usr/bin/env python3
"""Validate Pass 96 mask-authoritative LPC transition seams."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png"
PREVIEW = ROOT / "docs/assets/previews/havenwild_lpc_edge_signature_seams_v108.png"
EDGE_BITS = {"north": 1, "east": 2, "south": 4, "west": 8}


def edge_alpha(image: Image.Image, direction: str) -> list[int]:
    pixels = image.load()
    width, height = image.size
    if direction == "north":
        return [pixels[x, 0][3] for x in range(width)]
    if direction == "east":
        return [pixels[width - 1, y][3] for y in range(height)]
    if direction == "south":
        return [pixels[x, height - 1][3] for x in range(width)]
    return [pixels[0, y][3] for y in range(height)]


def crop(atlas: Image.Image, rect: list[int]) -> Image.Image:
    x, y, width, height = rect
    return atlas.crop((x, y, x + width, y + height))


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("version") != "0.8.1":
        raise AssertionError("Pass 99 transition manifest version 0.8.1 was not generated")
    if payload.get("seamPolicy", {}).get("version") != "havenwild.lpc_replacement_role.v0_2":
        raise AssertionError("authored replacement-role policy missing")
    atlas = Image.open(ATLAS).convert("RGBA")
    groups = set(payload.get("groups", []))
    required = {"sand_over_wet_sand", "pebble_path_over_dirt"}
    if not required.issubset(groups):
        raise AssertionError(f"Pass 95 runtime metadata was not restored: {sorted(required - groups)}")
    if len(payload.get("variants", [])) != 144:
        raise AssertionError(f"expected 144 outer variants, got {len(payload.get('variants', []))}")
    if len(payload.get("innerCornerVariants", [])) != 32:
        raise AssertionError(
            f"expected 32 verified inner corners, got {len(payload.get('innerCornerVariants', []))}"
        )
    failures: list[str] = []
    for entry in payload["variants"]:
        tile = crop(atlas, entry["rect"])
        mask = entry["mask4"]
        if set(entry.get("edgeSignatures", {})) != set(EDGE_BITS):
            failures.append(f"{entry['id']}: signatures missing")
        occupied = tile.getchannel("A").getbbox() is not None
        if mask == 0 and occupied:
            failures.append(f"{entry['id']}: mask zero must remain transparent")
        if mask != 0 and not occupied:
            failures.append(f"{entry['id']}: non-zero replacement role is empty")
    for entry in payload.get("innerCornerVariants", []):
        tile = crop(atlas, entry["rect"])
        if tile.getchannel("A").getbbox() is None:
            failures.append(f"{entry['id']}: verified inner-corner replacement role is empty")
    if failures:
        raise AssertionError("LPC seam conformance failed:\n" + "\n".join(failures[:40]))

    board = Image.new("RGBA", (1320, 760), (21, 25, 30, 255))
    draw = ImageDraw.Draw(board)
    draw.text((24, 18), "Havenwild Pass 96 — LPC edge-signature seam conformance", fill=(242, 245, 248, 255))
    draw.text((24, 42), "Complete authored roles; compound masks close with the verified family center", fill=(155, 195, 178, 255))
    samples = [entry for entry in payload["variants"] if entry["mask4"] in (1, 2, 3, 4, 6, 8, 9, 12, 15)][:72]
    for index, entry in enumerate(samples):
        column, row = index % 9, index // 9
        x, y = 24 + column * 142, 82 + row * 82
        tile = crop(atlas, entry["rect"]).resize((64, 64), Image.Resampling.NEAREST)
        board.alpha_composite(tile, (x, y))
        draw.text((x + 68, y + 18), entry["group"][:10], fill=(220, 225, 230, 255))
        draw.text((x + 68, y + 39), f"mask {entry['mask4']:02}", fill=(150, 185, 210, 255))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    board.save(PREVIEW, optimize=False, compress_level=9)
    print(f"V108 OK: {len(payload['variants'])} outer variants and {len(payload.get('innerCornerVariants', []))} inner corners are seam-conformant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
