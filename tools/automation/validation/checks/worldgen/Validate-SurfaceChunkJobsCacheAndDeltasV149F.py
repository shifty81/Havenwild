#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
required = [
    "crates/haven_world/src/surface_chunk_jobs.rs",
    "crates/haven_save/src/surface_chunk_storage.rs",
    "crates/haven_game/src/runtime_surface_streaming.rs",
    "content/world/surface_chunk_runtime_policy_v1.json",
    "docs/design/SURFACE_CHUNK_JOBS_CACHE_AND_DELTAS_PASS149F.md",
    "PASS149F_HANDOFF.md",
]
missing = [p for p in required if not (ROOT / p).is_file()]
if missing:
    raise SystemExit("Pass 149F missing: " + ", ".join(missing))
policy = json.loads((ROOT / required[3]).read_text(encoding="utf-8"))
assert policy["generation"]["duplicateRequestsCoalesced"] is True
assert policy["residency"]["evictGeneratedOutsidePreload"] is True
assert policy["disk"]["loadOrder"] == ["player_delta", "baseline", "generate"]
jobs = (ROOT / required[0]).read_text(encoding="utf-8")
storage = (ROOT / required[1]).read_text(encoding="utf-8")
runtime = (ROOT / required[2]).read_text(encoding="utf-8")
for token in ["SurfaceChunkJobQueue", "thread::Builder", "pending", "try_receive"]:
    assert token in jobs, token
for token in ["baseline.tworld", "player_delta.tworld", "load_surface_chunk", "atomic_write"]:
    assert token in storage, token
for token in ["update_surface_chunk_jobs", "evict_distant_generated_surface_chunks", "persist_active_generated_chunk_delta"]:
    assert token in runtime, token
main_lines = len((ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8").splitlines())
if main_lines > 459:
    raise SystemExit(f"main.rs architecture ceiling exceeded: {main_lines}/459")
print("Pass 149F surface chunk jobs/cache/delta validation passed")
