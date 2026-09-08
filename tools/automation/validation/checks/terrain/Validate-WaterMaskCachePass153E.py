from pathlib import Path
import sys

root = Path(__file__).resolve().parents[5]
live = (root / "crates/haven_world/src/autotile/live_autotile.rs").read_text(encoding="utf-8")
terrain = (root / "crates/haven_game/src/terrain_render.rs").read_text(encoding="utf-8")
pass_file = (root / "crates/haven_game/src/runtime_terrain_pass.rs").read_text(encoding="utf-8")
hud = (root / "crates/haven_game/src/runtime_diagnostics.rs").read_text(encoding="utf-8")

checks = [
    ("pub water_mask: WaterRenderMask" in live, "resolved autotile cells do not retain V7 water masks"),
    ("water_mask_cells" in live, "autotile sync report does not count retained water masks"),
    ("cached_water_mask" in terrain and "unwrap_or_else" in terrain, "terrain renderer does not consume cached water masks with a safe fallback"),
    ("water_mask: cached.water_mask" in pass_file, "runtime terrain pass does not forward retained water masks"),
    ("cache {} masks / {} rebuilt" in hud, "runtime HUD does not expose water cache diagnostics"),
    ("synchronized_cells_cache_v7_water_masks" in live, "water mask cache regression test is missing"),
]
errors = [message for ok, message in checks if not ok]
if errors:
    print("Pass 153E validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
print("Pass 153E OK: V7 water masks are retained in the dirty-cell autotile cache and runtime diagnostics expose cache rebuild cost")
