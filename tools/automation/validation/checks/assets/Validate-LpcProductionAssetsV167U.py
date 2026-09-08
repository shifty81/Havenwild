#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    animals = load("content/assets/oga_lpc/manifests/oga_lpc_farm_animals_runtime_catalog_v0_1.json")
    livestock = load("content/gameplay/livestock/livestock_species_v0_1.json")
    registry = load("content/assets/lpc/lpc_production_visual_registry_v0_2.json")
    bindings = load("content/editor/world_asset_edit_bindings_v0_2.json")
    gallery = load("content/worldgen/editor_test_world_asset_galleries_v0_1.json")

    species = {entry["species_id"] for entry in animals["species"]}
    require(species == {"chicken", "cow", "llama", "pig", "sheep"}, f"unexpected animal set: {sorted(species)}")
    require({entry["id"] for entry in livestock["species"]} == species, "livestock gameplay definitions do not match visual catalog")

    for entry in animals["species"]:
        require("walk" in entry["animations"] and "eat" in entry["animations"], f"{entry['species_id']} missing walk/eat")
        for state, animation in entry["animations"].items():
            path = ROOT / animation["source"]
            require(path.exists(), f"missing {path}")
            image = Image.open(path)
            require(list(image.size) == animation["sheet_size"], f"dimension mismatch: {path}")
            require(len(animation["frames"]) == 16, f"{entry['species_id']} {state} must contain 16 mapped frames")

    require(registry["terrain_v7"]["tile_count"] == 2048, "terrain V7 tile count changed")
    require(len(registry["terrain_v7"]["terrain_types"]) >= 30, "terrain material registry incomplete")
    for terrain in registry["terrain_v7"]["terrain_types"]:
        require((ROOT / terrain["source"]).exists(), f"missing terrain source {terrain['source']}")

    binding_ids = [entry["semantic_id"] for entry in bindings["bindings"]]
    require(len(binding_ids) == len(set(binding_ids)), "duplicate world edit binding IDs")
    require(any(item.startswith("livestock.") for item in binding_ids), "livestock edit bindings missing")
    require(any(item.startswith("terrain.lpc_v7.") for item in binding_ids), "terrain V7 edit bindings missing")
    require(gallery["world_id"] == "havenwild_editor_test_world", "gallery must target editor test world")

    print(f"OK {len(species)} LPC livestock species")
    print(f"OK {len(registry['terrain_v7']['terrain_types'])} LPC terrain materials")
    print(f"OK {len(bindings['bindings'])} world-to-Pixel Studio source bindings")
    print(f"OK {len(gallery['galleries'])} test-world gallery sections")


if __name__ == "__main__":
    main()
