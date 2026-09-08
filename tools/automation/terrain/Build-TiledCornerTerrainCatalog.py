#!/usr/bin/env python3
"""Build a generic Tiled corner-terrain catalog from a TSX/PNG pair."""
from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EMPTY_TERRAIN = "__empty__"


def repo_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def parse_aliases(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(repo_path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("alias map must be a JSON object of Havenwild material -> Tiled terrain")
    return {str(key): str(value) for key, value in payload.items()}


def material_id(catalog_id: str, terrain: str) -> str:
    prefix = catalog_id.lower().replace("_", "-")
    return prefix + "-" + terrain.lower().replace("_", "-")


def material_label(terrain: str) -> str:
    if terrain == EMPTY_TERRAIN:
        return "Empty"
    return terrain.replace("_", " ")


def material_category(terrain: str) -> str:
    if terrain == EMPTY_TERRAIN:
        return "empty"
    lower = terrain.lower()
    if "water" in lower:
        return "water"
    if "lava" in lower:
        return "hazard"
    if "hole" in lower:
        return "void"
    if "snow" in lower or "ice" in lower:
        return "cold"
    if "rock" in lower or "stone" in lower or "mudstone" in lower:
        return "stone"
    if "grass" in lower:
        return "grass"
    if "dirt" in lower or "earth" in lower or "soil" in lower or "mud" in lower:
        return "earth"
    if "sand" in lower or "gravel" in lower:
        return "loose_ground"
    return "terrain"


def editor_materials(catalog_id: str, terrains: list[str], entries: list[dict], aliases: dict[str, str]) -> list[dict]:
    aliases_by_terrain: dict[str, list[str]] = {}
    for material, terrain in aliases.items():
        aliases_by_terrain.setdefault(terrain, []).append(material)

    tuple_counts: Counter[str] = Counter()
    pure_tile_id: dict[str, int] = {}
    for entry in entries:
        corners = [entry["corners"][key] for key in ["topLeft", "topRight", "bottomLeft", "bottomRight"]]
        tuple_counts.update(corner for corner in set(corners) if corner != EMPTY_TERRAIN)
        if len(set(corners)) == 1 and corners[0] != EMPTY_TERRAIN:
            pure_tile_id.setdefault(corners[0], entry["tileId"])

    return [
        {
            "id": material_id(catalog_id, terrain),
            "label": material_label(terrain),
            "tiledTerrain": terrain,
            "category": material_category(terrain),
            "sourceCatalog": catalog_id,
            "tupleCount": tuple_counts[terrain],
            "pureFillTileId": pure_tile_id.get(terrain),
            "editorCatalogStatus": "generic_terrain_material",
            "runtimePaintSurface": "tile_kind" if aliases_by_terrain.get(terrain) else "generic_material_pending_storage",
            "paintableNow": bool(aliases_by_terrain.get(terrain)),
            "tileKindAliases": aliases_by_terrain.get(terrain, []),
        }
        for terrain in terrains
    ]


def read_tiled_corner_entries(tsx_path: Path, png_path: Path) -> tuple[list[str], list[dict], int, int]:
    root = ET.parse(tsx_path).getroot()
    tile_width = int(root.attrib["tilewidth"])
    tile_height = int(root.attrib["tileheight"])
    image_node = root.find("image")
    columns_attr = root.attrib.get("columns")
    if columns_attr:
        columns = int(columns_attr)
    elif image_node is not None and image_node.attrib.get("width"):
        columns = int(image_node.attrib["width"]) // tile_width
    else:
        raise ValueError(f"{tsx_path} has no columns attribute or image width")
    terrain_root = root.find("terraintypes")
    if terrain_root is None:
        raise ValueError(f"{tsx_path} has no terraintypes block")
    terrains = [terrain.attrib["name"] for terrain in terrain_root.findall("terrain")]
    if not terrains:
        raise ValueError(f"{tsx_path} has no named terrain types")

    entries = []
    seen: set[tuple[str, str, str, str]] = set()
    for tile in root.findall("tile"):
        terrain_attr = tile.attrib.get("terrain")
        if not terrain_attr:
            continue
        names = tuple(EMPTY_TERRAIN if value == "" else terrains[int(value)] for value in terrain_attr.split(","))
        if len(names) != 4:
            raise ValueError(f"tile {tile.attrib.get('id')} does not declare four terrain corners")
        if names in seen:
            continue
        tile_id = int(tile.attrib["id"])
        rect = [
            (tile_id % columns) * tile_width,
            (tile_id // columns) * tile_height,
            tile_width,
            tile_height,
        ]
        seen.add(names)
        entries.append(
            {
                "tileId": tile_id,
                "corners": {
                    "topLeft": names[0],
                    "topRight": names[1],
                    "bottomLeft": names[2],
                    "bottomRight": names[3],
                },
                "rect": rect,
            }
        )
    entries.sort(key=lambda entry: entry["tileId"])
    if not png_path.is_file():
        raise FileNotFoundError(png_path)
    return terrains, entries, tile_width, tile_height


def write_report(
    report_path: Path,
    catalog_id: str,
    source_tsx: Path,
    terrains: list[str],
    entries: list[dict],
    aliases: dict[str, str],
    materials: list[dict],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    usage: Counter[str] = Counter()
    pure = set()
    for entry in entries:
        corners = [entry["corners"][key] for key in ["topLeft", "topRight", "bottomLeft", "bottomRight"]]
        usage.update(corner for corner in set(corners) if corner != EMPTY_TERRAIN)
        if len(set(corners)) == 1 and corners[0] != EMPTY_TERRAIN:
            pure.add(corners[0])

    active = set(aliases.values())
    lines = [
        f"# {catalog_id} Tiled Corner Terrain Catalog",
        "",
        f"Source: `{source_tsx.relative_to(ROOT) if source_tsx.is_relative_to(ROOT) else source_tsx}`",
        "",
        f"- Terrain types: {len(terrains)}",
        f"- Unique corner tuples: {len(entries)}",
        f"- Pure fills: {len(pure)}",
        "",
    ]
    if aliases:
        lines.extend(["## Havenwild Aliases", "", "| Material | Tiled terrain |", "|---|---|"])
        for material, terrain in aliases.items():
            lines.append(f"| `{material}` | `{terrain}` |")
        lines.append("")
    lines.extend(["## Terrain Types", "", "| # | Terrain | Tuples | Pure fill | Status |", "|---:|---|---:|---|---|"])
    for index, terrain in enumerate(terrains):
        status = "active alias" if terrain in active else "cataloged"
        lines.append(f"| {index} | `{terrain}` | {usage[terrain]} | {'yes' if terrain in pure else 'no'} | {status} |")
    lines.extend([
        "",
        "## Editor Catalog",
        "",
        f"Generic terrain material records: {len(materials)}",
        f"Paintable through current aliases: {sum(1 for material in materials if material['paintableNow'])}",
    ])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, help="Stable catalog id")
    parser.add_argument("--tsx", required=True, help="Input Tiled TSX path")
    parser.add_argument("--png", required=True, help="Input image path")
    parser.add_argument("--out-json", required=True, help="Output manifest JSON path")
    parser.add_argument("--out-png", required=True, help="Output atlas PNG path")
    parser.add_argument("--report", required=True, help="Output Markdown report path")
    parser.add_argument("--aliases-json", help="Optional JSON map of Havenwild material -> Tiled terrain")
    parser.add_argument("--license", default="", help="License/credits note")
    args = parser.parse_args()

    tsx_path = repo_path(args.tsx)
    png_path = repo_path(args.png)
    out_json = repo_path(args.out_json)
    out_png = repo_path(args.out_png)
    report = repo_path(args.report)
    aliases = parse_aliases(args.aliases_json)
    terrains, entries, tile_width, tile_height = read_tiled_corner_entries(tsx_path, png_path)
    materials = editor_materials(args.id, terrains, entries, aliases)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(png_path, out_png)
    manifest = {
        "id": args.id,
        "kind": "tiled_corner_terrain_catalog",
        "version": "0.1.0",
        "tileSize": [tile_width, tile_height],
        "output": str(out_png.relative_to(ROOT) if out_png.is_relative_to(ROOT) else out_png).replace("\\", "/"),
        "source": str(tsx_path.relative_to(ROOT) if tsx_path.is_relative_to(ROOT) else tsx_path).replace("\\", "/"),
        "license": args.license,
        "runtimePolicy": "catalog all Tiled corner tuples; promote paintable materials through explicit Havenwild aliases",
        "emptyTerrainName": EMPTY_TERRAIN,
        "terrainTypes": terrains,
        "editorMaterials": materials,
        "tileKindTerrainMap": aliases,
        "entries": entries,
    }
    out_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_report(report, args.id, tsx_path, terrains, entries, aliases, materials)
    print(f"Generated {out_json.relative_to(ROOT) if out_json.is_relative_to(ROOT) else out_json}")
    print(f"Generated {out_png.relative_to(ROOT) if out_png.is_relative_to(ROOT) else out_png}")
    print(f"Wrote {report.relative_to(ROOT) if report.is_relative_to(ROOT) else report}")
    print(f"Cataloged {len(entries)} tuples across {len(terrains)} terrain types")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
