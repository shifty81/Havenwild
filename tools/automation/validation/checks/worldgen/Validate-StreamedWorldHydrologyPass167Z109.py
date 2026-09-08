#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]

def read(rel):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"missing required file: {rel}")
    return path.read_text(encoding="utf-8")

contract = json.loads(read("content/worldgen/streamed_world_hydrology_authority_v0_1.json"))
if contract.get("schema") != "havenwild.streamed_world_hydrology_authority.v0_1":
    raise SystemExit("unexpected streamed world/hydrology authority schema")
if contract.get("hydrology", {}).get("generated_waterfall_drop_step_levels") != 1:
    raise SystemExit("generated drainage must descend one LPC cliff tier per waterfall layer")

creation = read("crates/haven_world/src/world_creation.rs")
surface = read("crates/haven_world/src/geographic_surface.rs")
hydrology = read("crates/haven_world/src/geographic_hydrology.rs")
chunks = read("crates/haven_world/src/generated_surface_chunks.rs")
streaming = read("crates/haven_game/src/runtime_surface_streaming.rs")
cliffs = read("crates/haven_world/src/elevation_cliff_v2.rs")
wizard = read("crates/haven_game/src/world_creation_wizard.rs")
islands = read("crates/haven_world/src/island_pcg.rs")
client_generation = read("crates/haven_game/src/client_save_generation.rs")

for token in [
    "WorldExtentMode",
    "Endless",
    "WorldDifficultyPreset",
    "Story",
    "Peaceful",
    "Relaxed",
    "Standard",
    "Adventurous",
    "Rugged",
    "Harsh",
    "Wild",
    "Custom",
    "65_536",
    "waterfalls_required_at_structural_drops",
]:
    if token not in creation:
        raise SystemExit(f"world creation authority missing token: {token}")

for token in [
    "GEOGRAPHIC_REGION_SIZE_TILES: u32 = 2_048",
    "sample_geographic_surface",
    "starter_mainland_distance",
    "ContinentalFeature",
]:
    if token not in surface:
        raise SystemExit(f"global surface authority missing token: {token}")

for token in [
    "choose_upland_source",
    "choose_sink",
    "structural_levels_are_monotonic",
    "SourcePool",
    "SinkPond",
    "SinkLake",
    "RiverMouth",
    "drainage_features_for_bounds",
    "previous.saturating_sub(level) > 1",
]:
    if token not in hydrology:
        raise SystemExit(f"hydrology authority missing token: {token}")

if "generate_open_ocean_pcg_partition" in streaming:
    raise SystemExit("runtime still synthesizes open-ocean PCG partitions beyond starter rectangles")
if "generate_surface_pcg_partition_with_profile" not in streaming:
    raise SystemExit("runtime PCG expansion is not using global geographic surface generation")
if "GeographicGenerationProfile::from_world_creation" not in streaming:
    raise SystemExit("runtime streaming ignores saved world creation settings")
if "result.request.chunk" not in streaming:
    raise SystemExit("surface job result contract is stale")

if "generate_surface_pcg_partition_with_profile" not in islands:
    raise SystemExit("initial mainland does not use the same geographic sampler as streaming")
if "seed: if landmass_id == 0" not in client_generation:
    raise SystemExit("mainland seed is not preserved for streamed geographic continuity")

if "sample.surface.structural_level" not in chunks:
    raise SystemExit("generated freshwater cannot retain underlying structural levels")
if "GeographicWaterFeatureKind::River" not in chunks:
    raise SystemExit("generated surface is not materializing geographic river features")
if "current.water_kind != WaterKindV1::Ocean" not in cliffs:
    raise SystemExit("freshwater structural drops are not generalized waterfall candidates")

for token in [
    '"Challenge"',
    '"World extent"',
    '"Difficulty preset"',
    "difficulty_tuning",
]:
    if token not in wizard:
        raise SystemExit(f"world creation wizard missing player-facing control: {token}")

print("Pass167Z109 streamed world/hydrology authority validated")
