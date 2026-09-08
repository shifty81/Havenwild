#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = ROOT / "assets/source/licensed/lpc_revised/Terrain/cliff_summer.png"
DEFAULT_V7 = ROOT / "content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.png"
OUTPUT = ROOT / "assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png"
SOURCE_SHA256 = "94bd2ddb2c51677498453486092ef28e57e0c1880f4334359189229590298147"
V7_SHA256 = "adc395adc3defb182389d4ca888afdd896bdd6b672ab92609b428a5bbd79cd25"

# ElizaWy's grass palette is semantic surface material, not structural cliff
# geometry. W3 strips it from the derived *overlay* globally so complete authored
# 32x32 cliff cells/stamps can be projected over the V7 semantic terrain provider
# without carrying foreign rectangular ground fills. No rock/fringe geometry is
# cropped, mirrored, stretched, rotated, or synthesized.
ELIZAWY_SEMANTIC_GRASS_RGB = {
    (70, 130, 50),
    (117, 167, 67),
    (48, 100, 47),
    (28, 69, 37),
    (37, 86, 46),
    (25, 51, 45),
}
V7_GRASS_TILE_ID = 5
V7_COLUMNS = 16
TILE = 32


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def v7_grass_owner_rgb(v7: Image.Image) -> tuple[int, int, int]:
    col = V7_GRASS_TILE_ID % V7_COLUMNS
    row = V7_GRASS_TILE_ID // V7_COLUMNS
    crop = v7.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE)).convert("RGBA")
    r, g, b, _a = crop.getpixel((TILE // 2, TILE // 2))
    return (r, g, b)


def strip_semantic_ground(image: Image.Image, v7_owner: tuple[int, int, int]) -> None:
    pixels = image.load()
    semantic = set(ELIZAWY_SEMANTIC_GRASS_RGB)
    # This also makes the builder idempotent against an already-normalized W2
    # overlay whose broad owner fill had been converted to the pinned V7 green.
    semantic.add(v7_owner)
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a and (r, g, b) in semantic:
                pixels[x, y] = (0, 0, 0, 0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build Havenwild's whole-cell ElizaWy structural cliff overlay paired with the pinned V7 surface provider."
        )
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--v7", type=Path, default=DEFAULT_V7)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    source = args.source.resolve()
    v7_path = args.v7.resolve()
    output = args.output.resolve()
    if not source.is_file():
        raise SystemExit(
            f"ElizaWy source not found: {source}\n"
            "Run the LPC source sync first or pass --source <cliff_summer.png>."
        )
    if not v7_path.is_file():
        raise SystemExit(f"Pinned V7 terrain map not found: {v7_path}")

    actual_sha = sha256(source)
    if actual_sha != SOURCE_SHA256:
        raise SystemExit(
            f"Pinned ElizaWy cliff source hash mismatch: expected {SOURCE_SHA256}, found {actual_sha}"
        )
    actual_v7_sha = sha256(v7_path)
    if actual_v7_sha != V7_SHA256:
        raise SystemExit(f"Pinned V7 terrain-map hash mismatch: expected {V7_SHA256}, found {actual_v7_sha}")

    image = Image.open(source).convert("RGBA")
    v7 = Image.open(v7_path).convert("RGBA")
    if image.size != (512, 448):
        raise SystemExit(f"Unexpected ElizaWy cliff dimensions: {image.size}")
    if v7.width != 512 or v7.height % TILE:
        raise SystemExit(f"Unexpected V7 terrain-map dimensions: {v7.size}")

    owner_rgb = v7_grass_owner_rgb(v7)
    strip_semantic_ground(image, owner_rgb)

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)
    print(f"Wrote {output.relative_to(ROOT)}")
    print(f"ElizaWy source sha256: {actual_sha}")
    print(f"V7 source sha256: {actual_v7_sha}")
    print(f"stripped semantic grass palette + V7 owner RGB: {owner_rgb}")
    print(f"output sha256: {sha256(output)}")


if __name__ == "__main__":
    main()
