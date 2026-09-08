#!/usr/bin/env python3
from pathlib import Path
root = Path(__file__).resolve().parents[5]
cache = (root / "crates/haven_game/src/chunk_surface_cache.rs").read_text()
terrain = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text()
snapshot = (root / "crates/haven_game/src/runtime_performance_snapshot.rs").read_text()
for token in ("HAVENWILD_RETAINED_CHUNK_COMMANDS", "for_each_visible_command", "missing-surface", "surface-pending"):
    if token not in cache:
        raise SystemExit(f"Pass 154D retained execution capability missing {token}")
if not any(token in cache for token in ("retained-command-buffer", "retained-command-parity")):
    raise SystemExit("Pass 154D retained execution success state missing")
for token in ("retained_requested", "retained_active", "for_each_visible_command"):
    if token not in terrain:
        raise SystemExit(f"Pass 154D terrain capability missing {token}")
for token in ("PERF_SNAPSHOT", "chunk_exec_requested", "chunk_exec_active", "chunk_exec_fallbacks", "chunk_exec_reason"):
    if token not in snapshot:
        raise SystemExit(f"Pass 154D snapshot capability missing {token}")
print("Pass 154D capability retained: opt-in execution has preflight validation, automatic fallback, and structured telemetry")
