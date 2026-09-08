#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "content/editor/stamps/generic_multitile_stamp_contract_v0_1.json"
OUTPUT = ROOT / "docs/assets/previews/havenwild_generic_multitile_stamp_library_pass61.png"


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    entries: list[tuple[str, str, list[int], list[int], Image.Image]] = []
    total = 0
    for relative in contract["registryManifests"]:
        manifest = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        atlas = Image.open((ROOT / relative).with_suffix(".png")).convert("RGBA")
        total += len(manifest.get("objects", []))
        for entry in manifest.get("objects", []):
            footprint = entry.get("visualFootprint", [1, 1])
            if footprint[0] * footprint[1] > 1 or len(entries) < 6:
                entries.append(
                    (
                        entry.get("label") or entry["id"],
                        entry["id"],
                        entry["rect"],
                        footprint,
                        atlas,
                    )
                )
    if len(entries) > 18:
        step = max(1, len(entries) // 18)
        entries = entries[::step][:18]

    output = Image.new("RGBA", (1400, 900), (20, 24, 30, 255))
    draw = ImageDraw.Draw(output)
    draw.text((28, 18), "Havenwild Generic Multi-Tile Stamp Library — Pass 61", fill=(235, 240, 245, 255))
    draw.text(
        (28, 44),
        f"{total} registered project stamps | blue visual bounds | gold anchor",
        fill=(160, 174, 190, 255),
    )
    for index, (label, stable_id, rect, footprint, atlas) in enumerate(entries):
        column, row = index % 6, index // 6
        x, y = 28 + column * 220, 82 + row * 260
        draw.rounded_rectangle(
            (x, y, x + 198, y + 232),
            8,
            fill=(32, 38, 47, 255),
            outline=(76, 88, 103, 255),
            width=2,
        )
        rx, ry, rw, rh = map(int, rect)
        crop = atlas.crop((rx, ry, rx + rw, ry + rh))
        scale = min(170 / max(1, rw), 150 / max(1, rh), 3.0)
        size = (max(1, int(rw * scale)), max(1, int(rh * scale)))
        crop = crop.resize(size, Image.Resampling.NEAREST)
        px, py = x + (198 - size[0]) // 2, y + 12 + (150 - size[1]) // 2
        output.alpha_composite(crop, (px, py))
        draw.rectangle((px, py, px + size[0] - 1, py + size[1] - 1), outline=(82, 156, 236, 255), width=2)
        draw.ellipse((x + 95, y + 159, x + 103, y + 167), fill=(255, 207, 86, 255))
        shown_label = f"{label[:28]}…" if len(label) > 29 else label
        draw.text((x + 10, y + 174), shown_label, fill=(235, 240, 245, 255))
        draw.text((x + 10, y + 194), f"{footprint[0]}x{footprint[1]} tiles", fill=(95, 220, 130, 255))
        draw.text((x + 10, y + 212), stable_id[:28], fill=(150, 163, 180, 255))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.save(OUTPUT)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
