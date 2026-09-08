#!/usr/bin/env python3
"""Static fail-closed certification for H20V2 B1-B9 world-foundation closure."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def data(path: str):
    return json.loads(text(path))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"H20V2 world foundation closure FAILED: {message}")


semantic = text("crates/haven_world/src/semantic_world_bake.rs")
save = text("crates/haven_game/src/client_save_generation.rs")
map_root = text("crates/haven_game/src/runtime_world_map.rs")
map_bake = text("crates/haven_game/src/runtime_world_map_bake.rs")
map_helpers = text("crates/haven_game/src/runtime_world_map_helpers.rs")
generated = text("crates/haven_world/src/generated_surface_chunks.rs")
population = text("crates/haven_world/src/surface_population.rs")
startup = text("crates/haven_game/src/runtime_startup.rs")
stream_root = text("crates/haven_game/src/runtime_surface_streaming.rs")
stream_residency = text("crates/haven_game/src/runtime_surface_streaming_residency.rs")
stream_structural = text("crates/haven_game/src/runtime_surface_streaming_structural.rs")
terrain = text("crates/haven_game/src/runtime_terrain_pass.rs")
draw = text("crates/haven_game/src/runtime_draw.rs")
connectors = text("crates/haven_game/src/runtime_structural_connectors.rs")
coastal = text("crates/haven_world/src/structural_landform_coastal.rs")
cliff_draw = text("crates/haven_game/src/runtime_structural_cliff_draw.rs")
waterfall_draw = text("crates/haven_game/src/runtime_structural_waterfall_draw.rs")
waterfall_owner = text("crates/haven_game/src/runtime_structural_waterfall_owner.rs")
main = text("crates/haven_game/src/main.rs")
city_layout = text("crates/haven_world/src/mainland_features/alderreach_layout.rs")
mainland = text("crates/haven_world/src/mainland_features.rs")
city_instances = text("crates/haven_game/src/client_save_generation_city.rs")
building_runtime = text("crates/haven_game/src/building_instance_runtime.rs")
spec = text("docs/worldgen/H20_WORLD_COMPLETION_AUTHORITY.md")
closure = text("docs/worldgen/H20V2_WORLD_FOUNDATION_CLOSURE.md")

# B1 — finite semantic world bake exists before New Game can claim success.
for marker in (
    "SEMANTIC_WORLD_BAKE_SCHEMA",
    "SEMANTIC_WORLD_BAKE_RELATIVE_PATH",
    "drainage_features_for_bounds",
    "sample_generated_surface_map_code_with_drainage",
    "pub drainage_features: Vec<DrainageFeature>",
    "pub landmarks: Vec<SemanticWorldBakeLandmarkV1>",
):
    require(marker in semantic, f"B1 semantic bake missing {marker}")
require("if geography_profile.finite_world" in save, "B1 New Game does not gate finite bake creation")
require("build_semantic_world_bake_v1" in save, "B1 New Game does not build semantic bake")
require("save_semantic_world_bake_v1_to_path" in save, "B1 New Game does not persist semantic bake")
require("finite world semantic bake could not be constructed" in save, "B1 finite bake does not fail closed")

# B2 — reveal-all consumes persisted truth and visibly distinguishes forests.
require('include!("runtime_world_map_bake.rs")' in map_root, "B2 world-map bake module not registered")
require("load_semantic_world_bake_v1_from_path" in map_bake, "B2 Reveal All does not load saved semantic bake")
require("bake.matches(self.world_seed, profile)" in map_bake, "B2 saved bake is not seed/profile validated")
require("11 => 65" in map_helpers and "11 => Color::" in map_helpers, "B2 forest habitat lacks map priority/color")
require("geographic_forest_habitat" in generated and "11" in generated, "B2/B3 map sampler does not expose forest habitat")

# B3 — streamed ecology uses the same habitat seed as world geography and reports acceptance evidence.
require("populate_pcg_natural_objects_with_habitat_seed" in population, "B3 habitat-seed population authority missing")
require("geographic_forest_habitat(habitat_seed" in population, "B3 forest habitat still uses object/region seed")
require("world_seed," in generated and "populate_pcg_natural_objects_with_habitat_seed" in generated, "B3 streamed PCG does not pass world seed to habitat")
require("forest_habitat_cells" in population and "forest_trees" in population, "B3 forest diagnostics missing")
require("inside {} forest-habitat grass cells" in startup, "B3 runtime ecology diagnostics not surfaced")

# B4 — publication is bounded after worker completion and extreme zoom has a real LOD.
for marker in (
    "pending_hydrology_publish: VecDeque",
    "pending_structural_publish: VecDeque",
    "pending_structural_report",
):
    require(marker in stream_root, f"B4 publication queue missing {marker}")
require("hydrology_published < 2" in stream_residency, "B4 hydrology publication is not frame-bounded")
require("structural_published < 2" in stream_residency, "B4 structural publication is not frame-bounded")
require("publish_deadline = frame_started + 0.0015" in stream_residency, "B4 publication time budget missing")
require("wide_surface_lod = self.camera_zoom <= 0.95" in terrain, "B4 terrain wide-zoom LOD missing")
require("mapped_entry = if wide_surface_lod" in terrain, "B4 wide zoom still resolves mapped tuple detail")
require("surface_actor_visible_at_zoom" in draw, "B4 wide-zoom actor budget missing")
require("ObjectKind::Tree" in draw, "B4 wide zoom must retain tree acceptance silhouettes")

# B5 — only semantic ramp corridor owns traversal/cliff suppression; ladders require straight dry 2+ faces.
for marker in ("RiseRight", "RiseLeft", "corridor: &[(i32, i32)]"):
    require(marker in stream_structural, f"B5 ramp corridor ownership missing {marker}")
require("ladder_host_is_straight_south_face" in connectors, "B5 ladder straight-face certification missing")
require("cell.exposed_edges.0 == haven_world::EdgeMaskV2::SOUTH" in connectors, "B5 angled/corner ladder hosts are not rejected")
require("Returning no hosts here" in coastal and "Vec::new()" in coastal, "B5 shoreline constructed-ladder fallback still active")
require("NaturalVine" in coastal, "B5 water-facing connector policy is not documented in code")

# B6 — waterfall multi-cell source runs have exactly one draw owner.
require('mod runtime_structural_waterfall_draw;' in main, "B6 waterfall draw module not registered")
require("waterfall_connector_is_run_owner" in waterfall_draw, "B6 waterfall draw does not consult run ownership")
require("pub(super) fn waterfall_connector_is_run_owner" in waterfall_owner, "B6 deterministic waterfall owner authority missing")
require("draw_waterfall_connector(\n                        &manifest" in cliff_draw, "B6 south waterfall draw does not receive manifest ownership context")
require("draw_side_waterfall_if_present(&manifest" in cliff_draw, "B6 side waterfall draw does not receive manifest ownership context")

# B7/B8 — Willowmere/harbor are materialized as irregular routes + stone quay + wooden over-water pier.
require("paint_city_streets(&mut self, center: SurfaceCell, seed: u64)" in city_layout, "B8 seeded winding street authority missing")
require("willowmere_lane_offset" in city_layout, "B8 city lanes are still rigid grid-only")
require("naturalize_road_path" in city_layout, "B7 global/local road path naturalization missing")
require("paint_reserved_harbor_surface" in city_layout, "B7 stone harbor surface materializer missing")
require("TileKind::StonePath" in city_layout and "ZoneKind::HarborLot" in city_layout, "B7 harbor quay does not bind stone surface to HarborLot")
require("paint_harbor_pier" in city_layout and "TileKind::Bridge" in city_layout, "B7 wooden over-water pier materializer missing")
require("report.harbor_dock_tiles" in mainland, "B7 harbor pier result is not reported")
require("paint_city_streets(town, seed)" in mainland, "B8 mainland pass does not use seeded winding streets")

# B9 — residential Willowmere IDs resolve to enterable cottage authority; doors start closed; gable filler exists.
require(city_instances.count('"havenwild.estate.starter_cottage"') >= 4, "B9 Willowmere residential entries are not normalized to linked cottage interiors")
require('"pcg.willowmere.house.004", "havenwild.estate.starter_cottage"' in city_instances, "B9 fourth house still uses non-linked tall house recipe")
for path in (
    "content/buildings/recipes/three_level_house_prototype_v1.json",
    "content/buildings/recipes/tavern_standard_three_level_v1.json",
):
    recipe = data(path)
    blob = json.dumps(recipe)
    require('"state": "closed"' in blob, f"B9 {path} exterior door does not start closed")
upgrade_blob = json.dumps(data("content/buildings/recipes/estate_two_story_house_upgrade_v1.json"))
require("gable_fill_peak" in upgrade_blob and "gable_fill_base" in upgrade_blob, "B9 two-story front gable filler missing")
for marker in (
    "RuntimeBuildingDoorAnimation",
    "animation_for_transition",
    "frame_index",
    "set_opening_state",
):
    require(marker in building_runtime, f"B9 shared door animation runtime missing {marker}")

# Source-of-truth normalization: the active completion docs may not reintroduce one-high shoreline ladders.
require("true cliffs begin at Level 2" in spec, "H20 spec does not state Level-2 true-cliff minimum")
require("constructed ladders are reserved for straight, dry Level-2+" in spec, "H20 spec does not lock current ladder policy")
require("one-level shoreline cliffs" not in spec.lower(), "H20 spec still advertises retired one-high shoreline cliffs")
for section in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"):
    require(section in closure, f"closure handoff missing {section}")

print("PASS: H20V2 B1-B9 world foundation closure")
