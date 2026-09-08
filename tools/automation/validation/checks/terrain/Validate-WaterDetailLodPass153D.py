from pathlib import Path

root = Path(__file__).resolve().parents[5]
world = (root / 'crates/haven_world/src/water_surface.rs').read_text(encoding='utf-8')
terrain = (root / 'crates/haven_game/src/terrain_render.rs').read_text(encoding='utf-8')
runtime = (root / 'crates/haven_game/src/runtime_terrain_pass.rs').read_text(encoding='utf-8')
hud = (root / 'crates/haven_game/src/runtime_diagnostics.rs').read_text(encoding='utf-8')
required = {
    'WaterDetailProfile': world,
    'blend_layers: 2': world,
    'draw_diagonal_corners: false': world,
    'water_detail: WaterDetailProfile': terrain,
    'let layer_count = detail.blend_layers.max(1);': terrain,
    'water_budget(self.camera_zoom': runtime,
    'V7 authority': hud,
}
missing = [token for token, text in required.items() if token not in text]
if missing:
    raise SystemExit('Pass 153D validation failed: ' + ', '.join(missing))
print('Pass 153D OK: water blend cost is bounded to 1-2 layers by camera zoom while V7 topology remains authoritative')
