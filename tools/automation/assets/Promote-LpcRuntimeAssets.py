#!/usr/bin/env python3
"""Promote the pinned ElizaWy/LPC source tree into runtime/editor catalogs.

The slice catalog is virtual: it records 32x32 source-cell rects and sheet
metadata without writing millions of tiny files. Runtime atlases can then copy
from those rects when a cell is promoted into worldgen, objects, stamps, or
autotiles.
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
LPC_ROOT = ROOT / "assets/source/licensed/lpc_revised"
SLICE_CATALOG = ROOT / "content/assets/lpc/lpc_slice_catalog_v0_1.json"
SLICE_CATALOG_GZ = ROOT / "content/assets/lpc/lpc_slice_catalog_v0_1.json.gz"
ASSET_LIBRARY_BUNDLE_GZ = ROOT / "content/assets/lpc/lpc_asset_library_bundle_v0_1.json.gz"
OBJECT_ATLAS = ROOT / "assets/generated/havenwild_lpc_objects_160x192_v2.png"
OBJECT_MANIFEST = ROOT / "assets/generated/havenwild_lpc_objects_160x192_v2.json"
LEGACY_OBJECT_ATLAS = ROOT / "assets/generated/havenwild_2p5d_objects_32x64_v1.png"
LEGACY_OBJECT_MANIFEST = ROOT / "assets/generated/havenwild_2p5d_objects_32x64_v1.json"
OBJECT_REVISION = ROOT / "assets/generated/.lpc_terrain_object_revision"
OBJECT_REVISION_ID = "AC3R4F-tree-visible-natural-object-rebuild-v1"
EXTERNAL_SOURCES = ROOT / "content/assets/external_sources/external_asset_sources_v0_1.json"
DONOR_CATALOG = ROOT / "content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json"
ASSET_CATALOG = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"
PROJECT_AUTHORITY = ROOT / "content/assets/lpc/lpc_project_asset_authority_v0_1.json"
PROJECT_AUDIT_SUMMARY = ROOT / "WORKSPACE/generated/lpc/elizawy_repository_audit_v167z38_summary.json"
PROJECT_DOMAIN_CATALOG_ROOT = ROOT / "WORKSPACE/generated/lpc/catalogs"
PIXEL_WORKBENCH = ROOT / "content/assets/pixel_editor/pixel_editor_reference_workbench_v0_1.json"
IMPORT_QUEUE = ROOT / "content/assets/prototype_imports/prototype_asset_import_queue_v0_1.json"
IMPORT_INSTRUCTIONS = (
    ROOT
    / "content/assets/prototype_imports/prototype_asset_local_import_instructions_v0_1.json"
)
REFERENCE_PREVIEWS = (
    ROOT / "content/assets/reference_previews/asset_reference_preview_catalog_v0_1.json"
)
DRY_RUN_REPORT = (
    ROOT / "WORKSPACE/generated/prototype_imports/prototype_asset_bake_dry_run_report_v0_1.json"
)

TILE = 32
OBJECT_CELL = (160, 192)
OBJECT_COLUMNS = 8
OBJECT_IDS = [
    "oak_tree",
    "berry_bush",
    "oak_tree_variant_02",
    "oak_tree_variant_03",
    "boulder",
    "ore_node",
    "forage_mushroom",
    "wild_herb",
    "table_round",
    "chair_wood",
    "bar_counter",
    "keg",
    "oak_tree_variant_04",
    "berry_bush_variant_02",
    "forage_mushroom_variant_02",
    "wildflower_patch",
    "bed_basic",
    "fireplace",
    "door",
    "stairs_up",
    "crate_stack",
    "barrel",
    "well_pump",
    "scarecrow",
    "fence_post",
    "lamp_post",
    "construction_tape",
    "reed_patch",
    "bench",
    "tree_stump",
    "fallen_log",
    "signboard",
    "oak_tree_variant_05",
    "oak_tree_variant_06",
    "oak_tree_variant_07",
    "oak_tree_variant_08",
    "berry_bush_variant_03",
    "berry_bush_variant_04",
    "boulder_variant_02",
    "boulder_variant_03",
    "boulder_variant_04",
    "forage_mushroom_variant_03",
    "forage_mushroom_variant_04",
    "wild_herb_variant_02",
    "wild_herb_variant_03",
    "wildflower_patch_variant_02",
    "reed_patch_variant_02",
    "wildflower_patch_variant_03",
]


REQUIRED_WORLD_NATURE_PREFIXES = (
    "oak_tree",
    "berry_bush",
    "boulder",
    "forage_mushroom",
    "wild_herb",
    "wildflower_patch",
    "reed_patch",
)

OBJECT_SOURCE_CANDIDATES = {
    "oak_tree": ["Terrain/trees_summer.png"],
    "oak_tree_variant_02": ["Terrain/trees_summer.png"],
    "oak_tree_variant_03": ["Terrain/trees_summer.png"],
    "oak_tree_variant_04": ["Terrain/trees_summer.png"],
    "oak_tree_variant_05": ["Terrain/trees_summer.png"],
    "oak_tree_variant_06": ["Terrain/trees_summer.png"],
    "oak_tree_variant_07": ["Terrain/trees_summer.png"],
    "oak_tree_variant_08": ["Terrain/trees_summer.png"],
    "berry_bush": ["Terrain/plants_summer.png"],
    "berry_bush_variant_02": ["Terrain/plants_summer.png"],
    "berry_bush_variant_03": ["Terrain/plants_summer.png"],
    "berry_bush_variant_04": ["Terrain/plants_summer.png"],
    "boulder": ["Terrain/Rocks, Grasslands.png"],
    "boulder_variant_02": ["Terrain/Rocks, Grasslands.png"],
    "boulder_variant_03": ["Terrain/Rocks, Grasslands.png"],
    "boulder_variant_04": ["Terrain/Rocks, Grasslands.png"],
    "ore_node": ["Objects/Small Items/Ores & Ingots/Ore, Iron.png"],
    "forage_mushroom": ["Terrain/mushrooms.png"],
    "forage_mushroom_variant_02": ["Terrain/mushrooms.png"],
    "forage_mushroom_variant_03": ["Terrain/mushrooms.png"],
    "forage_mushroom_variant_04": ["Terrain/mushrooms.png"],
    "wildflower_patch": ["Terrain/wildflowers_summer.png", "Terrain/flowers.png"],
    "wildflower_patch_variant_02": ["Terrain/wildflowers_summer.png", "Terrain/flowers.png"],
    "wildflower_patch_variant_03": ["Terrain/flowers.png", "Terrain/wildflowers_summer.png"],
    "reed_patch": ["Terrain/plants_summer.png", "Terrain/wildflowers_summer.png"],
    "reed_patch_variant_02": ["Terrain/plants_summer.png", "Terrain/wildflowers_summer.png"],
    "wild_herb": [
        "Terrain/wildflowers_summer.png",
        "Terrain/flowers.png",
        "Terrain/plants_summer.png",
    ],
    "wild_herb_variant_02": [
        "Terrain/wildflowers_summer.png",
        "Terrain/flowers.png",
        "Terrain/plants_summer.png",
    ],
    "wild_herb_variant_03": [
        "Terrain/plants_summer.png",
        "Terrain/wildflowers_summer.png",
        "Terrain/flowers.png",
    ],
    "table_round": [
        "Objects/Furniture/Table, Rough Wood.png",
        "Objects/Furniture/Table, Card.png",
    ],
    "chair_wood": ["Objects/Furniture/Seating/Chair, Dining A.png"],
    "bar_counter": ["Objects/Furniture/Countertop.png"],
    "keg": ["Objects/Furniture/Barrel.png"],
    "bed_basic": ["Objects/Furniture/Beds/Beds, Single  A.png"],
    "fireplace": ["Objects/Furniture/Fireplace.png"],
    "door": ["Structure/Doors/Doors.png", "Structure/Doors/32x64px Doors/Doors.png"],
    "stairs_up": ["Objects/Furniture/Ladder.png", "Structure/Misc/Ladder.png"],
    "crate_stack": ["Objects/Furniture/Crate.png"],
    "barrel": ["Objects/Furniture/Barrel.png"],
    "well_pump": ["Structure/Misc/Well.png", "Objects/Furniture/Water Cooler.png"],
    "scarecrow": ["Objects/Furniture/Dress Form.png"],
    "fence_post": ["Structure/Fences/Fences.png"],
    "lamp_post": ["Objects/Furniture/Lighting, Outdoors.png"],
    "construction_tape": ["Structure/Misc/Construction Tape.png"],
    "bench": ["Objects/Furniture/Seating/Ottoman, Long A.png"],
    "tree_stump": ["Terrain/trees_summer.png"],
    "fallen_log": ["Objects/Small Items/Lumber.png"],
    "signboard": ["Objects/Furniture/Standing Screen.png"],
}

# Exact semantic slices override generic connected-component extraction when a
# source sheet intentionally contains several independent sprites. A normal
# gameplay Crate must resolve to one crate, never the whole Crate.png sheet.
OBJECT_EXACT_SOURCE_RECTS = {
    "crate_stack": (0, 32, 32, 32),
}

OBJECT_VARIANT_RANK = {
    "oak_tree": 0,
    "oak_tree_variant_02": 1,
    "oak_tree_variant_03": 2,
    "oak_tree_variant_04": 3,
    "oak_tree_variant_05": 4,
    "oak_tree_variant_06": 5,
    "oak_tree_variant_07": 6,
    "oak_tree_variant_08": 7,
    "berry_bush": 0,
    "berry_bush_variant_02": 1,
    "berry_bush_variant_03": 2,
    "berry_bush_variant_04": 3,
    "boulder": 0,
    "boulder_variant_02": 1,
    "boulder_variant_03": 2,
    "boulder_variant_04": 3,
    "forage_mushroom": 0,
    "forage_mushroom_variant_02": 1,
    "forage_mushroom_variant_03": 2,
    "forage_mushroom_variant_04": 3,
    "wild_herb": 0,
    "wild_herb_variant_02": 1,
    "wild_herb_variant_03": 2,
    "wildflower_patch": 3,
    "wildflower_patch_variant_02": 4,
    "wildflower_patch_variant_03": 5,
    "reed_patch": 6,
    "reed_patch_variant_02": 7,
}

OBJECT_RUNTIME_METADATA = {
    "tree": {
        "visualFootprintTiles": [3, 4],
        "collisionFootprintTiles": [1, 1],
        "occludesPlayer": True,
        "fadeWhenPlayerBehind": True,
        "interaction": "chop",
        "placementRole": "forest_canopy_primary",
    },
    "bush": {
        "visualFootprintTiles": [1, 1],
        "collisionFootprintTiles": [1, 1],
        "occludesPlayer": False,
        "fadeWhenPlayerBehind": False,
        "interaction": "forage",
        "placementRole": "forest_understory",
    },
    "rock": {
        "visualFootprintTiles": [1, 1],
        "collisionFootprintTiles": [1, 1],
        "occludesPlayer": False,
        "fadeWhenPlayerBehind": False,
        "interaction": "mine",
        "placementRole": "natural_obstacle",
    },
    "forage": {
        "visualFootprintTiles": [1, 1],
        "collisionFootprintTiles": [0, 0],
        "occludesPlayer": False,
        "fadeWhenPlayerBehind": False,
        "interaction": "forage",
        "placementRole": "forest_floor",
    },
    "default": {
        "visualFootprintTiles": [1, 2],
        "collisionFootprintTiles": [1, 1],
        "occludesPlayer": False,
        "fadeWhenPlayerBehind": False,
        "interaction": "use",
        "placementRole": "object",
    },
}


def object_metadata(object_id: str) -> dict:
    if object_id == "crate_stack":
        return {
            "visualFootprintTiles": [1, 1],
            "collisionFootprintTiles": [1, 1],
            "occludesPlayer": False,
            "fadeWhenPlayerBehind": False,
            "interaction": "open",
            "placementRole": "container",
        }
    if object_id.startswith("oak_tree"):
        return OBJECT_RUNTIME_METADATA["tree"]
    if object_id.startswith("berry_bush"):
        return OBJECT_RUNTIME_METADATA["bush"]
    if object_id.startswith("boulder"):
        return OBJECT_RUNTIME_METADATA["rock"]
    if (
        object_id.startswith("forage_mushroom")
        or object_id.startswith("wild_herb")
        or object_id.startswith("wildflower_patch")
        or object_id.startswith("reed_patch")
    ):
        return OBJECT_RUNTIME_METADATA["forage"]
    return OBJECT_RUNTIME_METADATA["default"]


def seasonal_sources(object_id: str, source_rect: list[int] | None) -> list[dict]:
    if source_rect is None:
        return []
    if object_id.startswith("oak_tree"):
        names = {
            "spring": "Terrain/trees_spring.png",
            "summer": "Terrain/trees_summer.png",
            "autumn": "Terrain/trees_autumn.png",
            "winter": "Terrain/trees_winter.png",
        }
    elif object_id.startswith("berry_bush") or object_id.startswith("reed_patch"):
        names = {
            "spring": "Terrain/plants_spring.png",
            "summer": "Terrain/plants_summer.png",
            "autumn": "Terrain/plants_autumn.png",
            "winter": "Terrain/plants_winter.png",
        }
    elif object_id.startswith("wild_herb") or object_id.startswith("wildflower_patch"):
        names = {
            "spring": "Terrain/wildflowers_spring.png",
            "summer": "Terrain/wildflowers_summer.png",
            "autumn": "Terrain/wildflowers_autumn.png",
            "winter": "Terrain/wildflowers_winter.png",
        }
    else:
        return []
    return [
        {"season": season, "source": f"assets/source/licensed/lpc_revised/{path}", "sourceRect": source_rect}
        for season, path in names.items()
    ]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_json_gzip(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
    with gzip.open(path, "wb", compresslevel=9) as stream:
        stream.write(raw)


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def classify_family(relative: Path) -> list[str]:
    top = relative.parts[0] if relative.parts else ""
    name = relative.name.lower()
    tags = [top.lower()] if top else []
    if top == "Terrain":
        tags.append("terrain.source")
        if name.startswith("terrain_"):
            tags.extend(["terrain.tileable", "terrain.ground_water", "terrain.seasonal"])
        if name.startswith("cliff_"):
            tags.extend(["terrain.cliff", "terrain.structural_multi_cell"])
        if name in {"rocks, grasslands.png", "rocks, cliffs.png"}:
            tags.extend(["terrain.rock_object", "object.natural"])
        if name == "rocks, cliffs.png":
            tags.append("terrain.cliff_debris")
        if name.startswith("trees_"):
            tags.extend(["terrain.tree", "object.natural", "terrain.seasonal"])
        if name.startswith("plants_"):
            tags.extend(["terrain.plant", "object.natural", "terrain.seasonal"])
        if "flower" in name:
            tags.extend(["terrain.flower", "object.natural"])
        if "mushroom" in name:
            tags.extend(["terrain.mushroom", "object.forage"])
        if name == "tilled_soil.png":
            tags.extend(["terrain.farm", "terrain.tileable"])
        if name == "waterfall.png":
            tags.extend(["terrain.water_feature", "terrain.waterfall"])
        if name == "ice-shallows.png":
            tags.extend(["terrain.water_feature", "terrain.ice"])
    elif top == "Objects":
        tags.append("object")
    elif top == "Structure":
        tags.extend(["structure", "tiled.structure"])
    elif top == "Characters":
        tags.append("character")
    elif top == "FX":
        tags.append("fx")
    return sorted(set(tags))


def likely_tileable(relative: Path, width: int, height: int) -> bool:
    text = relative.as_posix().lower()
    return (
        "terrain/" in text
        or "structure/floor" in text
        or "structure/walls" in text
        or "tiling" in text
        or (width % TILE == 0 and height % TILE == 0 and "characters/" not in text)
    )


def independent_cell_placement_allowed(relative: Path) -> bool:
    name = relative.name.casefold()
    return not (
        name.startswith("cliff_")
        or name == "rocks, cliffs.png"
        or name == "waterfall.png"
    )


def modular_use(relative: Path, width: int, height: int) -> str:
    name = relative.name.casefold()
    if name.startswith("cliff_"):
        return "multi_cell_structural_recipe_required"
    if name == "rocks, cliffs.png":
        return "connected_object_components"
    if name == "waterfall.png":
        return "animated_multi_cell_connector_recipe_required"
    return "tileable_or_modular" if likely_tileable(relative, width, height) else "sprite_layer_or_reference"


def non_empty_cell_count(image: Image.Image) -> int:
    alpha = image.getchannel("A") if image.mode == "RGBA" else image.convert("RGBA").getchannel("A")
    columns = image.width // TILE
    rows = image.height // TILE
    count = 0
    for row in range(rows):
        for column in range(columns):
            cell = alpha.crop(
                (
                    column * TILE,
                    row * TILE,
                    (column + 1) * TILE,
                    (row + 1) * TILE,
                )
            )
            if cell.getbbox() is not None:
                count += 1
    return count


def build_slice_catalog() -> dict:
    sheet_records = []
    for path in sorted(LPC_ROOT.rglob("*.png")):
        relative = path.relative_to(LPC_ROOT)
        try:
            image = Image.open(path)
            width, height = image.size
        except Exception:
            continue
        columns = width // TILE
        rows = height // TILE
        if columns == 0 or rows == 0:
            continue
        sheet_records.append(
            {
                "id": "lpc/" + relative.with_suffix("").as_posix().lower().replace(" ", "_"),
                "source": repo_path(path),
                "displayName": relative.with_suffix("").as_posix(),
                "folder": relative.parts[0] if relative.parts else "",
                "imageSize": [width, height],
                "sliceSize": [TILE, TILE],
                "grid": [columns, rows],
                "sliceCount": columns * rows,
                "nonEmptySliceCount": non_empty_cell_count(image.convert("RGBA")),
                "rectRule": "rect = [column * 32, row * 32, 32, 32]",
                "families": classify_family(relative),
                "likelyTileable": likely_tileable(relative, width, height),
                "modularUse": modular_use(relative, width, height),
                "independentCellPlacementAllowed": independent_cell_placement_allowed(relative),
            }
        )
    return {
        "schema": "havenwild.lpc_slice_catalog.v0_1",
        "updated": now(),
        "sourceRoot": "assets/source/licensed/lpc_revised",
        "source": "https://github.com/ElizaWy/LPC",
        "cellSize": [TILE, TILE],
        "coordinateConvention": "zero-based [column,row] cells; rect = [column*32,row*32,32,32]",
        "purpose": "Editor/runtime bridge for slicing ElizaWy/LPC sheets into addressable 32x32 source cells without writing per-cell files.",
        "rules": {
            "doNotExplodeCellsToDisk": True,
            "promoteByRect": True,
            "compressedCatalog": SLICE_CATALOG_GZ.relative_to(ROOT).as_posix(),
            "compressedLibraryBundle": ASSET_LIBRARY_BUNDLE_GZ.relative_to(ROOT).as_posix(),
            "worldEditorUse": "browse sheets, preview 32x32 cells, promote selected cells into worldgen/autotile/object/stamp manifests",
            "atlasSelectionTool": "click-drag on atlas preview to create a rectangular source-cell selection with live enlarged preview",
            "assemblyCanvas": "drop selected cells onto a snapped canvas to author landmass/autotile seed layouts for PCG",
        },
        "summary": {
            "sheetCount": len(sheet_records),
            "sliceCount": sum(record["sliceCount"] for record in sheet_records),
            "tileableSheetCount": sum(1 for record in sheet_records if record["likelyTileable"]),
        },
        "sheets": sheet_records,
    }


def first_existing(candidates: list[str]) -> Path | None:
    """Resolve exact source paths first, then a case-insensitive equivalent.

    The pinned repository is case-sensitive on Linux but commonly mounted on
    Windows. Catalog bindings must therefore resolve the same source file on
    either platform without guessing a semantically different asset.
    """
    for candidate in candidates:
        path = LPC_ROOT / candidate
        if path.is_file():
            return path

    for candidate in candidates:
        parts = Path(candidate).parts
        cursor = LPC_ROOT
        valid = True
        for part in parts:
            try:
                match = next(
                    (entry for entry in cursor.iterdir() if entry.name.casefold() == part.casefold()),
                    None,
                )
            except OSError:
                match = None
            if match is None:
                valid = False
                break
            cursor = match
        if valid and cursor.is_file():
            return cursor
    return None


_COMPONENT_CACHE: dict[Path, list[tuple[tuple[int, int, int, int], int]]] = {}


def connected_alpha_components(source: Path) -> list[tuple[tuple[int, int, int, int], int]]:
    cached = _COMPONENT_CACHE.get(source)
    if cached is not None:
        return cached

    alpha = Image.open(source).convert("RGBA").getchannel("A")
    width, height = alpha.size
    pixels = alpha.load()
    visited = bytearray(width * height)
    components: list[tuple[tuple[int, int, int, int], int]] = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or pixels[x, y] == 0:
                continue
            queue = deque([(x, y)])
            visited[index] = 1
            min_x = max_x = x
            min_y = max_y = y
            area = 0
            while queue:
                px, py = queue.pop()
                area += 1
                min_x = min(min_x, px)
                max_x = max(max_x, px)
                min_y = min(min_y, py)
                max_y = max(max_y, py)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = px + dx, py + dy
                        if nx < 0 or ny < 0 or nx >= width or ny >= height:
                            continue
                        neighbor = ny * width + nx
                        if visited[neighbor] or pixels[nx, ny] == 0:
                            continue
                        visited[neighbor] = 1
                        queue.append((nx, ny))
            bbox = (min_x, min_y, max_x + 1, max_y + 1)
            box_w = bbox[2] - bbox[0]
            box_h = bbox[3] - bbox[1]
            if area >= 6 and box_w >= 2 and box_h >= 2:
                components.append((bbox, area))

    _COMPONENT_CACHE[source] = components
    return components


_ROCK_COMPONENT_CACHE: dict[Path, list[tuple[tuple[int, int, int, int], int]]] = {}


def rock_alpha_components(source: Path) -> list[tuple[tuple[int, int, int, int], int]]:
    """Extract individual authored rocks without forcing a 32x32 crop.

    Four-connected alpha keeps diagonally adjacent sprites separate while still
    preserving rocks that legitimately span multiple LPC cells. This avoids the
    square fragments created by promoting one cell from the middle of a larger
    rock and avoids merging two neighboring authored rocks into one stamp.
    """
    cached = _ROCK_COMPONENT_CACHE.get(source)
    if cached is not None:
        return cached

    alpha = Image.open(source).convert("RGBA").getchannel("A")
    width, height = alpha.size
    pixels = alpha.load()
    visited = bytearray(width * height)
    components: list[tuple[tuple[int, int, int, int], int]] = []

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if visited[index] or pixels[x, y] == 0:
                continue
            queue = deque([(x, y)])
            visited[index] = 1
            min_x = max_x = x
            min_y = max_y = y
            area = 0
            while queue:
                px, py = queue.pop()
                area += 1
                min_x = min(min_x, px)
                max_x = max(max_x, px)
                min_y = min(min_y, py)
                max_y = max(max_y, py)
                for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                    nx, ny = px + dx, py + dy
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    neighbor = ny * width + nx
                    if visited[neighbor] or pixels[nx, ny] == 0:
                        continue
                    visited[neighbor] = 1
                    queue.append((nx, ny))
            bbox = (min_x, min_y, max_x + 1, max_y + 1)
            box_w = bbox[2] - bbox[0]
            box_h = bbox[3] - bbox[1]
            if area >= 24 and box_w >= 8 and box_h >= 8 and box_w <= 128 and box_h <= 128:
                components.append((bbox, area))

    _ROCK_COMPONENT_CACHE[source] = components
    return components


def rock_variant_components(
    source: Path,
) -> list[tuple[tuple[int, int, int, int], int] | None]:
    """Return four deterministic authored rock variants without inventing size classes.

    The first pass prefers representative small, wide, large, and tall shapes.
    Real LPC sheets do not always contain every one of those silhouettes. Missing
    preference slots are therefore filled from the remaining distinct authored
    components instead of rejecting the entire atlas. Only when a source sheet
    contains fewer than four usable components are existing authored components
    repeated as explicit aliases. Runtime footprint metadata is derived from each
    chosen source rectangle, so a fallback variant never inherits an incorrect
    one-tile or two-tile collision contract.
    """
    candidates = rock_alpha_components(source)
    if not candidates:
        return [None, None, None, None]

    def dimensions(item: tuple[tuple[int, int, int, int], int]) -> tuple[int, int]:
        bbox, _ = item
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    slots = [
        (lambda w, h: w <= TILE and h <= TILE, (24, 24)),
        (lambda w, h: w > TILE and h <= TILE, (56, 28)),
        (lambda w, h: w > TILE and h > TILE, (56, 56)),
        (lambda w, h: h > TILE and w <= TILE, (28, 56)),
    ]
    selected: list[tuple[tuple[int, int, int, int], int] | None] = [None] * len(slots)
    remaining = list(candidates)

    # Prefer the requested silhouette for each runtime slot when one exists.
    for slot_index, (predicate, target) in enumerate(slots):
        matches = [item for item in remaining if predicate(*dimensions(item))]
        if not matches:
            continue
        target_w, target_h = target
        choice = min(
            matches,
            key=lambda item: (
                abs(dimensions(item)[0] - target_w)
                + abs(dimensions(item)[1] - target_h),
                -item[1],
                item[0][1],
                item[0][0],
            ),
        )
        selected[slot_index] = choice
        remaining.remove(choice)

    # A missing silhouette is not a missing asset. Fill it with the closest
    # remaining authored component while keeping every selected source distinct.
    for slot_index, current in enumerate(selected):
        if current is not None or not remaining:
            continue
        target_w, target_h = slots[slot_index][1]
        choice = min(
            remaining,
            key=lambda item: (
                abs(dimensions(item)[0] - target_w)
                + abs(dimensions(item)[1] - target_h),
                -item[1],
                item[0][1],
                item[0][0],
            ),
        )
        selected[slot_index] = choice
        remaining.remove(choice)

    # Runtime currently exposes four stable rock IDs. If a future source sheet
    # provides fewer than four authored components, alias those real components
    # deterministically rather than emitting a transparent object or aborting the
    # build. The manifest records aliases through sourceMode below.
    authored = [item for item in selected if item is not None]
    if authored:
        alias_index = 0
        for slot_index, current in enumerate(selected):
            if current is None:
                selected[slot_index] = authored[alias_index % len(authored)]
                alias_index += 1

    return selected


_GRID_CELL_CACHE: dict[Path, list[tuple[tuple[int, int, int, int], tuple[int, int, int, int], int]]] = {}


def grid_alpha_cells(
    source: Path,
) -> list[tuple[tuple[int, int, int, int], tuple[int, int, int, int], int]]:
    """Return one authored candidate per occupied 32x32 LPC grid cell.

    Nature sheets intentionally place many independent rocks, bushes, flowers,
    reeds, and mushrooms directly beside one another. Connected-component
    extraction merges touching neighboring cells into a single oversized stamp.
    The LPC grid is the authority for these categories, so each occupied cell is
    promoted independently while the occupied sub-rectangle is retained only
    for ranking.
    """
    cached = _GRID_CELL_CACHE.get(source)
    if cached is not None:
        return cached

    alpha = Image.open(source).convert("RGBA").getchannel("A")
    columns = alpha.width // TILE
    rows = alpha.height // TILE
    candidates: list[tuple[tuple[int, int, int, int], tuple[int, int, int, int], int]] = []
    for row in range(rows):
        for column in range(columns):
            left = column * TILE
            top = row * TILE
            cell = alpha.crop((left, top, left + TILE, top + TILE))
            local_bbox = cell.getbbox()
            if local_bbox is None:
                continue
            area = TILE * TILE - cell.histogram()[0]
            occupied = (
                left + local_bbox[0],
                top + local_bbox[1],
                left + local_bbox[2],
                top + local_bbox[3],
            )
            # The promoted source rectangle remains exactly one LPC tile even
            # when the visible pixels occupy only a small part of that tile.
            candidates.append(((left, top, left + TILE, top + TILE), occupied, area))

    _GRID_CELL_CACHE[source] = candidates
    return candidates


def uses_grid_cell_authority(object_id: str) -> bool:
    return object_id.startswith((
        "berry_bush",
        "forage_mushroom",
        "wild_herb",
        "wildflower_patch",
        "reed_patch",
    ))


def component_score(object_id: str, bbox: tuple[int, int, int, int], area: int) -> float:
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if width > 192 or height > 192:
        return -1.0
    compactness = area / max(1, width * height)
    if object_id.startswith("oak_tree"):
        return area + height * 32.0 + width * 5.0
    if object_id == "tree_stump":
        return area + compactness * 1400.0 - abs(height - 24) * 12.0
    if object_id.startswith("berry_bush"):
        return area + compactness * 1800.0 + width * 8.0 - max(0, height - 72) * 15.0
    if object_id.startswith("boulder"):
        aspect_penalty = abs(width - height) * 8.0
        return area + compactness * 2200.0 - aspect_penalty
    if object_id.startswith("forage_mushroom"):
        return area + compactness * 1000.0 - abs(height - 20) * 18.0 - max(0, width - 48) * 20.0
    if (
        object_id.startswith("wild_herb")
        or object_id.startswith("wildflower_patch")
        or object_id.startswith("reed_patch")
    ):
        return area + compactness * 900.0 - abs(height - 24) * 14.0 - max(0, width - 64) * 12.0
    return area + compactness * 500.0


def representative_sprite(
    source: Path | None, object_id: str
) -> tuple[Image.Image, list[int] | None, str]:
    if source is None:
        return Image.new("RGBA", OBJECT_CELL, (0, 0, 0, 0)), None, "missing"
    image = Image.open(source).convert("RGBA")

    if object_id in OBJECT_EXACT_SOURCE_RECTS:
        left, top, width, height = OBJECT_EXACT_SOURCE_RECTS[object_id]
        source_box = (left, top, left + width, top + height)
        source_mode = "lpc_exact_source_rect_native_scale_large_cell"
    elif object_id.startswith("boulder"):
        candidates = rock_variant_components(source)
        rank = OBJECT_VARIANT_RANK.get(object_id, 0)
        selected = candidates[rank] if 0 <= rank < len(candidates) else None
        if selected is None:
            return Image.new("RGBA", OBJECT_CELL, (0, 0, 0, 0)), None, "missing_size_class"
        source_box, _area = selected
        source_mode = (
            "lpc_four_connected_authored_rock_alias"
            if any(previous == selected for previous in candidates[:rank])
            else "lpc_four_connected_authored_rock_component"
        )
    elif uses_grid_cell_authority(object_id):
        grid_candidates = grid_alpha_cells(source)
        if not grid_candidates:
            return Image.new("RGBA", OBJECT_CELL, (0, 0, 0, 0)), None, "missing"
        ranked = sorted(
            grid_candidates,
            key=lambda item: (
                component_score(object_id, item[1], item[2]),
                -item[0][1],
                -item[0][0],
            ),
            reverse=True,
        )
        rank = OBJECT_VARIANT_RANK.get(object_id, 0)
        source_box, _occupied_box, _area = ranked[min(rank, len(ranked) - 1)]
        source_mode = "lpc_32x32_grid_cell_native_scale_large_cell"
    else:
        candidates = connected_alpha_components(source)
        if not candidates:
            return Image.new("RGBA", OBJECT_CELL, (0, 0, 0, 0)), None, "missing"
        ranked = sorted(
            candidates,
            key=lambda item: component_score(object_id, item[0], item[1]),
            reverse=True,
        )
        rank = OBJECT_VARIANT_RANK.get(object_id, 0)
        source_box, _area = ranked[min(rank, len(ranked) - 1)]
        source_mode = "lpc_connected_component_native_scale_large_cell"

    crop = image.crop(source_box)
    scale = min(OBJECT_CELL[0] / crop.width, OBJECT_CELL[1] / crop.height, 1.0)
    if scale < 1.0:
        crop = crop.resize(
            (max(1, round(crop.width * scale)), max(1, round(crop.height * scale))),
            Image.Resampling.NEAREST,
        )
    output = Image.new("RGBA", OBJECT_CELL, (0, 0, 0, 0))
    x = (OBJECT_CELL[0] - crop.width) // 2
    y = OBJECT_CELL[1] - crop.height
    output.alpha_composite(crop, (x, y))
    return (
        output,
        [
            source_box[0],
            source_box[1],
            source_box[2] - source_box[0],
            source_box[3] - source_box[1],
        ],
        source_mode,
    )


def build_object_atlas() -> None:
    rows = (len(OBJECT_IDS) + OBJECT_COLUMNS - 1) // OBJECT_COLUMNS
    atlas = Image.new(
        "RGBA", (OBJECT_COLUMNS * OBJECT_CELL[0], rows * OBJECT_CELL[1]), (0, 0, 0, 0)
    )
    objects = []
    for index, object_id in enumerate(OBJECT_IDS):
        column = index % OBJECT_COLUMNS
        row = index // OBJECT_COLUMNS
        source = first_existing(OBJECT_SOURCE_CANDIDATES.get(object_id, []))
        sprite, source_rect, source_mode = representative_sprite(source, object_id)
        if object_id.startswith(REQUIRED_WORLD_NATURE_PREFIXES) and (
            source is None or source_rect is None
        ):
            raise RuntimeError(
                f"required ElizaWy world-nature asset could not be promoted: {object_id}"
            )
        atlas.alpha_composite(sprite, (column * OBJECT_CELL[0], row * OBJECT_CELL[1]))
        metadata = dict(object_metadata(object_id))
        if object_id.startswith("boulder") and source_rect is not None:
            source_w = source_rect[2]
            source_h = source_rect[3]
            visual_w = max(1, (source_w + TILE - 1) // TILE)
            visual_h = max(1, (source_h + TILE - 1) // TILE)
            metadata["visualFootprintTiles"] = [visual_w, visual_h]
            metadata["collisionFootprintTiles"] = [min(2, visual_w), 1]
        objects.append(
            {
                "id": object_id,
                "index": index,
                "rect": [column * OBJECT_CELL[0], row * OBJECT_CELL[1], *OBJECT_CELL],
                "source": repo_path(source) if source else "",
                "sourceRect": source_rect,
                "sourceMode": source_mode,
                "footAnchor": [OBJECT_CELL[0] // 2, OBJECT_CELL[1]],
                "seasonalSources": seasonal_sources(object_id, source_rect),
                **metadata,
            }
        )
    tree_source_rects = {
        tuple(record["sourceRect"])
        for record in objects
        if record["id"].startswith("oak_tree") and record["sourceRect"] is not None
    }
    if len(tree_source_rects) < 4:
        raise RuntimeError(
            "ElizaWy tree promotion resolved fewer than four distinct authored tree components"
        )

    rock_source_rects = {
        tuple(record["sourceRect"])
        for record in objects
        if record["id"].startswith("boulder") and record["sourceRect"] is not None
    }
    if len(rock_source_rects) < 2:
        raise RuntimeError(
            "ElizaWy rock promotion resolved fewer than two distinct authored rock components"
        )

    OBJECT_ATLAS.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(OBJECT_ATLAS, optimize=False, compress_level=9)
    write_json(
        OBJECT_MANIFEST,
        {
            "id": "havenwild_lpc_objects_160x192_v2",
            "kind": "lpc_natural_scale_object_atlas",
            "output": repo_path(OBJECT_ATLAS),
            "cellWidth": OBJECT_CELL[0],
            "cellHeight": OBJECT_CELL[1],
            "columns": OBJECT_COLUMNS,
            "rows": rows,
            "sourceRoot": "assets/source/licensed/lpc_revised",
            "objects": objects,
            "revision": OBJECT_REVISION_ID,
            "notes": [
                "ElizaWy trees are preserved at natural LPC scale inside large transparent cells; the whole source sheet is never shrunk into one tile.",
                "Eight tree candidates are promoted as first-class worldgen canopy assets with a one-tile trunk collision and a multi-tile visual footprint.",
                "Bushes, mushrooms, flowers, herbs, and reeds use authored 32x32 LPC grid cells.",
                "Rocks use four-connected authored alpha components: multi-cell rocks remain intact, diagonal neighbors remain separate, and square cell fragments are rejected.",
                "Existing ElizaWy nature art has no procedural-circle or colored-rectangle runtime fallback; missing bindings remain visible diagnostics in logs/catalog validation.",
                "Source rectangles and seasonal counterparts remain recorded for editor preview, attribution, footprint review, and seasonal swaps.",
            ],
        },
    )
    for legacy in (LEGACY_OBJECT_ATLAS, LEGACY_OBJECT_MANIFEST):
        if legacy.exists():
            legacy.unlink()
    OBJECT_REVISION.write_text(OBJECT_REVISION_ID + "\n", encoding="utf-8")


def build_editor_metadata(slice_catalog: dict) -> None:
    top_records = [
        ("lpc_terrain", "Terrain", "terrain.tileable", "Terrain sheets and authored autotile/stamp regions"),
        ("lpc_objects", "Objects", "object", "Furniture, moveable objects, wall items, and small items"),
        ("lpc_structure", "Structure", "structure", "Floors, walls, doors, roofs, fences, and building parts"),
        ("lpc_characters", "Characters", "character", "Layered character body, clothing, hair, head, and props"),
        ("lpc_fx", "FX", "fx", "Effects and animation source sheets"),
    ]
    source_record = {
        "id": "elizawy_lpc",
        "displayName": "ElizaWy/LPC",
        "author": "Eliza Wyatt (DeathsDarling), Lanea Zimmerman (Sharm), LPC contributors",
        "officialSourceUrl": "https://github.com/ElizaWy/LPC",
        "uploadedArchives": ["assets/source/licensed/lpc_revised"],
        "licenseStatus": "oga_by_3_0_attribution_required",
        "commercialRuntimePolicy": "allowed_with_attribution",
        "publicRepoPolicy": "allowed_with_attribution",
        "rawAssetPolicy": "vendored_pinned_source_allowed",
        "rawQuarantinePath": "assets/reference_quarantine/third_party/elizawy_lpc",
        "processedPrototypePath": "assets/generated/lpc",
        "candidateFamilies": [record[2] for record in top_records],
        "recommendedUse": "primary project-wide runtime/editor art foundation; route through the ElizaWy domain catalogs, then promote by explicit source rects and authored LPC roles",
        "prohibitedUse": "do not guess runtime semantics from filenames alone; review footprints/autotile roles before promotion",
        "notes": ["Pinned source is mirrored under assets/source/licensed/lpc_revised."],
    }
    write_json(
        EXTERNAL_SOURCES,
        {
            "schema": "havenwild.external_asset_sources.v0_1",
            "updated": now(),
            "purpose": "LPC-only source registry for Havenwild runtime/editor art.",
            "sources": [source_record],
        },
    )
    donor_records = []
    for donor_id, folder, family, description in top_records:
        matching = [
            sheet
            for sheet in slice_catalog["sheets"]
            if sheet["folder"].lower() == folder.lower()
        ]
        donor_records.append(
            {
                "id": donor_id,
                "externalSourceId": "elizawy_lpc",
                "displayName": f"LPC {folder}",
                "catalogRole": description,
                "tileGridProfiles": [[32, 32], [64, 64] if folder == "Characters" else [32, 64]],
                "scaleAdapterModes": ["native_32x32_slice", "promote_by_source_rect"],
                "families": sorted({family, *[tag for sheet in matching[:64] for tag in sheet["families"]]}),
                "referenceUsePolicy": "project_source_allowed_with_attribution",
                "prototypeIngestPolicy": "runtime_candidate_from_pinned_lpc_source",
                "editorVisibility": {
                    "standaloneEditor": "visible",
                    "inGameEditorDevMode": "visible",
                    "litePixelEditorPanel": "visible_as_slice_browser",
                    "runtimeGameDefault": "optional_runtime_after_promotion",
                },
                "pixelEditorReferenceMode": "slice_and_promote_exact_cells",
                "runtimeRestrictions": ["requires explicit semantic binding before worldgen/autotile runtime use"],
                "notes": [
                    f"{len(matching)} sheet(s) indexed in {SLICE_CATALOG.relative_to(ROOT).as_posix()}",
                    "World editor should preview source cells, then write promoted runtime bindings.",
                ],
            }
        )
    write_json(
        DONOR_CATALOG,
        {
            "schema": "havenwild.donor_reference_asset_catalog.v0_1",
            "updated": now(),
            "purpose": "LPC source groups exposed to the in-game Art tab and future world-editor slice tool.",
            "rules": {
                "runtimePromotion": "promote exact cells/rects into generated manifests",
                "sourceOfTruth": "content/assets/lpc/lpc_slice_catalog_v0_1.json",
            },
            "records": donor_records,
        },
    )
    write_json(
        ASSET_CATALOG,
        {
            "schema": "havenwild.asset_catalog.v0_1",
            "updated": now(),
            "purpose": "Unified LPC-only asset catalog indexes.",
            "primaryAuthority": repo_path(PROJECT_AUTHORITY),
            "indexes": [
                {"id": "elizawy_project_authority", "kind": "project_asset_authority", "path": repo_path(PROJECT_AUTHORITY), "editorUse": "project_asset_root"},
                {"id": "elizawy_repository_audit", "kind": "source_audit_summary", "path": repo_path(PROJECT_AUDIT_SUMMARY), "editorUse": "source_coverage_status"},
                *[
                    {
                        "id": f"elizawy_{domain_id}",
                        "kind": "elizawy_domain_catalog",
                        "path": repo_path(PROJECT_DOMAIN_CATALOG_ROOT / f"{domain_id}.json"),
                        "editorUse": "domain_asset_browser",
                    }
                    for domain_id in (
                        "terrain", "nature", "objects", "structure", "characters", "fx",
                        "palette", "reference_scenes", "repository_support", "legal_and_documentation"
                    )
                ],
                {"id": "external_sources", "kind": "source_registry", "path": repo_path(EXTERNAL_SOURCES), "editorUse": "asset_source_status"},
                {"id": "donor_reference", "kind": "donor_catalog", "path": repo_path(DONOR_CATALOG), "editorUse": "art_tab_rows"},
                {"id": "lpc_slice_catalog", "kind": "slice_catalog", "path": repo_path(SLICE_CATALOG), "editorUse": "slice_browser_source"},
                {"id": "lpc_slice_catalog_compressed", "kind": "compressed_slice_catalog", "path": repo_path(SLICE_CATALOG_GZ), "editorUse": "portable_asset_library"},
                {"id": "lpc_asset_library_bundle", "kind": "compressed_asset_library", "path": repo_path(ASSET_LIBRARY_BUNDLE_GZ), "editorUse": "reuse_in_other_projects"},
                {"id": "prototype_queue", "kind": "prototype_queue", "path": repo_path(IMPORT_QUEUE), "editorUse": "compatibility_stub"},
            ],
            "editorContracts": {
                "sliceTool": "select sheet -> inspect 32x32 cells -> promote cells into terrain/object/stamp/autotile manifests",
                "sliceToolInteractions": {
                    "atlasPreview": "click and drag to select source cells",
                    "selectionPreview": "show enlarged selected-cell rectangle and source rect metadata",
                    "assemblyCanvas": "place selected cells on a snapped canvas to author tileable patches/landmass stamps",
                    "pcgAssist": "export assembled patches as worldgen seed masks or autotile validation fixtures"
                },
                "worldEditorMap": "world map should consume scene/world manifests and redraw after scene mutations",
            },
        },
    )
    write_json(
        PIXEL_WORKBENCH,
        {
            "schema": "havenwild.pixel_editor_reference_workbench.v0_1",
            "updated": now(),
            "purpose": "LPC slice/promotion workbench contract for the Art tab and future world editor mode.",
            "defaultMode": "slice_promote",
            "allowedReferenceActions": ["inspect_32x32_cell", "copy_source_rect_metadata", "promote_exact_cell_to_runtime_manifest"],
            "blockedActions": ["trace_restricted_asset_pixels"],
            "tileSetTemplates": [
                {"id": "worldgen_terrain_32", "tileSize": [32, 32], "target": "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json", "sourceReferenceFamilies": ["terrain.tileable"]},
                {"id": "object_sprite_natural_scale", "tileSize": [160, 192], "target": "assets/generated/havenwild_lpc_objects_160x192_v2.json", "sourceReferenceFamilies": ["object", "structure", "terrain.tree"]},
            ],
            "catalogPath": repo_path(DONOR_CATALOG),
        },
    )
    write_json(
        IMPORT_QUEUE,
        {
            "schema": "havenwild.prototype_asset_import_queue.v0_1",
            "updated": now(),
            "purpose": "LPC source is already vendored; queue records runtime promotion targets.",
            "defaultImportMode": "promote_from_pinned_lpc_source",
            "entries": [
                {
                    "id": "lpc_runtime_promotions",
                    "externalSourceId": "elizawy_lpc",
                    "status": "ready",
                    "sourceArchiveNames": ["assets/source/licensed/lpc_revised"],
                    "candidateFamilies": ["terrain.tileable", "object", "structure", "character"],
                    "targetOutputs": ["assets/generated/lpc", "assets/generated/worldgen_v0_1"],
                    "runtimeUse": "allowed_with_attribution",
                    "notes": "Generated by Promote-LpcRuntimeAssets.py",
                }
            ],
        },
    )
    write_json(
        IMPORT_INSTRUCTIONS,
        {
            "schema": "havenwild.asset_local_import_instructions.v0_1",
            "updated": now(),
            "purpose": "LPC source is already mirrored locally.",
            "rules": {"preferredMode": "promote_from_assets/source/licensed/lpc_revised"},
            "records": [
                {
                    "externalSourceId": "elizawy_lpc",
                    "displayName": "ElizaWy/LPC",
                    "localImportStatus": "candidate_ready_from_pinned_source",
                    "preferredWorkspaceImportPath": "assets/source/licensed/lpc_revised",
                    "preferredQuarantinePath": "assets/reference_quarantine/third_party/elizawy_lpc",
                    "acceptedInputFiles": ["Terrain/terrain_summer.png", "Characters/Body/Body 02 - Masculine, Thin/Tan/Walk.png"],
                    "acceptedInputNotes": ["Full LPC source tree is mirrored and indexed."],
                    "dryRunCommand": "python tools/automation/assets/Promote-LpcRuntimeAssets.py",
                    "editorDisplay": "show_slice_catalog",
                    "runtimeUseRule": "allowed after explicit semantic binding and attribution",
                    "instruction": "Use the LPC slice catalog to promote exact 32x32 cells into runtime manifests.",
                }
            ],
        },
    )
    write_json(
        REFERENCE_PREVIEWS,
        {
            "schema": "havenwild.asset_reference_preview_catalog.v0_1",
            "updated": now(),
            "purpose": "Preview records for LPC source groups.",
            "rules": {"previewSource": "source sheets under assets/source/licensed/lpc_revised"},
            "records": [
                {
                    "externalSourceId": "elizawy_lpc",
                    "displayName": "ElizaWy/LPC",
                    "previewStatus": "ready",
                    "previewKind": "source_sheet",
                    "safePreviewPath": "assets/source/licensed/lpc_revised/Terrain/terrain_summer.png",
                    "thumbnailPath": "",
                    "contactSheetPath": "docs/assets/previews/havenwild_lpc_terrain_family_foundation_pass90.png",
                    "generatedBy": "Promote-LpcRuntimeAssets.py",
                    "sourcePolicy": "allowed_with_attribution",
                    "editorDisplay": "show_lpc_source_preview",
                    "notes": ["Use slice catalog for exact 32x32 cell selection."],
                }
            ],
        },
    )
    write_json(
        DRY_RUN_REPORT,
        {
            "schema": "havenwild.prototype_asset_bake_dry_run_report.v0_1",
            "dryRunOnly": False,
            "copyRawAssets": False,
            "generateRuntimeAssets": True,
            "adapterCatalogPath": "content/assets/prototype_imports/prototype_asset_import_adapters_v0_1.json",
            "reportPath": repo_path(DRY_RUN_REPORT),
            "entries": [
                {
                    "id": "lpc_runtime_promotions",
                    "adapterId": "lpc_runtime_promotions",
                    "externalSourceId": "elizawy_lpc",
                    "status": "ready",
                    "inputs": [
                        {
                            "archiveName": "assets/source/licensed/lpc_revised",
                            "role": "pinned_lpc_source_tree",
                            "found": True,
                            "checkedPaths": ["assets/source/licensed/lpc_revised"]
                        }
                    ],
                    "outputMetadata": repo_path(SLICE_CATALOG),
                    "outputProcessedAtlas": "assets/generated/lpc",
                    "notes": ["LPC source tree indexed and promotion-ready."],
                }
            ],
            "blockedSourceProbes": [],
            "summary": "ready=1; missing_source=0; refused_blocked=0",
        },
    )


def build_compressed_library(slice_catalog: dict) -> None:
    write_json_gzip(SLICE_CATALOG_GZ, slice_catalog)
    write_json_gzip(
        ASSET_LIBRARY_BUNDLE_GZ,
        {
            "schema": "havenwild.lpc_asset_library_bundle.v0_1",
            "updated": now(),
            "compression": "gzip",
            "sourceRoot": "assets/source/licensed/lpc_revised",
            "portableUse": "copy this bundle plus the pinned LPC source tree into another Havenwild-compatible project",
            "contents": {
                "sliceCatalog": slice_catalog,
                "runtimeAtlases": [
                    "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json",
                    "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json",
                    "assets/generated/havenwild_lpc_objects_160x192_v2.json",
                    "assets/generated/lpc/characters/havenwild_player_walk_64.json"
                ],
                "editorContracts": {
                    "atlasPreviewDragSelect": True,
                    "selectionPreviewWindow": True,
                    "assemblyCanvasForPcg": True,
                    "compressedNotEncrypted": True
                }
            }
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--objects-only",
        action="store_true",
        help="rebuild only the reviewed LPC object atlas without rescanning every source sheet",
    )
    args = parser.parse_args()
    if not LPC_ROOT.is_dir():
        raise FileNotFoundError(f"missing LPC source root: {LPC_ROOT}")
    if args.objects_only:
        build_object_atlas()
        print(f"Wrote {OBJECT_ATLAS.relative_to(ROOT)} at {OBJECT_REVISION_ID}")
        return

    slice_catalog = build_slice_catalog()
    write_json(SLICE_CATALOG, slice_catalog)
    build_object_atlas()
    build_editor_metadata(slice_catalog)
    build_compressed_library(slice_catalog)
    print(
        "Indexed "
        f"{slice_catalog['summary']['sheetCount']} LPC sheet(s), "
        f"{slice_catalog['summary']['sliceCount']} virtual 32x32 slice(s)"
    )
    print(f"Wrote {SLICE_CATALOG.relative_to(ROOT)}")
    print(f"Wrote {SLICE_CATALOG_GZ.relative_to(ROOT)}")
    print(f"Wrote {ASSET_LIBRARY_BUNDLE_GZ.relative_to(ROOT)}")
    print(f"Wrote {OBJECT_ATLAS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
