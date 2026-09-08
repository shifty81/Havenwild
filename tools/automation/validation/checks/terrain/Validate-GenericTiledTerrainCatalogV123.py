#!/usr/bin/env python3
"""Validate generic Tiled-corner terrain catalog intake."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "content/assets/lpc/source/open-game-art-terrain-pack-v0-1"
MANIFEST = ROOT / "content/assets/lpc/open_game_art_terrain_corner_catalog_v0_1.json"
ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/open_game_art_terrain_pack_v0_1.png"
REPORT = ROOT / "docs/assets/OPEN_GAME_ART_TERRAIN_PACK_CATALOG_PASS114.md"
PREVIEW = ROOT / "docs/assets/previews/havenwild_open_game_art_terrain_pack_materials_pass114.png"


def require_text(path: str, needles: list[str]) -> None:
    payload = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in payload]
    if missing:
        raise SystemExit(f"V123: {path} missing {missing}")


def main() -> int:
    for path in [
        SOURCE / "terrain.tsx",
        SOURCE / "terrain.png",
        SOURCE / "Attribution.txt",
        MANIFEST,
        ATLAS,
        REPORT,
        PREVIEW,
    ]:
        if not path.is_file():
            raise SystemExit(f"V123: missing {path.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("id") != "open_game_art_terrain_pack_v0_1":
        raise SystemExit("V123: wrong OpenGameArt catalog id")
    if manifest.get("kind") != "tiled_corner_terrain_catalog":
        raise SystemExit("V123: OpenGameArt terrain pack must use the generic Tiled-corner catalog kind")
    if manifest.get("emptyTerrainName") != "__empty__":
        raise SystemExit("V123: blank Tiled terrain corners must be preserved as __empty__")
    terrain_types = manifest.get("terrainTypes", [])
    if len(terrain_types) < 27:
        raise SystemExit("V123: expected the uploaded OpenGameArt pack's full terrain list")
    for terrain in ["Lava", "Hole", "Water", "Grass", "Wheat", "Sand Water", "Snow Ice", "Brick Road", "Sewer Water"]:
        if terrain not in terrain_types:
            raise SystemExit(f"V123: missing terrain type {terrain}")
    entries = manifest.get("entries", [])
    if len(entries) < 200:
        raise SystemExit("V123: expected hundreds of Tiled corner tuples from the uploaded pack")
    materials = manifest.get("editorMaterials", [])
    if len(materials) != len(terrain_types):
        raise SystemExit("V123: every OpenGameArt terrain type must become one editor material")
    by_terrain = {material.get("tiledTerrain"): material for material in materials}
    checks = {
        "Lava": "hazard",
        "Hole": "void",
        "Water": "water",
        "Snow Ice": "cold",
        "Brick Road": "terrain",
        "Sand Water": "water",
    }
    for terrain, category in checks.items():
        material = by_terrain.get(terrain)
        if not material or material.get("category") != category:
            raise SystemExit(f"V123: {terrain} must be cataloged as {category}")
        if material.get("paintableNow"):
            raise SystemExit(f"V123: {terrain} should remain catalog-only until runtime storage maps it")

    require_text(
        "tools/automation/terrain/Build-TiledCornerTerrainCatalog.py",
        [
            "EMPTY_TERRAIN",
            "columns_attr",
            "image_node",
            "emptyTerrainName",
            "catalog all Tiled corner tuples",
        ],
    )
    require_text(
        "tools/automation/terrain/Build-OpenGameArtTerrainCatalogV123.py",
        [
            "open_game_art_terrain_pack_v0_1",
            "Build-TiledCornerTerrainCatalog.py",
            "build_numbered_preview",
            "Attribution.txt",
        ],
    )
    require_text(
        "content/assets/lpc/tiled_corner_terrain_ingest_contract_v0_1.json",
        [
            "Blank corner indexes are preserved",
            "columns may be derived from the image width",
            "emptyTerrainName",
        ],
    )
    require_text(
        "tools/build/Build.sh",
        [
            "build OpenGameArt Tiled terrain material catalog",
            "Validate-GenericTiledTerrainCatalogV123.py",
        ],
    )
    require_text("tools/automation/validation/validate.py", ["Validate-GenericTiledTerrainCatalogV123.py"])
    print("V123 OK: generic Tiled terrain-pack intake catalogs every uploaded terrain material")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
