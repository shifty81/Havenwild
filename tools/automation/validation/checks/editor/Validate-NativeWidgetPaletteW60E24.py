#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/ui/native_widget_state_palette_w60e24_v1.json'))
 if d.get('schema')!='havenwild.native_widget_state_palette.w60e24.v1': errors.append('E24 schema mismatch')
except Exception as e: errors.append('E24 contract invalid: '+str(e))
helpers=t('apps/haven_editor_native/src/app/render_helpers.rs'); color=t('apps/haven_editor_native/src/app/pixel_color_panel.rs'); shared=t('apps/haven_editor_native/src/app/shared_palette.rs'); controls=t('apps/haven_editor_native/src/app/gui_controls.rs'); brush=t('crates/haven_pixel/src/brush.rs')
for marker in ['WidgetTone::Standard','WidgetTone::Primary','WidgetTone::Quiet','WidgetTone::Disabled']:
 if marker not in helpers: errors.append('widget tone missing '+marker)
for marker in ['pixel_color_popup_open','color_wheel_center','update_color_from_pointer','begin_color_picker_drag']:
 if marker not in (color+'\n'+shared+'\n'+controls): errors.append('current color picker marker missing '+marker)
for marker in ['Square','Circle','Diamond','Line','Dither','Spray']:
 if marker not in brush: errors.append('brush kind missing '+marker)
for marker in ['sprite_bottom_foreground_color_rect','sprite_bottom_background_color_rect','sprite_bottom_swap_color_rect','sprite_bottom_reset_color_rect']:
 if marker not in shared: errors.append('shared fixed-right palette control missing '+marker)
if errors:
 print('FAIL: W60E24 native widget/palette normalization'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E24 native widget/palette normalization (W76 continuous picker/shared palette)')
