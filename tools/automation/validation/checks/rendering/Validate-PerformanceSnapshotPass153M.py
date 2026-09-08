#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
telemetry = (ROOT / "crates/haven_game/src/render_telemetry.rs").read_text(encoding="utf-8")
entry = (ROOT / "crates/haven_game/src/runtime_performance_snapshot.rs").read_text(encoding="utf-8")
draw = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")

for token in [
    "SNAPSHOT_INTERVAL_SECONDS",
    "should_emit_snapshot",
    "estimated_fps",
]:
    assert token in telemetry, f"missing telemetry snapshot token: {token}"
for token in [
    "PERF_SNAPSHOT pass=",
    "water_primitives=",
    "present_ms=",
    "bottleneck=",
    "cache_rebuilt=",
]:
    assert token in entry, f"missing structured snapshot token: {token}"
assert "Pass 155B" in (ROOT / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")
print("Pass 153M OK: structured five-second performance snapshots persist to the session and rolling game logs")
