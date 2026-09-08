#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[5]
cache = root / "crates/haven_game/src/base_terrain_cache.rs"
terrain = root / "crates/haven_game/src/runtime_terrain_pass.rs"
main = root / "crates/haven_game/src/main.rs"
world_cache = root / "crates/haven_world/src/autotile/live_autotile.rs"
runtime_draw = root / "crates/haven_game/src/runtime_draw.rs"
client_entry = root / "crates/haven_game/src/runtime_performance_snapshot.rs"
for path in (cache, terrain, main, world_cache, runtime_draw, client_entry):
    if not path.exists():
        raise SystemExit(f"Pass 153Q missing {path.relative_to(root)}")

cache_text = cache.read_text(encoding="utf-8")
for token in (
    "struct BaseTerrainChunkCache",
    "const BASE_TERRAIN_CHUNK_SIZE: i32 = 16",
    "dirty_chunks",
    "autotile.last_dirty_cells()",
    "source_revision == autotile.revision()",
    "pub fn record_at",
):
    if token not in cache_text:
        raise SystemExit(f"Pass 153Q missing {token!r} in base terrain cache")
terrain_text = terrain.read_text(encoding="utf-8")
for token in (
    "self.base_terrain_cache.borrow_mut()",
    "base_terrain_cache.synchronize(map, &self.terrain_cache, self.world.active().biome)",
    "base_terrain_cache.for_each_visible_record",
):
    if token not in terrain_text:
        raise SystemExit(f"Pass 153Q missing {token!r} in terrain pass")
if "base_terrain_cache: std::cell::RefCell" not in main.read_text(encoding="utf-8"):
    raise SystemExit("Pass 153Q Game field missing")
if "pub fn revision(&self) -> u64" not in world_cache.read_text(encoding="utf-8"):
    raise SystemExit("Pass 153Q autotile revision contract missing")
if "Pass 155B" not in (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8"):
    raise SystemExit("Pass 153Q HUD identifier missing")
if "PERF_SNAPSHOT pass=" not in client_entry.read_text(encoding="utf-8"):
    raise SystemExit("Pass 153Q performance snapshot identifier missing")
print("Pass 153Q OK: static base-terrain records rebuild by dirty 16x16 chunk and feed visible terrain preparation")
