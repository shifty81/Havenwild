#!/usr/bin/env python3
"""Validate movement-time streaming is bounded and authored ramp corridors do not leak path fills."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
world_map = (ROOT / "crates/haven_game/src/runtime_world_map_game.rs").read_text(encoding="utf-8")
world_map_state = (ROOT / "crates/haven_game/src/runtime_world_map.rs").read_text(encoding="utf-8")
world_map_helpers = (ROOT / "crates/haven_game/src/runtime_world_map_helpers.rs").read_text(encoding="utf-8")
streaming = (ROOT / "crates/haven_game/src/runtime_surface_streaming.rs").read_text(encoding="utf-8")
residency = (ROOT / "crates/haven_game/src/runtime_surface_streaming_residency.rs").read_text(encoding="utf-8")
terrain_base = (ROOT / "crates/haven_game/src/runtime_terrain_base_draw.rs").read_text(encoding="utf-8")
terrain_pass = (ROOT / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
terrain_scene_surface = (ROOT / "crates/haven_game/src/terrain_scene_surface.rs").read_text(encoding="utf-8")
client_update = (ROOT / "crates/haven_game/src/client_pause_menu.rs").read_text(encoding="utf-8")
structural = (ROOT / "crates/haven_game/src/runtime_surface_streaming_structural.rs").read_text(encoding="utf-8")
continuous = (ROOT / "crates/haven_world/src/continuous_surface.rs").read_text(encoding="utf-8")
build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
errors = []

for marker in [
    "last_capture_sample: Option<(i32, i32)>",
    "last_capture_sample: None",
]:
    if marker not in world_map_state:
        errors.append(f"world-map movement throttle state missing marker: {marker}")

for marker in [
    "capture_active_world_map_chunk_if_moved",
    "capture_active_world_map_chunk_impl(false)",
    "already_explored",
    "world_map_exploration_bytes(&self.world_map.explored_chunks)",
    "queue_surface_background_bytes(path, bytes)",
]:
    if marker not in world_map:
        errors.append(f"movement discovery/background persistence missing marker: {marker}")
if "save_world_map_exploration(" in world_map:
    errors.append("movement world-map capture still performs direct synchronous exploration save")
if "serde_json::to_vec_pretty" in world_map_helpers:
    errors.append("world-map exploration still uses pretty JSON on the movement path")
if "self.capture_active_world_map_chunk_if_moved();" not in residency:
    errors.append("surface maintenance still force-captures the entire reveal radius every tick")

for marker in [
    "SURFACE_PUBLISH_BUDGET_SECONDS: f64 = 0.00075",
    "SURFACE_MAX_PUBLISH_PER_FRAME: usize = 1",
]:
    if marker not in streaming:
        errors.append(f"bounded surface publish cadence missing marker: {marker}")
for marker in [
    "integrated < SURFACE_MAX_PUBLISH_PER_FRAME",
    "hydrology_published < SURFACE_MAX_PUBLISH_PER_FRAME",
    "structural_published < SURFACE_MAX_PUBLISH_PER_FRAME",
]:
    if marker not in residency:
        errors.append(f"surface publish loop not using bounded partition cadence: {marker}")

for marker in [
    "runtime_terrain_presentation_tile",
    "tile != TileKind::MountainPath",
    "surface_authored_ramp_owner(global_x, global_y)",
    "TileKind::Grass",
]:
    if marker not in terrain_base:
        errors.append(f"ramp corridor presentation bridge missing marker: {marker}")
for marker in [
    "surface_authored_ramp_owner(global_x, global_y).is_some()",
    "runtime_terrain_presentation_tile(",
    "global: Some((global_x, global_y))",
]:
    if marker not in terrain_pass:
        errors.append(f"continuous-surface ramp presentation missing marker: {marker}")

# TerrainBaseDrawRequest carries optional global coordinates for streamed-world
# ramp presentation. Retained/local scene surfaces have no global address and
# must initialize the field explicitly so the request contract remains compile-complete.
if "global: None," not in terrain_scene_surface:
    errors.append("retained terrain scene-surface request does not initialize TerrainBaseDrawRequest.global")

if "self.terrain_cache_next_sync_at = now + 0.35;" not in client_update:
    errors.append("fallback terrain-cache polling cadence was not reduced from the 10Hz stutter-prone path")

for marker in [
    "structural_cache",
    ".contains_key(binding.scene_id.as_str())",
    "large development world immediately after the first frame",
]:
    if marker not in structural:
        errors.append(f"bounded ramp-owner cache rebuild missing marker: {marker}")
for marker in [
    ".binary_search_by_key(&chunk, |binding| binding.chunk)",
    "self.binding_for_chunk(chunk)",
]:
    if marker not in continuous:
        errors.append(f"continuous-surface hot chunk lookup missing marker: {marker}")

if "Validate-StreamingCadenceRampPresentationA14AB4.py" not in build:
    errors.append("A14AB4 validator is not registered in Full Quality Gate")

if errors:
    print("A14AB4 Streaming Cadence + Ramp Presentation validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PASS: A14AB4 movement streaming cadence + authored ramp presentation")
