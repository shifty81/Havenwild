#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = [
    ROOT / "crates/haven_world/src/continuous_surface.rs",
    ROOT / "crates/haven_game/src/runtime_surface_streaming.rs",
    ROOT / "crates/haven_game/src/runtime_scene_navigation.rs",
    ROOT / "crates/haven_game/src/runtime_surface_streaming_residency.rs",
    ROOT / "content/world/continuous_surface_manifest_v1.json",
]
missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
if missing:
    raise SystemExit("Missing Pass 149D files: " + ", ".join(missing))

manifest = json.loads((ROOT / "content/world/continuous_surface_manifest_v1.json").read_text(encoding="utf-8"))
contract = manifest["runtime_contract"]
assert contract["exterior_edge_transitions"] == "disabled_for_authored_surface_chunks"
assert contract["coordinate_authority"] == "global_world_tile_coordinates"
assert contract["active_window"] == "3x3_chunks"
assert contract["preload_window"] == "5x5_chunk_metadata_ring"
assert contract["authored_chunk_dimensions_tiles"] == [96, 64]

surface = required[0].read_text(encoding="utf-8")
assert "pub struct SurfaceRuntimeState" in surface
assert "pub fn active_window" in surface and "pub fn preload_window" in surface
assert "MAP_W as i32" in surface and "MAP_H as i32" in surface
runtime = required[1].read_text(encoding="utf-8")
residency = (ROOT / "crates/haven_game/src/runtime_surface_streaming_residency.rs").read_text(encoding="utf-8")
assert "try_stream_exterior_position" in residency
assert "Surface chunk render binding refresh" in residency
assert "H20 fail-closed boundary" in residency
assert "Crossed surface" in residency
navigation = required[2].read_text(encoding="utf-8")
assert "try_stream_exterior_position" in navigation
assert "if surface_streaming" in navigation and "return;" in navigation
character = (ROOT / "crates/haven_game/src/character_world_runtime.rs").read_text(encoding="utf-8")
assert "surface_global_tile" in character
print("Pass 149D continuous overworld streaming validation passed")
