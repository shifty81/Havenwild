#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
errors=[]
w72d = ROOT/'content/editor/gui/canvas_chrome_alignment_w72d_v1.json'
if w72d.exists():
    layers=(ROOT/'apps/haven_editor_native/src/app/canvas_layers.rs').read_text(encoding='utf-8')
    controller=(ROOT/'apps/haven_editor_native/src/app/canvas_controller.rs').read_text(encoding='utf-8')
    view=(ROOT/'apps/haven_editor_native/src/app/canvas_view.rs').read_text(encoding='utf-8')
    font=(ROOT/'apps/haven_editor_native/src/app/editor_text.rs').read_text(encoding='utf-8')
    for marker in ['W72D locked GUI geometry: Tool Rail is a dedicated left column outside',
                   'W72D locked GUI geometry: Layers is the dedicated panel immediately to']:
        if marker not in layers: errors.append('W72D superseding chrome missing: '+marker)
    if 'rect.x + left' not in controller: errors.append('W72D authored canvas inset missing')
    if 'retired compatibility shim' not in view: errors.append('W72D full-width toolbar retirement missing')
    for marker in ['flush', 'populate_font_cache']:
        if marker not in font: errors.append('W72B font barrier lost: '+marker)
    if errors:
        print('FAIL: W72C lineage under W72D locked geometry')
        for error in errors: print(' - '+error)
        sys.exit(1)
    print('PASS: W72C lineage retained; W72D locked Tool/Layers sibling geometry recognized')
    sys.exit(0)
def read(rel):
    p=ROOT/rel
    if not p.exists():
        errors.append(f"missing {rel}")
        return ""
    return p.read_text(encoding="utf-8")
contract=ROOT/'content/editor/canvas/cumulative_infinite_canvas_w72c_v1.json'
try:
    data=json.loads(contract.read_text(encoding='utf-8'))
    if data.get('schema')!='havenwild.editor.cumulative_infinite_canvas.w72c.v1':
        errors.append('W72C contract schema mismatch')
except Exception as exc:
    errors.append(f'W72C contract invalid: {exc}')
controller=read('apps/haven_editor_native/src/app/canvas_controller.rs')
for marker in [
    'W72C: the CanvasWorkspace is the center workspace surface itself.',
    'rect.x + 1.0',
    'rect.y + 1.0',
    '(rect.w - 2.0).max(1.0)',
    '(rect.h - 2.0).max(1.0)',
    'self.canvas_host_rect()',
]:
    if marker not in controller:
        errors.append(f'canvas_controller missing marker: {marker}')
for bad in ['rect.x + 16.0, rect.y + 42.0', 'host.y + 98.0', 'host.y + 62.0']:
    if bad in controller:
        errors.append(f'legacy reserved canvas geometry remains: {bad}')
draw=read('apps/haven_editor_native/src/app/draw.rs')
if 'draw_panel(layout.center_panel, "Canvas")' in draw:
    errors.append('center CanvasWorkspace is still rendered as a titled panel')
for marker in ['W72C: the center is the CanvasWorkspace surface itself.', 'self.draw_canvas_tool_rack();', 'self.draw_canvas_layer_rail();', 'self.draw_canvas_view_controls_overlay();']:
    if marker not in draw:
        errors.append(f'draw.rs missing marker: {marker}')
layers=read('apps/haven_editor_native/src/app/canvas_layers.rs')
for marker in ['canvas_overlay_surface_rect', 'let x = host.x + tool_visual_w + RAIL_GAP']:
    if marker not in layers:
        errors.append(f'canvas_layers missing marker: {marker}')
tools=read('apps/haven_editor_native/src/app/canvas_tool_rack.rs')
for marker in ['The Tool reveal control always owns the upper-left canvas border', 'host.x,']:
    if marker not in tools:
        errors.append(f'canvas_tool_rack missing marker: {marker}')
view=read('apps/haven_editor_native/src/app/canvas_view.rs')
for marker in ['upper-right corner', 'draw_canvas_view_controls', 'canvas_view_control_rect']:
    if marker not in view:
        errors.append(f'canvas_view missing marker: {marker}')
scene=read('apps/haven_editor_native/src/app/draw_scene_views.rs')
for marker in ['W72C: the top-left belongs exclusively to the Tool and Layer overlays.', 'viewport.y + viewport.h - 43.0', 'self.draw_autotile_toolbar(content_host)']:
    if marker not in scene:
        errors.append(f'draw_scene_views missing marker: {marker}')
auto=read('apps/haven_editor_native/src/app/autotile_authoring.rs')
if 'host.y + host.h - 36.0' not in auto:
    errors.append('Scene autotile controls are not bottom-nested')
world=read('apps/haven_editor_native/src/app/world_surface_editor.rs')
for marker in ['W72C: reserve the upper-left of the infinite world canvas', 'viewport.y + viewport.h - 58.0']:
    if marker not in world:
        errors.append(f'world_surface_editor missing marker: {marker}')
pixel=read('apps/haven_editor_native/src/app/pixel_studio_render.rs')
for marker in ['Only the document-tab strip reserves top-level space', 'There is no full-width separator toolbar', 'Tools + Layers overlay the canvas']:
    if marker not in pixel:
        errors.append(f'pixel_studio_render missing marker: {marker}')
# No live workspace is allowed to call the retired full-width canvas toolbar.
for rel in [
    'apps/haven_editor_native/src/app/draw.rs',
    'apps/haven_editor_native/src/app/draw_scene_views.rs',
    'apps/haven_editor_native/src/app/world_surface_editor.rs',
    'apps/haven_editor_native/src/app/scene_bank_workspace.rs',
    'apps/haven_editor_native/src/app/pixel_studio_render.rs',
]:
    if 'draw_canvas_toolbar(' in read(rel):
        errors.append(f'{rel} still calls retired full-width canvas toolbar')
# W72B must survive the cumulative rollup.
font=read('apps/haven_editor_native/src/app/editor_text.rs')
for marker in ['flush', 'populate_font_cache']:
    if marker not in font:
        errors.append(f'editor_text missing W72B font mutation marker: {marker}')
if errors:
    print('FAIL: W72C cumulative infinite canvas normalization')
    for error in errors:
        print(' - '+error)
    sys.exit(1)
print('PASS: W72C cumulative infinite canvas normalization')
