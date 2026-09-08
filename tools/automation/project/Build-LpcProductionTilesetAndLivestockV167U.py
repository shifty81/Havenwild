#!/usr/bin/env python3
"""Build Havenwild's normalized LPC terrain/livestock production registries.

The script intentionally keeps art and simulation separate:
- source art is cataloged by stable IDs, geometry, hashes, and edit policy;
- gameplay rules live in data definitions;
- generated atlases are never treated as authoring sources.
"""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
ANIMAL_ROOT = ROOT / "content/assets/oga_lpc/source/animals/farm_animals"
TERRAIN_ROOT = ROOT / "content/assets/lpc/source/lpc-terrains-v7"
CLIFF_ROOT = ROOT / "content/assets/oga_lpc/source/terrain/cliffs_grass_top"
WATER_PATH = ROOT / "content/assets/oga_lpc/source/terrain/animated_water/wateranimate2.png"
MANIFEST_ROOT = ROOT / "content/assets/oga_lpc/manifests"
LPC_ROOT = ROOT / "content/assets/lpc"
EDITOR_ROOT = ROOT / "content/editor"
PREVIEW_PATH = ROOT / "docs/assets/previews/lpc_production_assets_v167u.png"

DIRECTIONS = ["north", "west", "south", "east"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def alpha_bbox(image: Image.Image) -> list[int] | None:
    box = image.getchannel("A").getbbox()
    return list(box) if box else None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def animal_catalog() -> dict[str, Any]:
    species_layouts = {
        "chicken": {"cell": [32, 32], "shadow_cell": [32, 32], "footprint": [1, 1], "render_tiles": [1, 1]},
        "cow": {"cell": [128, 128], "shadow_cell": [128, 128], "footprint": [2, 1], "render_tiles": [4, 4]},
        "llama": {"cell": [128, 128], "shadow_cell": [128, 128], "footprint": [1, 1], "render_tiles": [4, 4]},
        "pig": {"cell": [128, 128], "shadow_cell": [128, 128], "footprint": [2, 1], "render_tiles": [4, 4]},
        "sheep": {"cell": [128, 128], "shadow_cell": [128, 128], "footprint": [2, 1], "render_tiles": [4, 4]},
    }
    entries: list[dict[str, Any]] = []
    for species, layout in species_layouts.items():
        animations: dict[str, Any] = {}
        for state in ("walk", "eat"):
            path = ANIMAL_ROOT / f"{species}_{state}.png"
            if not path.exists():
                continue
            image = Image.open(path).convert("RGBA")
            cw, ch = layout["cell"]
            frames = []
            for row, direction in enumerate(DIRECTIONS):
                for frame in range(4):
                    rect = [frame * cw, row * ch, cw, ch]
                    crop = image.crop((rect[0], rect[1], rect[0] + cw, rect[1] + ch))
                    frames.append({
                        "direction": direction,
                        "frame": frame,
                        "rect": rect,
                        "alpha_bbox": alpha_bbox(crop),
                        "foot_anchor": [cw // 2, ch - 1],
                    })
            animations[state] = {
                "source": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "sheet_size": list(image.size),
                "cell_size": [cw, ch],
                "directions": DIRECTIONS,
                "frames_per_direction": 4,
                "frame_duration_ms": 180 if state == "walk" else 240,
                "playback": "loop" if state == "walk" else "forward_hold_reverse",
                "frames": frames,
            }
        shadow_path = ANIMAL_ROOT / f"{species}_shadow.png"
        shadow: dict[str, Any] | None = None
        if shadow_path.exists():
            image = Image.open(shadow_path).convert("RGBA")
            scw, sch = layout["shadow_cell"]
            shadow = {
                "source": shadow_path.relative_to(ROOT).as_posix(),
                "sha256": sha256(shadow_path),
                "sheet_size": list(image.size),
                "cell_size": [scw, sch],
                "direction_rows": DIRECTIONS,
                "foot_anchor": [scw // 2, sch - 1],
            }
        elif species in {"pig", "sheep"}:
            shadow = {
                "source_alias": "llama.shadow",
                "policy": "temporary_reviewed_alias",
                "note": "Original pack recommends the llama shadow as the closest supplied base.",
            }
        entries.append({
            "species_id": species,
            "source_submission": "oga.lpc.farm_animals",
            "selected_license": "CC-BY-3.0",
            "author": "Daniel Eddeland (daneeklu)",
            "direction_row_order": DIRECTIONS,
            "world_footprint_tiles": layout["footprint"],
            "render_canvas_tiles": layout["render_tiles"],
            "collision_policy": "metadata_owned_not_alpha_owned",
            "animations": animations,
            "shadow": shadow,
            "runtime_aliases": {
                "idle": f"{species}.walk.south.frame0",
                "move": f"{species}.walk",
                "graze": f"{species}.eat",
            },
            "production_state": "reviewed_source_geometry",
        })
    return {
        "schema": "havenwild.oga_lpc_farm_animals_runtime_catalog.v0_1",
        "tile_size": 32,
        "direction_row_order": DIRECTIONS,
        "rules": {
            "bottom_center_foot_anchor": True,
            "nearest_neighbor_filtering": True,
            "alpha_does_not_define_collision": True,
            "art_does_not_define_gameplay_values": True,
            "missing_animation_falls_back_to_idle": True,
        },
        "species": entries,
    }


def terrain_registry() -> dict[str, Any]:
    tsx_path = TERRAIN_ROOT / "terrain-v7.tsx"
    tree = ET.parse(tsx_path)
    root = tree.getroot()
    tile_w = int(root.attrib["tilewidth"])
    tile_h = int(root.attrib["tileheight"])
    columns = int(root.attrib["columns"])
    terrain_image = TERRAIN_ROOT / root.find("image").attrib["source"]
    types = []
    terrain_types = root.find("terraintypes")
    for index, terrain in enumerate(list(terrain_types) if terrain_types is not None else []):
        tile_id = int(terrain.attrib["tile"])
        x = (tile_id % columns) * tile_w
        y = (tile_id // columns) * tile_h
        name = terrain.attrib["name"]
        category = "water" if name.startswith("Water") else (
            "grass" if name.startswith("Grass") else (
                "snow_ice" if name.startswith("Snow") or name.startswith("Ice") else (
                    "rock" if "Rock" in name or "Stone" in name else "ground"
                )
            )
        )
        types.append({
            "terrain_index": index,
            "tiled_name": name,
            "stable_id": "terrain.lpc_v7." + name.lower().replace("_", "."),
            "category": category,
            "pure_fill_tile_id": tile_id,
            "source_rect": [x, y, tile_w, tile_h],
            "source": terrain_image.relative_to(ROOT).as_posix(),
            "authoring_policy": "source_or_havenwild_override",
            "runtime_policy": "semantic_terrain_resolver_selects_visual",
        })

    cliff_sheets = []
    for material, filename in (
        ("grass", "LPC_cliffs_grass.png"),
        ("dark_dirt", "LPC_cliffs_ddirt.png"),
        ("sand", "LPC_cliffs_sand.png"),
        ("snow", "LPC_cliffs_snow.png"),
    ):
        path = CLIFF_ROOT / filename
        image = Image.open(path).convert("RGBA")
        cliff_sheets.append({
            "stable_id": f"terrain.cliff.lpc.{material}",
            "surface_material": material,
            "source": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "sheet_size": list(image.size),
            "cell_size": [32, 32],
            "columns": image.width // 32,
            "rows": image.height // 32,
            "selection_authority": "elevation_cliff_v2",
            "review_catalog": "content/assets/oga_lpc/manifests/oga_lpc_cliff_cell_catalog_v0_1.json",
        })

    water_image = Image.open(WATER_PATH).convert("RGBA")
    waterfall_frames = []
    for row, y in enumerate((0, 192)):
        for frame, x in enumerate((0, 96, 192, 288)):
            waterfall_frames.append({
                "variant": row,
                "frame": frame,
                "rect": [x, y, 96, 192],
                "source_anchor": [48, 31],
                "destination_anchor": [48, 191],
            })

    return {
        "schema": "havenwild.lpc_production_visual_registry.v0_2",
        "rules": {
            "semantic_world_state_is_authoritative": True,
            "visual_tiles_are_derived": True,
            "generated_atlases_are_read_only": True,
            "third_party_edits_use_havenwild_overrides": True,
            "pixel_filter": "nearest",
        },
        "terrain_v7": {
            "source_tsx": tsx_path.relative_to(ROOT).as_posix(),
            "source_image": terrain_image.relative_to(ROOT).as_posix(),
            "sha256": sha256(terrain_image),
            "tile_size": [tile_w, tile_h],
            "columns": columns,
            "tile_count": int(root.attrib["tilecount"]),
            "terrain_types": types,
        },
        "structural_cliffs": cliff_sheets,
        "animated_water": {
            "stable_id": "terrain.water.animated_waterfalls",
            "source": WATER_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256(WATER_PATH),
            "sheet_size": list(water_image.size),
            "waterfall_frames": waterfall_frames,
            "render_authority": "hydrology_v2_plus_structural_waterfall_query",
            "semantic_mutation": False,
            "production_state": "source_geometry_cataloged_visual_mapping_review_required",
        },
        "livestock_catalog": "content/assets/oga_lpc/manifests/oga_lpc_farm_animals_runtime_catalog_v0_1.json",
    }


def editor_bindings(registry: dict[str, Any], animals: dict[str, Any]) -> dict[str, Any]:
    bindings = []
    for terrain in registry["terrain_v7"]["terrain_types"]:
        bindings.append({
            "semantic_id": terrain["stable_id"] + ".pure_fill",
            "source_path": terrain["source"],
            "source_rect": terrain["source_rect"],
            "asset_kind": "terrain_material",
            "edit_policy": "source_or_override",
            "affected_systems": ["terrain_material_registry", "terrain_atlas", "world_viewport"],
        })
    for sheet in registry["structural_cliffs"]:
        bindings.append({
            "semantic_id": sheet["stable_id"] + ".sheet",
            "source_path": sheet["source"],
            "source_rect": [0, 0, *sheet["sheet_size"]],
            "asset_kind": "structural_cliff_sheet",
            "edit_policy": "source_or_override",
            "affected_systems": ["cliff_visual_binding", "structural_cache_preview", "world_viewport"],
        })
    for species in animals["species"]:
        for state, animation in species["animations"].items():
            bindings.append({
                "semantic_id": f"livestock.{species['species_id']}.{state}",
                "source_path": animation["source"],
                "source_rect": [0, 0, *animation["sheet_size"]],
                "asset_kind": "animated_world_entity",
                "edit_policy": "source_or_override",
                "affected_systems": ["livestock_renderer", "animation_preview", "world_viewport"],
            })
    bindings.append({
        "semantic_id": "terrain.water.animated_waterfalls.sheet",
        "source_path": registry["animated_water"]["source"],
        "source_rect": [0, 0, *registry["animated_water"]["sheet_size"]],
        "asset_kind": "water_effect_sheet",
        "edit_policy": "source_or_override",
        "affected_systems": ["waterfall_renderer", "water_effect_preview", "world_viewport"],
    })
    return {
        "schema": "havenwild.world_asset_edit_bindings.v0_2",
        "rules": {
            "generated_outputs_are_read_only": True,
            "third_party_sources_require_project_override_for_destructive_normalization": True,
            "save_updates_open_viewport": True,
            "large_rebuilds_use_background_jobs": True,
            "overlapping_visuals_require_layer_selection": True,
        },
        "bindings": bindings,
    }


def build_preview(registry: dict[str, Any], animals: dict[str, Any]) -> None:
    canvas = Image.new("RGBA", (1600, 1050), (22, 22, 24, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 14), "Havenwild LPC Production Sources — Pass 167U", fill=(240, 230, 200, 255))

    terrain = Image.open(ROOT / registry["terrain_v7"]["source_image"]).convert("RGBA")
    terrain.thumbnail((500, 500), Image.Resampling.NEAREST)
    canvas.alpha_composite(terrain, (20, 50))
    draw.text((20, 560), "LPC Terrain V7 — semantic materials and transitions", fill=(230, 230, 230, 255))

    x = 550
    y = 50
    for sheet in registry["structural_cliffs"]:
        image = Image.open(ROOT / sheet["source"]).convert("RGBA")
        image = image.resize((288, 216), Image.Resampling.NEAREST)
        canvas.alpha_composite(image, (x, y))
        draw.text((x, y + 220), sheet["surface_material"], fill=(230, 230, 230, 255))
        x += 310
        if x > 1250:
            x = 550
            y += 260

    x = 20
    y = 620
    for species in animals["species"]:
        walk = species["animations"].get("walk")
        if not walk:
            continue
        image = Image.open(ROOT / walk["source"]).convert("RGBA")
        cell_w, cell_h = walk["cell_size"]
        frame = image.crop((0, 2 * cell_h, cell_w, 3 * cell_h))
        frame.thumbnail((160, 160), Image.Resampling.NEAREST)
        canvas.alpha_composite(frame, (x, y))
        draw.text((x, y + 165), species["species_id"], fill=(230, 230, 230, 255))
        x += 200

    water = Image.open(ROOT / registry["animated_water"]["source"]).convert("RGBA")
    water.thumbnail((560, 380), Image.Resampling.NEAREST)
    canvas.alpha_composite(water, (1020, 650))
    draw.text((1020, 1030), "Animated water and waterfall source", fill=(230, 230, 230, 255))
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(PREVIEW_PATH)


def main() -> None:
    animals = animal_catalog()
    registry = terrain_registry()
    write_json(MANIFEST_ROOT / "oga_lpc_farm_animals_runtime_catalog_v0_1.json", animals)
    write_json(LPC_ROOT / "lpc_production_visual_registry_v0_2.json", registry)
    write_json(EDITOR_ROOT / "world_asset_edit_bindings_v0_2.json", editor_bindings(registry, animals))
    build_preview(registry, animals)
    print(f"Wrote {len(animals['species'])} livestock species")
    print(f"Wrote {len(registry['terrain_v7']['terrain_types'])} terrain material bindings")
    print(f"Wrote preview: {PREVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
