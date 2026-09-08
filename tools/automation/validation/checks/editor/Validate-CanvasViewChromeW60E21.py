#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/ui/canvas_view_chrome_w60e21_v1.json'))
 if d.get('schema')!='havenwild.canvas_view_chrome.w60e21.v1': errors.append('E21 schema mismatch')
except Exception as e: errors.append('E21 contract invalid: '+str(e))
layout=t('apps/haven_editor_native/src/app/pixel_studio_layout.rs'); inp=t('apps/haven_editor_native/src/app/pixel_studio_input.rs'); render=t('apps/haven_editor_native/src/app/pixel_studio_render.rs'); canvas=t('apps/haven_editor_native/src/app/canvas_controller.rs'); tabs=t('apps/haven_editor_native/src/app/document_tabs.rs')
for marker in ['draw_canvas_view_controls_overlay','handle_canvas_view_controls_click','canvas_view_control_rect']:
 if marker not in canvas: errors.append('canonical canvas chrome marker missing '+marker)
if 'draw_scene_document_tabs' not in tabs and 'document_tabs' not in tabs: errors.append('protected document-tab canvas chrome missing')
if errors:
 print('FAIL: W60E21 canvas view chrome'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E21 canvas view chrome')
