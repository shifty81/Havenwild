#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(rel):
 p=R/rel
 if not p.is_file(): errors.append('missing '+rel); return ''
 return p.read_text(encoding='utf-8')
reg=t('apps/haven_editor_native/src/app/tool_registry.rs'); rack=t('apps/haven_editor_native/src/app/canvas_tool_rack.rs'); render=t('apps/haven_editor_native/src/app/pixel_studio_render.rs')
for m in ['Self::Selection','Self::Paint','Self::Shapes','Self::Transform','Self::Content','Self::Gameplay','Self::Animation']:
 if m not in reg: errors.append('tool taxonomy missing '+m)
for m in ['pixel_symmetry_tool_rect','draw_pixel_symmetry_popup','Horizontal + Vertical','draw_contextual_brush_slider','apply_contextual_brush_slider']:
 if m not in rack: errors.append('tool option authority missing '+m)
for bad in ['format!("Brush {}px"','"Sym H"','"Sym V"']:
 if bad in render: errors.append('Pixel canvas top row still owns tool option '+bad)
try:
 data=json.loads((R/'content/editor/ui/canvas_tool_taxonomy_w60e14_v1.json').read_text(encoding='utf-8'))
 if data.get('schema')!='havenwild.canvas_tool_taxonomy.w60e14.v1': errors.append('E14 schema mismatch')
except Exception as e: errors.append('E14 contract invalid: '+str(e))
if errors:
 print('FAIL: W60E14 tool taxonomy/options'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E14 tool taxonomy/options')
