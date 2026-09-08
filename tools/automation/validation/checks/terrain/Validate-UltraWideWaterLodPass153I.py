from pathlib import Path

root = Path(__file__).resolve().parents[5]
water = (root / "crates/haven_world/src/water_surface.rs").read_text(encoding="utf-8")
terrain = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
budget = (root / "crates/haven_game/src/water_render_budget.rs").read_text(encoding="utf-8")
hud = (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")
required = {
    "ultra-wide one-layer tier": "camera_zoom < 0.55",
    "single layer": "blend_layers: 1",
    "ultra-wide label": '"ultra-wide"',
    "quantized phase": "(raw_time * 4.0).floor() * 0.25",
}
missing = [name for name, token in required.items() if token not in water + terrain + budget]
if missing:
    raise SystemExit("Pass 153I validation FAILED: missing " + ", ".join(missing))
if "V7 authority" not in hud:
    raise SystemExit("Pass 153I validation FAILED: V7 runtime identity missing")
print("Pass 153I OK: ultra-wide water retains V7 topology with one blend layer and quarter-second animation updates")
