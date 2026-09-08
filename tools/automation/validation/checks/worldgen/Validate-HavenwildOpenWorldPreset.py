#!/usr/bin/env python3
"""Validate the Havenwild open-world/PCG direction contract.

This intentionally avoids third-party jsonschema dependencies so it can run in a
plain Python install on Windows or CI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
PRESET = ROOT / "content" / "worldgen" / "havenwild_open_world_preset_v1.json"
SCHEMA = ROOT / "content" / "schemas" / "havenwild_open_world_preset.schema.v1.json"
REQUIRED_ANCHORS = {
    "starter_tavern_plot",
    "town_center",
    "city_hall",
    "harbor",
    "starter_cave_entrance",
    "main_road_network",
    "early_forest",
    "early_forage_zone",
    "early_fertile_soil",
}
REQUIRED_INTERIOR_TRANSITIONS = {"interior", "cave", "dungeon", "cellar", "upper_floor"}
REQUIRED_CAVE_REVEALS = {"lower_shaft", "ore_pocket", "side_room"}


def pair(value, label, errors):
    if not isinstance(value, list) or len(value) != 2 or not all(isinstance(v, int) for v in value):
        errors.append(f"{label} must be a two-integer array")
        return (0, 0)
    if value[0] <= 0 or value[1] <= 0:
        errors.append(f"{label} values must be positive")
    return (value[0], value[1])


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not PRESET.exists():
        print(f"FAIL missing preset: {PRESET}")
        return 1
    if not SCHEMA.exists():
        print(f"FAIL missing schema: {SCHEMA}")
        return 1

    preset = json.loads(PRESET.read_text(encoding="utf-8"))
    _schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    if preset.get("schema") != "havenworld.open_world_preset.v1":
        errors.append("schema must be havenworld.open_world_preset.v1")
    if preset.get("game") != "Havenwild":
        errors.append("game must be Havenwild")
    if preset.get("generator_version") != "havenwild.worldgen.v1":
        errors.append("generator_version must be havenwild.worldgen.v1")

    overworld = preset.get("overworld", {})
    if overworld.get("mode") != "continuous_chunked_overworld":
        errors.append("overworld.mode must be continuous_chunked_overworld")
    if overworld.get("outdoor_transitions_allowed") is not False:
        errors.append("outdoor transitions must remain disabled for the open-world surface")

    world_w, world_h = pair(overworld.get("world_size_tiles"), "overworld.world_size_tiles", errors)
    chunk_w, chunk_h = pair(overworld.get("chunk_size_tiles"), "overworld.chunk_size_tiles", errors)
    pair(overworld.get("tile_size_pixels"), "overworld.tile_size_pixels", errors)
    if world_w and chunk_w and world_w < 512:
        errors.append("open-world width must be at least 512 tiles")
    if world_h and chunk_h and world_h < 512:
        errors.append("open-world height must be at least 512 tiles")
    if world_w and chunk_w and world_w % chunk_w != 0:
        warnings.append("world width is not evenly divisible by chunk width")
    if world_h and chunk_h and world_h % chunk_h != 0:
        warnings.append("world height is not evenly divisible by chunk height")

    transitions = set(overworld.get("interior_transition_types", []))
    missing_transitions = sorted(REQUIRED_INTERIOR_TRANSITIONS - transitions)
    if missing_transitions:
        errors.append(f"missing enclosed transition types: {', '.join(missing_transitions)}")

    generation = preset.get("factorio_style_generation", {})
    if generation.get("rerollable_seed") is not True:
        errors.append("factorio_style_generation.rerollable_seed must be true")
    if generation.get("deterministic_chunks") is not True:
        errors.append("factorio_style_generation.deterministic_chunks must be true")
    varied = set(generation.get("varies_per_world", []))
    for required in ["town_layout", "road_network", "resource_distribution", "cave_entrances"]:
        if required not in varied:
            errors.append(f"factorio_style_generation.varies_per_world missing {required}")

    anchors = set(preset.get("required_anchors", []))
    missing_anchors = sorted(REQUIRED_ANCHORS - anchors)
    if missing_anchors:
        errors.append(f"missing required anchors: {', '.join(missing_anchors)}")

    caves = preset.get("caves", {})
    if caves.get("effectively_infinite") is not True:
        errors.append("caves.effectively_infinite must be true")
    if caves.get("weak_spots_enabled") is not True:
        errors.append("caves.weak_spots_enabled must be true")
    if caves.get("lower_shafts_require_rope_ladder") is not True:
        errors.append("caves.lower_shafts_require_rope_ladder must be true")
    reveal_types = set(caves.get("reveal_types", []))
    missing_reveals = sorted(REQUIRED_CAVE_REVEALS - reveal_types)
    if missing_reveals:
        errors.append(f"missing cave reveal types: {', '.join(missing_reveals)}")

    materials = preset.get("materials", {})
    if materials.get("rendering_model") != "texture_material_atlas_plus_overlays":
        errors.append("materials.rendering_model must be texture_material_atlas_plus_overlays")
    if materials.get("shader_role") != "polish_only":
        errors.append("materials.shader_role must remain polish_only")

    for warning in warnings:
        print(f"WARN {warning}")
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    chunks_x = world_w // max(1, chunk_w)
    chunks_y = world_h // max(1, chunk_h)
    print(
        f"PASS Havenwild open-world preset: {world_w}x{world_h} tiles, "
        f"{chunks_x}x{chunks_y} chunks, {len(anchors)} required anchors"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
