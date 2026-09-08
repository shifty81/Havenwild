#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/ui/inspector_bottom_dock_w60e23_v1.json'))
 if d.get('schema')!='havenwild.inspector_bottom_dock.w60e23.v1': errors.append('E23 schema mismatch')
 if d.get('bottomDock',{}).get('tabs')!=['Console','Imports','Build','Activity']: errors.append('E23 bottom tabs must exclude duplicate Validation')
 if d.get('bottomDock',{}).get('validationReportOwner')!='right_dock.validation': errors.append('E23 right-dock Validation owner missing')
except Exception as e: errors.append('E23 contract invalid: '+str(e))
shell=t('apps/haven_editor_native/src/app/workspace_shell.rs'); chrome=t('apps/haven_editor_native/src/app/workspace_chrome.rs')
for marker in ['bottom_dock_open','bottom_dock_tab','bottom_dock_height','pub(crate) const ALL: [Self; 4]']:
 if marker not in shell: errors.append('bottom dock state missing '+marker)
if 'Self::Validation,' in shell.split('pub(crate) const ALL: [Self; 4]',1)[1].split('];',1)[0]: errors.append('bottom dock still exposes duplicate Validation tab')
if 'RightDockTab' not in shell or 'Self::Validation => "Validation"' not in shell: errors.append('right dock Validation authority missing')
for marker in ['draw_workspace_bottom_dock','Bottom Panels','bottom_dock_height']:
 if marker not in chrome: errors.append('bottom dock chrome missing '+marker)
if errors:
 print('FAIL: W60E23 inspector/bottom dock normalization'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E23 inspector/bottom dock normalization')
