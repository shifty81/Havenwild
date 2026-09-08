#!/usr/bin/env python3
"""Build the strict 32x32 world-paint compatibility atlas from generated LPC terrain."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
TILE = 32
OUT_DIR = ROOT / "assets/generated/world_tiles/havenwild_world_environment_test_v0_1"
CONTENT_DIR = ROOT / "content/assets/world_tiles"
ATLAS_REL = (
    "assets/generated/world_tiles/havenwild_world_environment_test_v0_1/"
    "havenwild_world_environment_test_v0_1.png"
)
MANIFEST_REL = "content/assets/world_tiles/havenwild_world_environment_test_v0_1.json"

BASE_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json"
BASE_ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.png"
TRANSITION_MANIFEST = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json"
TRANSITION_ATLAS = ROOT / "assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.png"
ASSET_CATALOG = ROOT / "content/assets/catalog/havenwild_asset_catalog_v0_1.json"

LAYER_STACK = [
    (0, "ground_base", "semantic terrain material", True),
    (10, "water_base", "semantic water material", True),
    (20, "ground_transition_fringe", "terrain boundary fringe", True),
    (30, "water_surface_fx", "water overlays and foam", True),
    (40, "cave_base", "cave floor material", True),
    (50, "cave_wall_face", "cave wall edge material", True),
    (60, "town_surface", "town and paved material", True),
    (70, "indoor_floor", "wood and interior floor material", True),
    (80, "debris_overlay", "small terrain detail overlay", True),
    (90, "collision_footprint", "non-rendering collision mask", False),
    (100, "occlusion_fade_mask", "non-rendering fade mask", False),
    (110, "dev_overlay", "editor visualization overlay", False),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def crop_cell(source: Image.Image, rect: list[int]) -> Image.Image:
    return source.crop((rect[0], rect[1], rect[0] + TILE, rect[1] + TILE))


def base_rects(manifest: dict) -> dict[str, list[int]]:
    return {tile["id"]: tile["rect"] for tile in manifest["tiles"]}


def transition_rects(manifest: dict, group: str) -> list[list[int]]:
    variants = [
        variant
        for variant in manifest["variants"]
        if variant["group"] == group and 0 <= variant["mask4"] <= 15
    ]
    variants.sort(key=lambda variant: variant["mask4"])
    return [variant["rect"] for variant in variants]


def append_record(records: list[dict], sheet: Image.Image, image: Image.Image, meta: dict) -> None:
    index = len(records)
    x = (index % 8) * TILE
    y = (index // 8) * TILE
    sheet.alpha_composite(image, (x, y))
    record_id = meta["id"]
    records.append(
        {
            "id": f"{record_id}_32x32",
            "sourceAtlas": ATLAS_REL,
            "atlasRect": [x, y, TILE, TILE],
            "gridSize": [TILE, TILE],
            "family": meta["family"],
            "layer": meta["layer"],
            "variant": meta.get("variant", ""),
            "autotileRole": meta.get("autotileRole", "base"),
            "supportsSubcellPaint": True,
            "sourceKind": meta.get("sourceKind", "lpc_generated_runtime"),
            "runtimeDefault": meta.get("runtimeDefault", False),
        }
    )


def role_name(mask: int) -> str:
    return f"mask_{mask:02d}"


def build_records() -> tuple[Image.Image, list[dict]]:
    base_manifest = load_json(BASE_MANIFEST)
    transition_manifest = load_json(TRANSITION_MANIFEST)
    base_image = Image.open(BASE_ATLAS).convert("RGBA")
    transition_image = Image.open(TRANSITION_ATLAS).convert("RGBA")
    base = base_rects(base_manifest)

    entries: list[tuple[Image.Image, dict]] = []

    for mask, rect in enumerate(transition_rects(transition_manifest, "sand_bank_over_shallow")):
        entries.append(
            (
                crop_cell(transition_image, rect),
                {
                    "id": f"sand_shoreline_{mask:02d}",
                    "family": "sand",
                    "layer": "ground_transition_fringe",
                    "variant": role_name(mask),
                    "autotileRole": "shoreline",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    sand_cycle = ["sand", "wet_sand", "pebble_shore", "sand"]
    for mask in range(16):
        tile_id = sand_cycle[mask % len(sand_cycle)]
        entries.append(
            (
                crop_cell(base_image, base[tile_id]),
                {
                    "id": f"sand_ground_base_{mask:02d}",
                    "family": "sand",
                    "layer": "ground_base",
                    "variant": role_name(mask),
                    "autotileRole": "base",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    water_cycle = ["water", "shallow_water", "deep_water", "ocean_shallow"]
    for mask in range(16):
        tile_id = water_cycle[mask % len(water_cycle)]
        entries.append(
            (
                crop_cell(base_image, base[tile_id]),
                {
                    "id": f"water_base_{mask:02d}",
                    "family": "water",
                    "layer": "water_base",
                    "variant": role_name(mask),
                    "autotileRole": "base",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    cave_base_cycle = ["cave_floor", "cave_floor", "mountain_rock", "cave_floor"]
    for mask in range(16):
        tile_id = cave_base_cycle[mask % len(cave_base_cycle)]
        entries.append(
            (
                crop_cell(base_image, base[tile_id]),
                {
                    "id": f"cave_base_{mask:02d}",
                    "family": "cave",
                    "layer": "cave_base",
                    "variant": role_name(mask),
                    "autotileRole": "base",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    for mask in range(16):
        tile_id = "cave_wall" if mask % 2 else "cave_floor"
        entries.append(
            (
                crop_cell(base_image, base[tile_id]),
                {
                    "id": f"cave_wall_edge_{mask:02d}",
                    "family": "cave",
                    "layer": "cave_wall_face",
                    "variant": role_name(mask),
                    "autotileRole": "wall_edge",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    paved_cycle = ["brick_floor", "stone_floor", "stone_path", "road"]
    for mask in range(16):
        tile_id = paved_cycle[mask % len(paved_cycle)]
        entries.append(
            (
                crop_cell(base_image, base[tile_id]),
                {
                    "id": f"paved_brick_edge_{mask:02d}",
                    "family": "paved_brick",
                    "layer": "town_surface",
                    "variant": role_name(mask),
                    "autotileRole": "edge",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    wood_cycle = ["wood_floor", "plank_floor", "bridge", "wood_floor"]
    for mask in range(16):
        tile_id = wood_cycle[mask % len(wood_cycle)]
        entries.append(
            (
                crop_cell(base_image, base[tile_id]),
                {
                    "id": f"wood_plank_edge_{mask:02d}",
                    "family": "wood_plank",
                    "layer": "indoor_floor",
                    "variant": role_name(mask),
                    "autotileRole": "edge",
                    "runtimeDefault": mask == 0,
                },
            )
        )

    rows = math.ceil(len(entries) / 8)
    sheet = Image.new("RGBA", (8 * TILE, rows * TILE), (0, 0, 0, 0))
    records: list[dict] = []
    for image, meta in entries:
        append_record(records, sheet, image, meta)
    return sheet, records


def write_contract() -> None:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    contract = {
        "schema": "havenwild.world_tile_contract.v0_1",
        "updated": now,
        "purpose": "LPC-backed strict 32x32 compatibility contract for client world-paint rendering.",
        "canonicalTileSize": [32, 32],
        "runtimeCanonicalBakeSize": [32, 32],
        "supportedDonorGridSizes": [[32, 32], [16, 16], [8, 8], [4, 4]],
        "subcellMasks": [
            {"id": "subcell_16", "cellSize": [16, 16], "grid": [2, 2], "purpose": "quarter-cell painting"},
            {"id": "subcell_8", "cellSize": [8, 8], "grid": [4, 4], "purpose": "sixteenth-cell painting"},
            {"id": "subcell_4", "cellSize": [4, 4], "grid": [8, 8], "purpose": "fine mask painting"},
        ],
        "environmentFamiliesV1": ["sand", "water", "cave", "paved_brick", "wood_plank"],
        "layerStackV1": [
            {"order": order, "id": layer_id, "authority": authority, "rendered": rendered}
            for order, layer_id, authority, rendered in LAYER_STACK
        ],
        "brushModesV1": ["cell", "subcell", "line", "rectangle", "fill"],
        "namingRules": {
            "baseTilePattern": "{family}_{layer}_{variant}_32x32",
            "transitionPattern": "{family}_{role}_{mask}_32x32",
            "overlayPattern": "{family}_{layer}_{variant}_overlay_32x32",
            "strictCase": "lower_snake_case",
            "allowedSuffix": "_32x32",
        },
        "multiplayerRules": {
            "storeSemanticMaterial": True,
            "doNotStoreAtlasRectAsAuthority": True,
            "resolveOnClientFromManifest": True,
        },
    }
    (CONTENT_DIR / "world_tile_contract_v0_1.json").write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )


def write_manifest(sheet: Image.Image, records: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    png_path = OUT_DIR / "havenwild_world_environment_test_v0_1.png"
    sheet.save(png_path)
    manifest = {
        "schema": "havenwild.world_tile_atlas_manifest.v0_1",
        "id": "havenwild_world_environment_test_v0_1",
        "updated": now,
        "purpose": "LPC-derived strict 32x32 atlas used by live world-paint render bindings.",
        "canonicalTileSize": [32, 32],
        "sourceAtlas": ATLAS_REL,
        "sourceImageSize": [sheet.width, sheet.height],
        "columns": sheet.width // TILE,
        "rows": sheet.height // TILE,
        "sourcePolicy": "derived_from_pinned_lpc_generated_terrain",
        "runtimeDefault": True,
        "records": records,
    }
    (CONTENT_DIR / "havenwild_world_environment_test_v0_1.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def update_asset_catalog() -> None:
    catalog = load_json(ASSET_CATALOG)
    indexes = catalog.setdefault("indexes", [])
    wanted = {
        "world_tile_contract": {
            "id": "world_tile_contract",
            "kind": "world_tile_contract",
            "path": "content/assets/world_tiles/world_tile_contract_v0_1.json",
            "editorUse": "world_paint_contract",
        },
        "world_environment_test_tiles": {
            "id": "world_environment_test_tiles",
            "kind": "world_tile_atlas_manifest",
            "path": MANIFEST_REL,
            "editorUse": "world_paint_render_bindings",
        },
    }
    by_id = {entry.get("id"): entry for entry in indexes}
    for key, value in wanted.items():
        if key in by_id:
            by_id[key].update(value)
        else:
            indexes.append(value)
    catalog["updated"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    ASSET_CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sheet, records = build_records()
    write_contract()
    write_manifest(sheet, records)
    update_asset_catalog()
    print(f"Built LPC world-paint environment atlas: {len(records)} records at {ATLAS_REL}")


if __name__ == "__main__":
    main()
