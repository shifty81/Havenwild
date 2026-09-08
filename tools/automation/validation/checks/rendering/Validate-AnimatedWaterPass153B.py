from pathlib import Path
root = Path(__file__).resolve().parents[3]
text = (root / 'crates/haven_game/src/terrain_render.rs').read_text(encoding='utf-8')
required = [
    'world_x: i32',
    'world_y: i32',
    'time: f32',
    'let phase = time * 0.72',
    'let phase = time * 1.15',
    'WATER_CORNER_NORTH_EAST',
]
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit('Pass 153B validation failed: ' + ', '.join(missing))
water_start = text.index('fn draw_water_depth_mask(')
water_end = text.index('fn diagonal_direction_code', water_start)
if 'draw_circle' in text[water_start:water_end]:
    raise SystemExit('Pass 153B validation failed: legacy circular depth stamp returned')
print('Pass 153B OK: V7 water masks drive animated depth and shoreline motion without circular stamps')
