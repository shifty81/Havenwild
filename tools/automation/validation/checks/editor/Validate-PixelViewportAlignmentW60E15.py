#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(rel):
 p=R/rel
 if not p.is_file(): errors.append('missing '+rel); return ''
 return p.read_text(encoding='utf-8')
render=t('apps/haven_editor_native/src/app/pixel_studio_render.rs'); layout=t('apps/haven_editor_native/src/app/pixel_studio_layout.rs'); studio=t('apps/haven_editor_native/src/app/pixel_studio.rs'); canvas=t('apps/haven_editor_native/src/app/canvas_controller.rs')
for m in ['draw_pixel_aligned_checkerboard','cell_pixels','transform.image.x','transform.image.y']:
 if m not in render: errors.append('pixel-aligned checkerboard missing '+m)
for m in ['draw_canvas_view_controls_overlay','handle_canvas_view_controls_click']:
 if m not in canvas: errors.append('canonical compact Pixel canvas chrome missing '+m)
if 'zoom_one_to_one' not in studio: errors.append('1:1 zoom authority missing')
if 'draw_checkerboard(clipped, 28.0)' in render: errors.append('old screen-space checkerboard still used for main Pixel canvas')
try:
 data=json.loads((R/'content/editor/ui/pixel_viewport_contract_w60e15_v1.json').read_text(encoding='utf-8'))
 if data.get('checkerboard',{}).get('mustAlignWithPixelGrid') is not True: errors.append('E15 alignment contract not locked')
except Exception as e: errors.append('E15 contract invalid: '+str(e))
if errors:
 print('FAIL: W60E15 pixel viewport alignment'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E15 pixel viewport alignment')
