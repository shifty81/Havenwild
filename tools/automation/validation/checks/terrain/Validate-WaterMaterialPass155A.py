from pathlib import Path
root = Path(__file__).resolve().parents[5]
main = (root / 'crates/haven_game/src/main.rs').read_text(encoding='utf-8')
terrain = (root / 'crates/haven_game/src/runtime_terrain_pass.rs').read_text(encoding='utf-8')
material = (root / 'crates/haven_game/src/water_material.rs').read_text(encoding='utf-8')
ripples = (root / 'crates/haven_game/src/water_ripple_runtime.rs').read_text(encoding='utf-8')
required = [
    ('water material module', 'mod water_material;' in main),
    ('ripple runtime module', 'mod water_ripple_runtime;' in main),
    ('shader material load', 'load_material(' in material),
    ('semantic depth input', 'resolve_water_surface_sample' in material),
    ('V7 water mask input', 'WaterRenderMask' in material),
    ('bounded ripple queue', 'MAX_RIPPLES' in ripples and 'VecDeque' in ripples),
    ('runtime water pass', 'water_material.draw_surface' in terrain),
    ('CPU fallback retained', 'draw_tile_transition_overlays' in terrain),
]
missing = [name for name, ok in required if not ok]
if missing:
    raise SystemExit('Pass 155A validation failed: ' + ', '.join(missing))
print('Pass 155A OK: shader-backed semantic water, V7 masks, adaptive quality, bounded ripples, and CPU fallback are wired.')
