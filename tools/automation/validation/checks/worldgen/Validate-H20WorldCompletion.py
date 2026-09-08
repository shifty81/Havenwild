#!/usr/bin/env python3
"""Compatibility validator for current H20/H20V2 world-completion authority."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"H20 world completion FAILED: {message}")


profile = text("crates/haven_world/src/geographic_surface.rs")
skeleton = text("crates/haven_world/src/archipelago_skeleton.rs")
generated = text("crates/haven_world/src/generated_surface_chunks.rs")
population = text("crates/haven_world/src/surface_population.rs")
cache = text("crates/haven_save/src/surface_chunk_storage.rs")
features = text("crates/haven_world/src/mainland_features.rs")
save = text("crates/haven_game/src/client_save_generation.rs")
city = text("crates/haven_game/src/client_save_generation_city.rs")
water = text("crates/haven_game/src/water_material.rs")
terrain = text("crates/haven_game/src/runtime_terrain_pass.rs")
world_map = text("crates/haven_game/src/runtime_world_map_bake.rs")
semantic = text("crates/haven_world/src/semantic_world_bake.rs")
spec = text("docs/worldgen/H20_WORLD_COMPLETION_AUTHORITY.md")
closure = text("docs/worldgen/H20V2_WORLD_FOUNDATION_CLOSURE.md")

# H20A: finite plan remains the live geography authority.
for marker in (
    "finite_world: bool",
    "finite_world_dimensions_tiles",
    "major_landmass_count",
    "ArchipelagoSkeleton::for_geographic_profile",
):
    require(marker in profile, f"geographic profile/sampler missing {marker}")
require("major_landmass_count.clamp(3, 15)" in profile, "requested major-landmass range is not locked to 3-15")
require("for_geographic_profile" in skeleton, "ArchipelagoSkeleton is not live geographic authority")
require("production_maximum_fifteen_major_landmasses_remains_placeable" in skeleton, "15-major placement test missing")
require("finite_archipelago_samples_every_requested_major_landmass_center_as_land" in profile, "major-landmass center sampler test missing")

# H20B/H20V2 B3: deterministic ecology runs on streamed partitions and shares world habitat seed.
require("populate_pcg_natural_objects_with_habitat_seed" in generated, "streamed PCG ecology does not use habitat-seed authority")
require("natural_object_density_for_region(region)" in generated, "PCG streamed ecology is not region-aware")
require("geographic_forest_habitat(habitat_seed" in population, "forest habitat is not keyed to the world seed authority")
require("scene.zone_at(x, y) != ZoneKind::None" in population, "reserved settlement/harbor zones do not protect against ecology")
require("minimum_partition_tree_count" in population and "minimum_trees" in population, "streamed ecology lacks deterministic per-partition tree visibility floor")
require("SURFACE_CHUNK_CACHE_VERSION: u32 = 6" in cache, "generated baseline cache version is unexpected")

# H20C/H20V2 B8-B9: Willowmere is physical, save-backed, staggered, and residentially enterable.
require("willowmere_center: Option<[i32; 2]>" in features, "mainland pass does not expose capital center")
require("write_willowmere_worldgen_buildings" in save, "new-world generation does not materialize Willowmere buildings")
require(city.count('"pcg.willowmere.') >= 8, "Willowmere first block has fewer than eight stable building IDs")
require("BuildingPlacementSpace::ContinuousSurface" in city, "Willowmere does not use shared ContinuousSurface building authority")
require(city.count('"havenwild.estate.starter_cottage"') >= 4, "Willowmere residential entries are not normalized to linked cottage interiors")

# H20D: live water remains time animated while retaining LPC/V7 base semantics.
require("resolve_water_surface_sample" in water, "water animation bypasses WaterSurfaceSample authority")
require("animated_water_overlay_profile" in water, "pixel-art water animation profile missing")
require("u_time" in water, "compatibility water shader remains static")
require("draw_animation_overlay_tile" in terrain, "terrain renderer does not submit animated water overlay")
require("water_budget.animation_time" in terrain, "water animation ignores bounded telemetry budget")

# H20E/H20V2 B1-B2: finite world is pre-baked and Reveal All consumes that persisted truth.
for marker in (
    "SEMANTIC_WORLD_BAKE_RELATIVE_PATH",
    "drainage_features_for_bounds",
    "sample_generated_surface_map_code_with_drainage",
):
    require(marker in semantic, f"semantic world bake missing {marker}")
require("build_semantic_world_bake_v1" in save and "save_semantic_world_bake_v1_to_path" in save, "New Game does not persist finite semantic bake")
require("load_semantic_world_bake_v1_from_path" in world_map, "Reveal All does not load the saved semantic world bake")
require("bake.matches(self.world_seed, profile)" in world_map, "Reveal All does not validate bake seed/profile")
require('label: "Willowmere".to_string()' in world_map, "Willowmere is not marked on development map")

# H20F/H20V2 source of truth.
for section in ("H20A", "H20B", "H20C", "H20D", "H20E", "H20F"):
    require(section in spec, f"spec missing {section}")
require("true cliffs begin at Level 2" in spec, "spec does not preserve normalized Level-2 cliff authority")
for section in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"):
    require(section in closure, f"H20V2 closure document missing {section}")

print("PASS: H20 world-completion authority (archipelago + semantic bake + ecology + Willowmere + water + reveal map)")
