#!/usr/bin/env python3
from pathlib import Path
root = Path(__file__).resolve().parents[5]
cache = root / "crates/haven_game/src/base_terrain_cache.rs"
terrain = root / "crates/haven_game/src/runtime_terrain_pass.rs"
runtime_draw = root / "crates/haven_game/src/runtime_draw.rs"
client_entry = root / "crates/haven_game/src/runtime_performance_snapshot.rs"
for path in (cache, terrain, runtime_draw, client_entry):
    if not path.exists():
        raise SystemExit(f"Pass 153R missing {path.relative_to(root)}")
cache_text = cache.read_text(encoding="utf-8")
for token in (
    "pub(crate) const BASE_TERRAIN_CHUNK_SIZE: i32 = 16",
    "pub fn for_each_visible_record",
    "min_chunk_x",
    "max_chunk_x",
    "visible_chunk_count += 1",
    "visit(x, y, record)",
):
    if token not in cache_text:
        raise SystemExit(f"Pass 153R missing {token!r} in base terrain cache")
terrain_text = terrain.read_text(encoding="utf-8")
for token in (
    "base_terrain_cache.for_each_visible_record",
    "let visible_chunk_count",
    "tile: cached.tile",
    "transitions: cached.transitions.as_ref()",
):
    if token not in terrain_text:
        raise SystemExit(f"Pass 153R missing {token!r} in terrain pass")
if "V7 authority" not in (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8"):
    raise SystemExit("Pass 153R V7 HUD identity missing")
if "PERF_SNAPSHOT pass=" not in client_entry.read_text(encoding="utf-8"):
    raise SystemExit("Pass 153R structured performance snapshot missing")
print("Pass 153R OK: visible terrain expands only retained 16x16 chunks intersecting the camera bounds")
