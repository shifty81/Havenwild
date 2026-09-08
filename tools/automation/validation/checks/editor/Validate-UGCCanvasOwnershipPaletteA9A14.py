#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[5]
errors=[]

def need(path, tokens=(), forbidden=()):
    p=ROOT/path
    if not p.exists():
        errors.append(f"missing {path}")
        return ""
    text=p.read_text(encoding='utf-8')
    for token in tokens:
        if token not in text: errors.append(f"{path}: missing token {token!r}")
    for token in forbidden:
        if token in text: errors.append(f"{path}: forbidden token remains {token!r}")
    return text

need(Path('apps/haven_editor_native/src/app/mod.rs'), [
    'mod brush_palette_drawer;', 'brush_palette_offset: usize', 'brush_palette_offset: 0',
])
need(Path('apps/haven_editor_native/src/app/canvas_tool_rack.rs'), [
    'A14Y:', 'tool_shelf_source_rect', 'tool_shelf_mode_rect', 'tool_shelf_palette_rect',
    'shared_palette_visible = !self.workspace_shell.shared_palette_visible',
])
need(Path('apps/haven_editor_native/src/app/shared_palette.rs'), [
    'self.draw_canvas_brush_palette(rect)', 'H21-A14Y',
], forbidden=['self.draw_asset_palette(rect)'])
need(Path('apps/haven_editor_native/src/app/brush_palette_drawer.rs'), [
    'draw_canvas_brush_palette', 'COLLISION_CHOICES', 'ATMOSPHERE_CHOICES', 'WEATHER_CHOICES',
    'brush_accepts_asset', 'Semantic choices modify authoring intent',
])
need(Path('apps/haven_editor_native/src/app/brush_authoring.rs'), [
    'never carry a stale source across incompatible brush kinds', 'brush_palette_offset = 0',
])
need(Path('apps/haven_editor_native/src/app/canvas_layers.rs'), [
    'CanvasLayerGroup::Surface', 'CanvasLayerGroup::Content', 'CanvasLayerGroup::Simulation',
    'CanvasLayerGroup::Overrides', '+ self.canvas_layer_rail_width()',
    'Layers is a dedicated panel, not text painted over the world',
    'label: "Visual Overrides"', 'label: "Generated / Derived"',
])
world_ui=need(Path('apps/haven_editor_native/src/app/world_surface_authoring_ui.rs'), [
    'World painting is owned by the left Tool Rail', 'single authority',
    'Properties dock is inspection-only',
])
for stale in ['"Authoring Layer"', '"Global Tool"', '"Active Brush"']:
    if stale in world_ui: errors.append(f'world Properties still exposes duplicate control heading {stale}')
need(Path('docs/editor/H21_A9A14_CANVAS_OWNERSHIP_PALETTE_NORMALIZATION.md'), ['Palette Panel', 'Reuse-first LPC direction'])

try:
    bridge=json.loads((ROOT/'content/editor/authoring/lpc_semantic_bridge_v0_1.json').read_text())
    assert bridge['schema']=='havenwild.editor.lpc_semantic_bridge.v0_1'
    if not bridge['rules']['source_assets_remain_read_only']: errors.append('LPC bridge must keep source assets read-only')
    if 'pcg_approved' not in bridge['approval_states']: errors.append('LPC bridge missing PCG approval state')
    if 'terrain.grass' not in bridge['starter_ids']: errors.append('LPC bridge missing canonical terrain starter ID')
except Exception as e:
    errors.append(f'LPC semantic bridge invalid: {e}')

if errors:
    print('[FAIL] H21 A9-A14 canvas ownership/palette normalization')
    for e in errors: print(' -',e)
    sys.exit(1)
print('[PASS] H21 A9-A14 canvas ownership/palette normalization')
