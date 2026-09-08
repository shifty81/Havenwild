#!/usr/bin/env python3
"""Compatibility validator for the current H20S/H20V2 seed + structural rules.

The original H20 script encoded the retired one-high shoreline-cliff + ladder
contract. Build.ps1 still calls this stable filename, so keep the entry point but
certify the normalized authority instead of the superseded rule.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"H20 seed/cliff/shore closure FAILED: {message}")


main = text("crates/haven_game/src/main.rs")
bootstrap = text("crates/haven_game/src/game_bootstrap.rs")
stream = text("crates/haven_game/src/runtime_surface_streaming_workers.rs")
cache = text("crates/haven_save/src/surface_chunk_storage.rs")
surface = text("crates/haven_world/src/geographic_surface.rs")
normalization = text("crates/haven_world/src/structural_elevation_normalization.rs")
coastal = text("crates/haven_world/src/structural_landform_coastal.rs")
ramps = text("crates/haven_world/src/structural_landform_ramps.rs")
generated = text("crates/haven_world/src/generated_surface_chunks.rs")
connectors = text("crates/haven_game/src/runtime_structural_connectors.rs")

# Full 64-bit seed remains the shared geography/runtime authority.
require("world_seed: u64," in main, "runtime world seed is not 64-bit")
require("metadata.world_seed as u32" not in bootstrap, "saved world seed is still truncated to u32")
require(".map(|metadata| metadata.world_seed)" in bootstrap, "bootstrap does not retain exact saved seed")
require("generate_streamed_surface_pcg_partition_with_profile" in stream, "surface worker is not using streamed PCG generation")

# Generated baselines are versioned and stale caches fail closed.
require("SURFACE_CHUNK_CACHE_VERSION: u32 = 6" in cache, "generated chunk cache version is unexpected")
require('join("baseline.version")' in cache, "generated chunk baseline version sidecar is missing")
require("baseline_cache_version_is_current" in cache, "stale generated baselines are not rejected")

# H20S structural normalization supersedes the historical shoreline-one-high rule.
require("Level 1 is reserved for a certified authored ramp transition" in surface, "geographic sampler does not reserve Level 1 for ramps")
require("geographic_authority_never_emits_standalone_level_one_cliffs" in surface, "standalone Level-1 geography regression test missing")
for marker in (
    "normalize_partitioned_structural_elevation_v1",
    "certified_ramp_cells",
    "constructed_ladder_allowed_v1",
    "level_drop >= 2 && !receiver_swimmable",
):
    require(marker in normalization, f"structural normalization missing {marker}")
require("Level-2 -> 1 -> 0 corridor" in ramps, "ramp selector is not anchored to the normalized 2->1->0 corridor")
require("choose_shoreline_ladder_hosts" in coastal, "shoreline ladder compatibility entry point missing")
require("Vec::new()" in coastal and "NaturalVine" in coastal, "shoreline constructed ladders do not fail closed for natural vine access")
require("normalize_surface_map_structural_elevation_v1" in generated, "streamed/direct generated surface does not apply structural normalization")
require("Level 1 is reserved for certified ramp paths" in generated, "generated-surface Level-1 regression check missing")
require("ladder_host_is_straight_south_face" in connectors, "runtime ladder host does not certify straight cliff shape")
require("EdgeMaskV2::SOUTH" in connectors, "runtime ladder host is not locked to the current straight south-face artwork")

print("PASS: H20 64-bit seed + H20S Level-2 cliff/ramp/water-facing connector closure")
