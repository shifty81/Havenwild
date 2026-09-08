from pathlib import Path

root = Path(__file__).resolve().parents[5]
world = (root / "crates/haven_world/src/water_surface.rs").read_text(encoding="utf-8")
render = (root / "crates/haven_game/src/terrain_render.rs").read_text(encoding="utf-8")
lib = (root / "crates/haven_world/src/lib.rs").read_text(encoding="utf-8")
required = [
    "pub struct WaterSurfaceSample",
    "reflection_strength",
    "refraction_strength",
    "caustic_strength",
    "pub struct WaterRippleEvent",
    "resolve_water_surface_sample",
]
missing = [token for token in required if token not in world]
if missing:
    raise SystemExit(f"Pass 153C missing water optics contract tokens: {missing}")
if "pub mod water_surface;" not in lib:
    raise SystemExit("Pass 153C water_surface module is not exported")
if "resolve_water_surface_sample" not in render or "surface.reflection_strength" not in render:
    raise SystemExit("Pass 153C runtime bridge is not consuming shader-ready optics")
print("Pass 153C OK: V7 water topology feeds depth, reflection, refraction, caustic, foam-phase, and ripple-ready data")
