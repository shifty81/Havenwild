#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/ui/integrated_canvas_rails_w60e20_v1.json'))
 if d.get('schema')!='havenwild.integrated_canvas_rails.w60e20.v1': errors.append('E20 schema mismatch')
except Exception as e: errors.append('E20 contract invalid: '+str(e))
shell=t('apps/haven_editor_native/src/app/workspace_shell.rs'); chrome=t('apps/haven_editor_native/src/app/workspace_chrome.rs'); layers=t('apps/haven_editor_native/src/app/canvas_layers.rs')
for marker in ['canvas_tool_rail_collapsed','canvas_layer_rail_collapsed','canvas_layer_rail_width']:
 if marker not in shell: errors.append('workspace rail state missing '+marker)
for marker in ['canvas_layer_rail_width','canvas_tool_rail_collapsed','canvas_layer_rail_collapsed']:
 if marker not in chrome and marker not in layers: errors.append('rail interaction marker missing '+marker)
if errors:
 print('FAIL: W60E20 integrated canvas rails'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W60E20 integrated canvas rails')
