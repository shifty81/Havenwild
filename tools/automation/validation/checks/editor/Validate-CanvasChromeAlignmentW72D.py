#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def read(rel):
    p=ROOT/rel
    if not p.exists():
        errors.append(f'missing {rel}')
        return ''
    return p.read_text(encoding='utf-8')

contract=ROOT/'content/editor/gui/canvas_chrome_alignment_w72d_v1.json'
try:
    data=json.loads(contract.read_text(encoding='utf-8'))
    if data.get('schema')!='havenwild.editor.canvas_chrome_alignment.w72d.v1':
        errors.append('W72D contract schema mismatch')
except Exception as exc:
    errors.append(f'W72D contract invalid: {exc}')

layers=read('apps/haven_editor_native/src/app/canvas_layers.rs')
for marker in [
    'W72D locked GUI geometry: Tool Rail is a dedicated left column outside',
    'W72D locked GUI geometry: Layers is the dedicated panel immediately to',
    'self.canvas_tool_rack_width()',
    'self.canvas_layer_rail_width()',
    'self.main_viewport_rect()',
    'const RAIL_GAP: f32 = super::editor_theme::metrics::PANEL_GAP;',
]:
    if marker not in layers: errors.append(f'canvas_layers missing marker: {marker}')
controller=read('apps/haven_editor_native/src/app/canvas_controller.rs')
for marker in [
    'W72D locked GUI geometry: Tool Rail and Layers are dedicated sibling',
    'rect.x + left',
    '(rect.w - left).max(1.0)',
    'draw_canvas_view_controls_overlay',
]:
    if marker not in controller: errors.append(f'canvas_controller missing marker: {marker}')
view=read('apps/haven_editor_native/src/app/canvas_view.rs')
for marker in [
    'W72D: [-] [zoom] [+] [1:1] [Frame] is the only zoom/view chrome',
    'upper-right corner',
    'retired compatibility shim',
]:
    if marker not in view: errors.append(f'canvas_view missing marker: {marker}')
rack=read('apps/haven_editor_native/src/app/canvas_tool_rack.rs')
for marker in [
    'visible_tool_entries',
    'visible_tool_button_rect',
    'Tool-specific options are always bottom-anchored',
    'TOOL_GROUP_GAP',
    '[1_u8, 2, 3, 4, 5, 8, 12, 16, 24, 32]',
]:
    if marker not in rack: errors.append(f'canvas_tool_rack missing marker: {marker}')
pixel=read('apps/haven_editor_native/src/app/pixel_studio.rs')
if 'const SIZES: [u8; 10] = [1, 2, 3, 4, 5, 8, 12, 16, 24, 32];' not in pixel:
    errors.append('Pixel brush-size ladder not expanded through 32px')
theme=read('apps/haven_editor_native/src/app/editor_theme.rs')
for marker in ['pub const PANEL_GAP: f32 = 6.0;', 'pub const PANEL_EDGE_INSET: f32 = 1.0;']:
    if marker not in theme: errors.append(f'editor theme missing normalized spacing marker: {marker}')
# Explicitly reject the superseded overlay-width authority.
for bad in [
    'pub(crate) fn canvas_tool_rack_width(&self) -> f32 {\n        0.0',
    'pub(crate) fn canvas_layer_rail_width(&self) -> f32 {\n        0.0',
]:
    if bad in layers: errors.append('superseded overlay rail geometry remains active')
if errors:
    print('FAIL: W72D canvas chrome alignment / zoom integration')
    for error in errors: print(' - '+error)
    sys.exit(1)
print('PASS: W72D canvas chrome alignment / zoom integration')
