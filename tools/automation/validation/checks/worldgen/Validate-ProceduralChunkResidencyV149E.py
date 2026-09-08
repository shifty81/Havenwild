#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[5]
required = [
    ROOT / "crates/haven_world/src/generated_surface_chunks.rs",
    ROOT / "crates/haven_game/src/runtime_surface_streaming.rs",
    ROOT / "content/world/generated_surface_chunk_policy_v1.json",
]
for path in required:
    if not path.exists():
        raise SystemExit(f"missing Pass 149E file: {path.relative_to(ROOT)}")
policy = json.loads(required[2].read_text(encoding="utf-8"))
assert policy["schema"] == "havenwild.generated_surface_chunk.v1"
assert policy["residency"]["active_window"] == "3x3"
assert policy["residency"]["metadata_window"] == "5x5"
world = required[0].read_text(encoding="utf-8")
runtime = required[1].read_text(encoding="utf-8")
for token in ["generate_surface_chunk", "SurfaceResidencyWindow", "surface_x_", "scene.transitions.clear()"]:
    assert token in world, token
for token in ["generate_surface_chunk", "world.insert_scene", "scene_id_for_chunk", "SurfaceResidencyWindow::refresh"]:
    assert token in runtime, token
print("Pass 149E procedural chunk residency validation passed")
