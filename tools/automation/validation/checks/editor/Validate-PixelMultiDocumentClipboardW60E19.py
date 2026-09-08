#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p):
 q=R/p
 if not q.is_file(): errors.append('missing '+p); return ''
 return q.read_text(encoding='utf-8')
try:
 d=json.loads(t('content/editor/ui/pixel_multidocument_clipboard_w60e19_v1.json'))
 if d.get('schema')!='havenwild.pixel_multidocument_clipboard.w60e19.v1': errors.append('E19 schema mismatch')
except Exception as e: errors.append('E19 contract invalid: '+str(e))
state=t('apps/haven_editor_native/src/app/pixel_studio.rs'); inp=t('apps/haven_editor_native/src/app/pixel_studio_input.rs'); doc=t('crates/haven_pixel/src/document_operations.rs')
for marker in ['document_tabs','active_document_tab','clipboard: Option<PixelClipboard>','copy_selection_to_clipboard','paste_clipboard_into_selection','open_promote_selection_wizard']:
 if marker not in state: errors.append('Pixel multi-document/clipboard marker missing '+marker)
for marker in ['copy_selection_pixels','cut_selection_pixels','paste_pixel_clipboard','duplicate_selection_pixels']:
 if marker not in doc: errors.append('Pixel clipboard primitive missing '+marker)
for marker in ['KeyCode::C','KeyCode::X','KeyCode::V','KeyCode::D','KeyCode::P']:
 if marker not in inp: errors.append('Pixel clipboard/promotion shortcut marker missing '+marker)
if errors:
 print('FAIL: W60E19 Pixel multi-document clipboard/promotion'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E19 Pixel multi-document clipboard/promotion')
