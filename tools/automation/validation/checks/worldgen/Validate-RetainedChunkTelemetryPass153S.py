from pathlib import Path

root = Path(__file__).resolve().parents[5]
telemetry = (root / "crates/haven_game/src/render_telemetry.rs").read_text(encoding="utf-8")
terrain = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
entry = (root / "crates/haven_game/src/runtime_performance_snapshot.rs").read_text(encoding="utf-8")
hud = (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")
cache = (root / "crates/haven_game/src/base_terrain_cache.rs").read_text(encoding="utf-8")
required = {
    "telemetry visible chunks": "visible_chunks: Cell<usize>" in telemetry,
    "telemetry retained chunks": "retained_chunks: Cell<usize>" in telemetry,
    "telemetry rebuilt chunks": "base_cache_rebuilt_chunks: Cell<usize>" in telemetry,
    "telemetry rebuilt cells": "base_cache_rebuilt_cells: Cell<usize>" in telemetry,
    "terrain records visible chunk count": "visible_chunk_count" in terrain,
    "terrain records base rebuild report": "base_cache_report.rebuilt_chunks" in terrain,
    "cache reports retained chunk count": "pub fn retained_chunk_count" in cache,
    "structured snapshot fields": "visible_chunks={} retained_chunks={} base_rebuilt_chunks={} base_rebuilt_cells={}" in entry,
    "current pass identity": "Pass 155B" in hud and "PERF_SNAPSHOT pass=" in entry,
}
missing = [name for name, ok in required.items() if not ok]
if missing:
    raise SystemExit("Pass 153S validation failed: " + ", ".join(missing))
print("Pass 153S OK: retained chunk visibility and base-cache rebuild cost are exposed in HUD and structured performance snapshots")
