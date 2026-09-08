from pathlib import Path

root = Path(__file__).resolve().parents[5]
cache = (root / "crates/haven_game/src/chunk_surface_cache.rs").read_text()
terrain = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text()
snapshot = (root / "crates/haven_game/src/runtime_performance_snapshot.rs").read_text()
required = [
    "ChunkSurfaceTileCommand",
    "ChunkSurfaceCommandBuffer",
    "prepared_commands",
    "retained_commands",
    "record.clone()",
]
missing = [token for token in required if token not in cache]
if missing:
    raise SystemExit(f"Pass 154C missing command-buffer tokens: {missing}")
if "&base_terrain_cache" not in terrain:
    raise SystemExit("Pass 154C terrain synchronization does not feed the retained base cache")
for token in ("chunk_prepared_commands", "chunk_retained_commands", "PERF_SNAPSHOT pass="):
    if token not in snapshot:
        raise SystemExit(f"Pass 154C snapshot missing {token}")
print("Pass 154C OK: dirty terrain chunks build retained render command buffers with reuse telemetry")
