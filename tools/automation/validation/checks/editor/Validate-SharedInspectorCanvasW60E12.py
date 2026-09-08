#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(x): return (R/x).read_text(encoding='utf-8') if (R/x).is_file() else ''
rack=t('apps/haven_editor_native/src/app/canvas_tool_rack.rs'); dock=t('apps/haven_editor_native/src/app/object_inspector.rs'); help=t('apps/haven_editor_native/src/app/editor_help.rs'); right=t('apps/haven_editor_native/src/app/right_dock.rs'); commands=t('apps/haven_editor_native/src/app/command_registry.rs')
if 'if shift { return; }' not in rack: errors.append('plain-vs-Shift shortcut ownership missing')
if 'pub(crate) fn draw_scene_dock' in dock:
 section=dock.split('pub(crate) fn draw_scene_dock',1)[1].split('fn draw_terrain_tuple_inspector',1)[0]
 if '"Tools"' in section: errors.append('Scene right dock still exposes duplicate Tools tab')
for m in ['Properties','Alt+1..9','Shift-modified keys']:
 if m not in (dock+'\n'+right+'\n'+help+'\n'+commands): errors.append('missing E12 UI/help '+m)
mp=R/'content/editor/canvas/canvas_tool_capability_matrix_w60e12_v2.json'
try:
 data=json.loads(mp.read_text(encoding='utf-8'))
 if data.get('schema')!='havenwild.canvas_tool_capability_matrix.v2': errors.append('E12 matrix schema mismatch')
except Exception as e: errors.append('E12 matrix invalid: '+str(e))
if errors:
 print('FAIL: W60E12 shared inspector/canvas normalization'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E12 shared inspector/canvas normalization (canonical right dock)')
