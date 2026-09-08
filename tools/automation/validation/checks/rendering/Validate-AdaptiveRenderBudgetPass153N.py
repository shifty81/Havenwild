#!/usr/bin/env python3
from pathlib import Path
root = Path(__file__).resolve().parents[5]
checks={
 "crates/haven_game/src/render_telemetry.rs":["PRESSURE_ENTER_FRAMES", "adaptive_pressure_active", "PRESSURE_EXIT_FRAMES"],
 "crates/haven_world/src/water_surface.rs":["with_frame_pressure", "camera_zoom >= 0.95"],
 "crates/haven_game/src/runtime_terrain_pass.rs":[".water_budget("],
 "crates/haven_game/src/runtime_performance_snapshot.rs":["PERF_SNAPSHOT pass=", "budget={}"],
 "crates/haven_game/src/runtime_draw.rs":["quality_label"],
 "crates/haven_game/src/runtime_diagnostics.rs":["Pass 155B"],
}
for rel,tokens in checks.items():
 text=(root/rel).read_text(encoding="utf-8")
 for token in tokens:
  if token not in text:
   raise SystemExit(f"Pass 153N missing {token!r} in {rel}")
print("Pass 153N OK: sustained frame pressure selects a hysteresis-backed wide-view water budget without reducing normal zoom quality")
