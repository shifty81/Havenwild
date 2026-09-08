from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[5]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

config = read("crates/haven_game/src/runtime_config.rs")
startup = read("crates/haven_game/src/runtime_startup.rs")
streaming = "\n".join([
    read("crates/haven_game/src/runtime_surface_streaming.rs"),
    read("crates/haven_game/src/runtime_surface_streaming_residency.rs"),
    read("crates/haven_game/src/runtime_surface_streaming_structural.rs"),
])
navigation = read("crates/haven_game/src/runtime_scene_navigation.rs")
terrain_pass = read("crates/haven_game/src/runtime_terrain_pass.rs")
continuous = read("crates/haven_world/src/continuous_surface.rs") + "\n" + read("crates/haven_world/src/continuous_surface_tests.rs")
generated = read("crates/haven_world/src/generated_surface_chunks.rs")
island = read("crates/haven_world/src/island_pcg.rs") + "\n" + read("crates/haven_world/src/island_pcg_tests.rs")
coastline = read("crates/haven_world/src/island_coastline.rs")
terrain_contract = read("crates/haven_core/src/terrain_contract.rs")
watering = read("crates/haven_game/src/gameplay_tool_runtime.rs")
game_main = read("crates/haven_game/src/main.rs")
world_lib = read("crates/haven_world/src/lib.rs")
save = read("crates/haven_save/src/lib.rs")
authority = json.loads(read("content/worldgen/open_world_surface_runtime_authority_v0_2.json"))
test_world = json.loads(read("content/worldgen/client_worldgen_test_world_v0_1.json"))

errors = []

def require(text: str, markers, scope: str):
    for marker in markers:
        if marker not in text:
            errors.append(f"missing {scope} marker: {marker}")

require(config, [
    "Err(_) => false",
    '"1" | "true" | "on" | "yes"',
    "The normal client boots the selected persistent PCG world",
], "normal-client startup")
if test_world.get("enabled_by_default") is not False:
    errors.append("certification test world is still enabled by default")
if test_world.get("rules", {}).get("production_pack_is_authoritative_during_worldgen_development") is not False:
    errors.append("certification pack still overrides persistent PCG worlds")

require(island, [
    "Exterior rectangles are storage partitions of one continuous surface",
    "generated_exterior_partitions_have_no_scene_edge_transitions",
    "pcg_surface_scene_id",
], "PCG generation")
if "add_adjacent_scene_transitions" in island or "insert_edge_transition" in island:
    errors.append("PCG generation still emits exterior edge-transfer transitions")

require(continuous, [
    "pub pcg_region: Option<String>",
    "pcg_surface_scene_id(region, chunk)",
    "strip_pcg_exterior_transitions",
    "migrate_legacy_pcg_ocean_domains",
    "legacy_pcg_ocean_migration_keeps_enclosed_pond_fresh",
], "continuous-surface authority")
require(generated, [
    "generate_surface_pcg_partition_with_profile",
    "Missing rectangles are no longer synthesized",
    "same global geography",
], "same-region geographic streaming")
require(world_lib, [
    "generate_open_ocean_pcg_partition",
    "generate_open_ocean_surface_chunk",
], "haven_world public ocean-partition surface")
require(streaming, [
    "generate_surface_pcg_partition_with_profile",
    "active_surface_origin_px",
    "local_world_to_runtime_world",
    "runtime_world_to_active_local",
], "runtime surface streaming")
require(navigation, [
    "storage-partition edge",
    "scene_id_is_surface_partition",
    "runtime_world_to_screen",
], "global exterior navigation")
require(terrain_pass, [
    "active_surface_origin_px",
], "neighbor terrain composition")
if not (
    "draw_loaded_surface_neighbors" in terrain_pass
    or (
        "draw_continuous_surface_terrain" in terrain_pass
        and "one global terrain grid" in terrain_pass
    )
):
    errors.append("missing neighbor/global terrain composition marker")

require(coastline, [
    "TileKind::OceanDeep",
    "TileKind::OceanShallow",
    "generated_coast_uses_marine_shallow_and_deep_semantics",
], "marine PCG coastline")
require(terrain_contract, [
    "pub enum WaterSourceClass",
    "TileKind::OceanShallow | TileKind::OceanDeep => WaterSourceClass::Salt",
    "can_fill_watering_container_from",
    "marine_and_freshwater_share_water_collision_but_not_container_use",
], "water gameplay domain")
require(watering, [
    "Ocean water is salt water and cannot fill the watering can",
    "Filled watering can from fresh",
], "watering-container gameplay")
require(game_main, [
    "water_source_class",
    "WaterSourceClass",
], "haven_game water-domain import surface")
require(island, [
    "fn height_for_tile",
    "fn slug",
], "PCG retained generation helpers")
require(startup, [
    "migrate_legacy_pcg_ocean_domains",
    "strip_pcg_exterior_transitions",
], "saved-world migration")
generation_match = re.search(
    r"CURRENT_CLIENT_GENERATION_VERSION:\s*u32\s*=\s*(\d+)", save
)
if generation_match is None or int(generation_match.group(1)) < 11:
    errors.append("saved-world generation version is below the Z77 minimum of 11")

runtime_rules = authority.get("runtimeRules", {})
for key in [
    "normalClientBootsSelectedPersistentPcgWorld",
    "certificationWorldRequiresExplicitOptIn",
    "loadedNeighborTerrainRendersInOneViewport",
    "exteriorCameraUsesGlobalSurfaceCoordinates",
    "pcgExteriorPartitionsContainNoEdgeTransitions",
    "missingPcgPartitionsSampleSameGeographicField",
    "genericGeneratedLandCannotEnterPcgRegionNamespace",
    "legacyPcgOceanMigrationPreservesEnclosedFreshwater",
]:
    if runtime_rules.get(key) is not True:
        errors.append(f"open-world runtime authority missing true rule: {key}")
terrain_rules = authority.get("terrainPresentationRules", {})
for key in [
    "marineAndFreshwaterUseSameV7DepthTopology",
    "marineWaterRetainsSaltwaterGameplayIdentity",
    "freshwaterOnlyFillsWateringContainers",
]:
    if terrain_rules.get(key) is not True:
        errors.append(f"water authority missing true rule: {key}")

if errors:
    raise SystemExit("Z77 validation failed:\n- " + "\n- ".join(errors))
print("Pass167Z77 seamless PCG surface and marine-water authority validated")
