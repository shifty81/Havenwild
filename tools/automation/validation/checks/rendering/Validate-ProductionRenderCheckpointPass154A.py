#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
required = {
    "crates/haven_game/src/chunk_render_contract.rs": [
        "ChunkRenderBackend", "PerTileFallback", "RetainedChunkSurface",
        "ChunkSurfaceLifecycleReport", "dirty_surfaces", "fallback_available",
    ],
    "crates/haven_game/src/runtime_performance_snapshot.rs": [
        "PERF_SNAPSHOT pass=", "chunk_backend=", "chunk_dirty_surfaces=",
        "chunk_invalidation=",
    ],
    "crates/haven_game/src/runtime_diagnostics.rs": [
        "renderer_summary", "chunk_summary",
    ],
    "crates/haven_game/src/base_terrain_cache.rs": [
        "render_capability", "surface_lifecycle_report",
        "ChunkSurfaceLifecycleReport::from_base_cache",
    ],
    "crates/haven_game/src/client_entry.rs": [
        "runtime_performance_snapshot::format_performance_snapshot",
    ],
}
for relative, needles in required.items():
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"missing {relative}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"{relative} missing {needle!r}")

draw_lines = len((ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8").splitlines())
if draw_lines > 750:
    raise SystemExit(f"runtime_draw.rs exceeds architecture limit: {draw_lines}")

archive = ROOT / "docs/archive/pass_history"
if not archive.is_dir() or len(list(archive.glob("PASS*.md"))) < 50:
    raise SystemExit("historical pass handoffs were not archived")

print("Pass 154A capability retained: safe per-tile fallback, retained chunk-surface lifecycle contracts, extracted snapshots, and archived pass history are present")
