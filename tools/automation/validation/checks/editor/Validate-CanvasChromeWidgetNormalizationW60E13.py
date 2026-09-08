#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(rel):
 p=R/rel
 if not p.is_file(): errors.append('missing '+rel); return ''
 return p.read_text(encoding='utf-8')
render=t('apps/haven_editor_native/src/app/render_helpers.rs')
layers=t('apps/haven_editor_native/src/app/canvas_layers.rs')
rack=t('apps/haven_editor_native/src/app/canvas_tool_rack.rs')
shell=t('apps/haven_editor_native/src/app/workspace_shell.rs')
chrome=t('apps/haven_editor_native/src/app/workspace_chrome.rs')
for m in ['draw_workspace_folder_tab','Active face visually joins the panel/canvas below']:
 if m not in render: errors.append('folder workspace tab missing: '+m)
for m in ['canvas_tool_rail_collapsed','canvas_layer_rail_collapsed','canvas_layer_rail_width']:
 if m not in shell: errors.append('workspace rail persistence missing: '+m)
for m in ['CANVAS_TOOL_RACK_COMPACT_WIDTH','CANVAS_LAYER_RAIL_COMPACT_WIDTH','update_canvas_layer_resize_input','Layers is a dedicated panel, not text painted over the world','+ self.canvas_layer_rail_width()','draw_canvas_layer_rail']:
 if m not in layers: errors.append('canvas rail normalization missing: '+m)
# A14X uses a dedicated fixed-width Layers panel; the old drag-resize grip remains retired.
for retired in ['canvas_layer_resize_grip_rect','draw_layer_resize_grip']:
 if retired in layers: errors.append('retired boxed Layers resize authority restored: '+retired)
if 'RAIL_HEADER_H' not in rack or 'canvas_tool_rail_collapsed' not in rack: errors.append('tool rail collapse UI missing')
if 'for offset in [-5.0_f32, 0.0, 5.0]' not in chrome: errors.append('shared diagonal splitter treatment missing')
try:
 data=json.loads((R/'content/editor/ui/native_editor_widget_contract_w60e13_v1.json').read_text(encoding='utf-8'))
 if data.get('schema')!='havenwild.native_editor_widget_contract.w60e13.v1': errors.append('E13 contract schema mismatch')
except Exception as e: errors.append('E13 contract invalid: '+str(e))
if errors:
 print('FAIL: W60E13 canvas chrome/widget normalization'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E13 canvas chrome/widget normalization')
