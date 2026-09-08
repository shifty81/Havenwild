#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
issues = []

world_paint = ROOT / 'crates/haven_world/src/world_paint.rs'
text = world_paint.read_text(encoding='utf-8')
required = [
    'mirror_horizontal: bool',
    'mirror_vertical: bool',
    'mirror_centers',
    'world_paint_mirrored_centers',
    '(MAP_W as i32 - 1) - center_x',
    '(MAP_H as i32 - 1) - center_y',
]
for needle in required:
    if needle not in text:
        issues.append(f'missing world paint mirror token: {needle}')

delta = (ROOT / 'crates/haven_world/src/world_paint_delta.rs').read_text(encoding='utf-8')
for needle in ['mirror_horizontal', 'mirror_vertical', 'mirror_centers']:
    if needle not in delta:
        issues.append(f'paint delta missing {needle}')

game = (ROOT / 'crates/haven_game/src/world_paint_editor_panel.rs').read_text(encoding='utf-8')
draw_path = ROOT / 'crates/haven_game/src/world_paint_editor_draw.rs'
if draw_path.exists():
    game += '\n' + draw_path.read_text(encoding='utf-8')
for needle in ['MirrorH', 'MirrorV', 'KeyCode::H', 'KeyCode::V']:
    if needle not in game:
        issues.append(f'paint editor panel missing {needle}')

brush_contract = json.loads((ROOT / 'content/assets/world_tiles/world_paint_brush_contract_v0_1.json').read_text(encoding='utf-8'))
mirror_modes = {entry.get('id') for entry in brush_contract.get('mirrorModes', [])}
for mode in ['mirror_horizontal', 'mirror_vertical']:
    if mode not in mirror_modes:
        issues.append(f'brush contract missing mirror mode {mode}')

pixel_spec_path = ROOT / 'content/editor/pixel_editor/egui_pixel_editor_host_panel_v0_1.json'
if not pixel_spec_path.exists():
    issues.append('missing egui pixel editor host panel spec')
else:
    spec = json.loads(pixel_spec_path.read_text(encoding='utf-8'))
    if spec.get('uiBackend') != 'egui':
        issues.append('pixel editor host panel uiBackend must be egui')
    if spec.get('canonicalTileSize') != [32, 32]:
        issues.append('pixel editor host panel must lock canonicalTileSize [32,32]')
    tools = set(spec.get('toolsMvp', []))
    for tool in ['mirror_horizontal', 'mirror_vertical', 'grid_realign_preview']:
        if tool not in tools:
            issues.append(f'pixel editor toolsMvp missing {tool}')
    boundary = spec.get('monolithBoundary', {})
    for crate in ['haven_game', 'haven_editor', 'haven_assets', 'haven_world', 'haven_render']:
        if crate not in boundary:
            issues.append(f'pixel editor monolith boundary missing {crate}')

if issues:
    print('WorldPaintMirrorAndPixelEditorV36 FAILED')
    for issue in issues:
        print(f'- {issue}')
    raise SystemExit(1)
print('WorldPaintMirrorAndPixelEditorV36 passed')
