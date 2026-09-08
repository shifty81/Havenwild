#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
def text(path):
    p=ROOT/path
    if not p.exists():
        errors.append(f'missing {path}')
        return ''
    return p.read_text(encoding='utf-8')
def require(path,*markers):
    s=text(path)
    for marker in markers:
        if marker not in s:
            errors.append(f'{path} missing marker: {marker}')
contract=ROOT/'content/editor/gui/canvas_workspace_overlay_w71_v1.json'
w72d_contract = ROOT/'content/editor/gui/canvas_chrome_alignment_w72d_v1.json'
if w72d_contract.exists():
    require('apps/haven_editor_native/src/app/canvas_layers.rs',
            'W72D locked GUI geometry: Tool Rail is a dedicated left column outside',
            'W72D locked GUI geometry: Layers is the dedicated panel immediately to',
            '+ self.canvas_layer_rail_width()',
            'Layers is a dedicated panel, not text painted over the world')
    require('apps/haven_editor_native/src/app/canvas_view.rs',
            'W72D: [-] [zoom] [+] [1:1] [Frame] is the only zoom/view chrome')
    require('apps/haven_editor_native/src/app/canvas_controller.rs',
            'draw_canvas_view_controls_overlay', 'handle_canvas_view_controls_click')
    if errors:
        print('FAIL: W71 CanvasWorkspace normalization (W72D superseding geometry)')
        for error in errors: print(' -', error)
        sys.exit(1)
    print('PASS: W71 CanvasWorkspace normalization (W72D dedicated Tool/Layers/Canvas geometry recognized)')
    sys.exit(0)
try:
    data=json.loads(contract.read_text(encoding='utf-8'))
    if data.get('schema')!='havenwild.editor.canvas_workspace_overlay.w71.v1':
        errors.append('W71 contract schema mismatch')
except Exception as exc:
    errors.append(f'W71 contract invalid: {exc}')
w72a_contract = ROOT/'content/editor/canvas/true_canvas_overlay_geometry_w72a_v1.json'
if w72a_contract.exists():
    # W72A supersedes W71's last reserved ruler gutter: rulers now overlay the
    # same full canvas surface as Tools/Layers/view controls.
    require('apps/haven_editor_native/src/app/canvas_layers.rs',
            'W72A: rulers are overlays too',
            'canvas_overlay_surface_rect',
            'CANVAS_TOOL_RACK_COMPACT_WIDTH',
            'let x = host.x + tool_visual_w + RAIL_GAP')
else:
    require('apps/haven_editor_native/src/app/canvas_layers.rs',
            'Tool/Layer rails',
            'self.canvas_authoring_ruler_gutter()',
            'CANVAS_TOOL_RACK_COMPACT_WIDTH',
            'let x = host.x + tool_visual_w + RAIL_GAP')
require('apps/haven_editor_native/src/app/canvas_tool_rack.rs',
        'The Tool reveal control always owns the upper-left canvas border',
        'Rect::new(\n                host.x,')
require('apps/haven_editor_native/src/app/canvas_view.rs',
        'canvas_view_control_rect',
        'draw_canvas_view_controls',
        'upper-right corner')
require('apps/haven_editor_native/src/app/canvas_controller.rs',
        'draw_canvas_view_controls_overlay',
        'handle_canvas_view_controls_click',
        'EditorViewportMode::PixelStudio')
require('apps/haven_editor_native/src/app/draw.rs','self.draw_canvas_view_controls_overlay();')
require('apps/haven_editor_native/src/app/input.rs','self.handle_canvas_view_controls_click(mx, my)')
require('apps/haven_editor_native/src/app/pixel_studio.rs',
        'active_document_on_right',
        'Keep both documents in the same visual panes')
require('apps/haven_editor_native/src/app/pixel_studio_render.rs',
        'pixel_split_left_rect',
        'pixel_split_right_rect',
        'click to edit',
        'for mode in [DocumentSplitMode::Single, DocumentSplitMode::Vertical]')
require('apps/haven_editor_native/src/app/pixel_studio_input.rs',
        'Editing companion Pixel document in-place',
        'for mode in [DocumentSplitMode::Single, DocumentSplitMode::Vertical]')
require('apps/haven_editor_native/src/app/workspace_shell.rs',
        'Older persisted horizontal split layouts migrate to the supported mode',
        'self.document_split_mode = DocumentSplitMode::Vertical')
require('crates/haven_ui/src/lib.rs',
        'UiColumn', 'UiScrollState', 'canvas_overlays_reserve_layout')
require('apps/haven_editor_native/src/app/object_inspector.rs',
        'use haven_ui::{UiColumn, UiRect};',
        'Properties uses a common vertical widget flow')
# W71 must not regress to rails participating in document geometry.
layers=text('apps/haven_editor_native/src/app/canvas_layers.rs')
if 'if self.workspace_shell.canvas_tool_rail_collapsed { 0.0 } else { CANVAS_TOOL_RACK_WIDTH }' in layers:
    errors.append('Tool Rail still reserves CanvasWorkspace width')
if 'if self.workspace_shell.canvas_layer_rail_collapsed { 0.0 } else { self.canvas_layer_rail_expanded_width() }' in layers:
    errors.append('Layer Rail still reserves CanvasWorkspace width')
# Pixel UI intentionally exposes only one dual-document orientation.
pixel_input=text('apps/haven_editor_native/src/app/pixel_studio_input.rs')
if 'for mode in [DocumentSplitMode::Single, DocumentSplitMode::Vertical, DocumentSplitMode::Horizontal]' in pixel_input:
    errors.append('Pixel Studio still exposes horizontal split UI')
if errors:
    print('FAIL: W71 CanvasWorkspace overlay/widget normalization')
    for error in errors:
        print(' -', error)
    sys.exit(1)
print('PASS: W71 CanvasWorkspace overlay/widget normalization')
