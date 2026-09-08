#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(rel):
 p=R/rel
 if not p.is_file(): errors.append('missing '+rel); return ''
 return p.read_text(encoding='utf-8')
draw=t('apps/haven_editor_native/src/app/draw.rs')
for m in ['self.draw_canvas_tool_rack();','self.draw_canvas_layer_rail();','draw_panel(','draw_workspace_bottom_dock','draw_workspace_splitters']:
 if m not in draw: errors.append('shared shell draw path missing '+m)
try:
 data=json.loads((R/'content/editor/ui/project_panel_mapping_w60e16_v1.json').read_text(encoding='utf-8'))
 if data.get('schema')!='havenwild.project_panel_mapping.w60e16.v1': errors.append('E16 schema mismatch')
 for key in ['world_routes','world_editor','scene_bank','scene_editor','pixel_studio','animation_studio','character_studio']:
  if key not in data.get('workspaces',{}): errors.append('panel map missing '+key)
except Exception as e: errors.append('E16 contract invalid: '+str(e))
if errors:
 print('FAIL: W60E16 project-wide panel mapping'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E16 project-wide panel mapping')
