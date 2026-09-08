#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"missing required file: {rel}")
    return path.read_text(encoding="utf-8")

contract = json.loads(read("content/worldgen/geographic_world_authority_v0_1.json"))
if contract.get("schema") != "havenwild.geographic_world_authority.v0_1":
    raise SystemExit("unexpected geographic world authority schema")

geo = read("crates/haven_world/src/geographic_landforms.rs")
structural = read("crates/haven_world/src/structural_landform_generation.rs")
highland = read("crates/haven_world/src/highland_generation.rs")
chunks = read("crates/haven_world/src/generated_surface_chunks.rs")
instances = read("crates/haven_world/src/world_instance.rs")
legacy = read("crates/haven_game/src/terrain_generation.rs")
population = read("crates/haven_world/src/surface_population.rs")
lib = read("crates/haven_world/src/lib.rs")

required_geo = [
    "MACRO_CELL_TILES: i32 = 192",
    "sample_geographic_landform",
    "geographic_structural_level",
    "geographic_forest_habitat",
    "FOREST_MACRO_CELL_TILES: i32 = 224",
    "struct BentRidgeFeature",
    "struct RidgeBand",
    "struct RotatedEllipse",
]
for token in required_geo:
    if token not in geo:
        raise SystemExit(f"geographic feature authority missing token: {token}")

if "geological_noise(" in structural:
    raise SystemExit("structural topology still calls geological_noise")
if "dirt_noise" in highland:
    raise SystemExit("highland generation still contains dirt_noise thresholding")
if "map.set(x, y, TileKind::MountainPath)" in highland:
    raise SystemExit("highland generation still paints automatic MountainPath shoulders")
if "geographic_structural_level" not in structural:
    raise SystemExit("structural generation is not consuming geographic landforms")
if "sample_geographic_landform" not in highland:
    raise SystemExit("highland materials are not consuming geographic landforms")
if "set_structural_level(x, y, Some(structural_level))" not in chunks:
    raise SystemExit("on-demand chunks do not persist geographic structural levels")
if "sample.surface.structural_level >= 2" not in chunks and "sample.landform_level >= 2" not in chunks:
    raise SystemExit("on-demand highland material is not geographic-feature driven")
if "geographic_forest_habitat" not in population:
    raise SystemExit("natural population is not consuming bounded geographic forest habitat")
if "geological_noise(" in population:
    raise SystemExit("natural population still thresholds geological noise into forest habitat")
if "TileKind::MountainPath" in legacy.replace(
    "// MountainPath is a traversal/road semantic, not a generic highland\n        // material. Procedural ramps/connectors own it explicitly.",
    "",
):
    raise SystemExit("legacy terrain classifier still generates MountainPath")

for token in [
    "pub enum WorldScope",
    "HomeEstate",
    "pub enum WorldExtent",
    "Endless",
    "pub enum PersistencePolicy",
    "pub struct WorldDescriptor",
]:
    if token not in instances:
        raise SystemExit(f"world instance authority missing token: {token}")

for token in ["pub mod geographic_landforms;", "pub mod world_instance;"]:
    if token not in lib:
        raise SystemExit(f"haven_world module surface missing: {token}")

print("Pass167Z108 geographic world authority validated")
