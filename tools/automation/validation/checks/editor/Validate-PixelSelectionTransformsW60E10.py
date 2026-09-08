#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(x): return (R/x).read_text(encoding='utf-8') if (R/x).is_file() else ''
ops=t('crates/haven_pixel/src/document_operations.rs'); state=t('apps/haven_editor_native/src/app/pixel_studio.rs'); inp=t('apps/haven_editor_native/src/app/pixel_studio_input.rs'); render=t('apps/haven_editor_native/src/app/pixel_studio_render.rs')
for m in ['rotate_selection_clockwise','nudge_selection','select_opaque_bounds','select_color_bounds']:
 if m not in ops: errors.append('missing E10 operation '+m)
for m in ['RepeatPreviewMode','symmetry_axis_x','symmetry_axis_y']:
 if m not in state: errors.append('missing E10 state '+m)
for m in ['KeyCode::R','KeyCode::O','KeyCode::T','symmetry_axis_x']:
 if m not in inp: errors.append('missing E10 input '+m)
if 'Repeat Preview' not in render: errors.append('repeat preview UI missing')
if errors:
 print('FAIL: W60E10 pixel selection transforms'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E10 pixel selection transforms')
