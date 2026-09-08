#!/usr/bin/env python3
"""Build the OpenGameArt Tiled terrain-pack catalog for Havenwild."""
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
CATALOG_ID = "open_game_art_terrain_pack_v0_1"
SOURCE = "content/assets/lpc/source/open-game-art-terrain-pack-v0-1"
PREVIEW = ROOT / "docs/assets/previews/havenwild_open_game_art_terrain_pack_materials_pass114.png"


def build_numbered_preview(tsx: Path, png: Path) -> None:
    root = ET.parse(tsx).getroot()
    tile_width = int(root.attrib["tilewidth"])
    tile_height = int(root.attrib["tileheight"])
    terrain_nodes = root.find("terraintypes")
    if terrain_nodes is None:
        raise SystemExit("V123 build: missing terraintypes in OpenGameArt TSX")

    source = Image.open(png).convert("RGBA")
    columns = source.width // tile_width
    terrains = [(terrain.attrib["name"], int(terrain.attrib["tile"])) for terrain in terrain_nodes.findall("terrain")]
    cell_w = 208
    cell_h = 58
    cols = 3
    rows = (len(terrains) + cols - 1) // cols
    margin = 16
    board = Image.new("RGBA", (margin * 2 + cols * cell_w, margin * 2 + 36 + rows * cell_h), (22, 27, 30, 255))
    draw = ImageDraw.Draw(board)
    draw.text((margin, margin), "OpenGameArt Tiled Terrain Materials - Pass114", fill=(235, 235, 220, 255))

    for index, (name, tile_id) in enumerate(terrains, start=1):
        col = (index - 1) % cols
        row = (index - 1) // cols
        x = margin + col * cell_w
        y = margin + 34 + row * cell_h
        sx = (tile_id % columns) * tile_width
        sy = (tile_id // columns) * tile_height
        crop = source.crop((sx, sy, sx + tile_width, sy + tile_height))
        board.alpha_composite(crop, (x, y + 6))
        draw.text((x + 42, y + 6), f"{index:02d}. {name}", fill=(238, 238, 225, 255))
        draw.text((x + 42, y + 25), f"tile {tile_id}", fill=(172, 182, 178, 255))

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    board.save(PREVIEW)


def main() -> int:
    tsx = ROOT / SOURCE / "terrain.tsx"
    png = ROOT / SOURCE / "terrain.png"
    attribution = ROOT / SOURCE / "Attribution.txt"
    for path in [tsx, png, attribution]:
        if not path.is_file():
            raise SystemExit(f"V123 build: missing {path.relative_to(ROOT)}")

    command = [
        sys.executable,
        str(ROOT / "tools/automation/terrain/Build-TiledCornerTerrainCatalog.py"),
        "--id",
        CATALOG_ID,
        "--tsx",
        str(tsx.relative_to(ROOT)),
        "--png",
        str(png.relative_to(ROOT)),
        "--out-json",
        "content/assets/lpc/open_game_art_terrain_corner_catalog_v0_1.json",
        "--out-png",
        "assets/generated/worldgen_v0_1/terrain/open_game_art_terrain_pack_v0_1.png",
        "--report",
        "docs/assets/OPEN_GAME_ART_TERRAIN_PACK_CATALOG_PASS114.md",
        "--license",
        "OpenGameArt terrain pack attribution is stored beside the source TSX/PNG.",
    ]
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode:
        return completed.returncode
    build_numbered_preview(tsx, png)
    print(f"Wrote {PREVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
