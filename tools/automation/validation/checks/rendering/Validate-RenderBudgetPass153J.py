from pathlib import Path

root = Path(__file__).resolve().parents[3]
checks = {
    "telemetry module": root / "crates/haven_game/src/render_telemetry.rs",
    "terrain pass": root / "crates/haven_game/src/runtime_terrain_pass.rs",
    "runtime HUD": root / "crates/haven_game/src/runtime_diagnostics.rs",
}
for label, path in checks.items():
    if not path.exists():
        raise SystemExit(f"Pass 153J FAILED: missing {label}: {path}")

telemetry = checks["telemetry module"].read_text(encoding="utf-8")
terrain = checks["terrain pass"].read_text(encoding="utf-8")
hud = checks["runtime HUD"].read_text(encoding="utf-8")
required = ["visible_cells", "transition_cells", "estimated_water_primitives", "preparation_millis"]
for token in required:
    if token not in telemetry:
        raise SystemExit(f"Pass 153J FAILED: telemetry missing {token}")
if "terrain_render_telemetry.record" not in terrain:
    raise SystemExit("Pass 153J FAILED: terrain pass does not record actual worklists")
required_hud = ["V7 authority", "water prim", "ms prep", "visible_cells", "water_primitives", "prep_ms"]
for token in required_hud:
    if token not in hud:
        raise SystemExit(f"Pass 153J FAILED: runtime diagnostics missing {token}")
print("Pass 153J OK: runtime diagnostics expose visible cells, transition cells, estimated water primitives, and terrain preparation time")
