from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5]
terrain = (root / "crates/haven_game/src/terrain_render.rs").read_text(encoding="utf-8")
runtime = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
hud = (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")

checks = [
    ("draw_tile_transition_overlays" in terrain, "atlas transition pass is missing"),
    ("for cell in &transition_work" in runtime, "runtime does not issue a coherent atlas transition pass"),
    ("draw_surface(" in runtime and "draw_interior_span(" in runtime, "semantic water surface pass is missing"),
    ("TransitionOverlayPass::Water" not in runtime and "draw_water_depth_mask" not in terrain, "obsolete per-cell water depth overlay pass is still active"),
    ("let animation_time = water_budget.animation_time" in runtime, "water animation time is not sampled once per frame"),
    ("V7 authority" in hud, "runtime HUD does not expose V7 authority identity"),
]
errors = [message for ok, message in checks if not ok]
if errors:
    print("Pass 153F validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
print("Pass 153F OK: atlas transitions and flat semantic water render in coherent passes with one animation-time sample per frame")
