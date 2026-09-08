#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/authoring/selection_transform_gizmo_w61c_v1.json'))
 if d.get('schema')!='havenwild.selection_transform_gizmo.w61c.v1': errors.append('W61C schema mismatch')
 policy=d.get('pixelPolicy',{})
 if policy.get('selectionOwnedPivotFollowsMoveScaleMirror') is not True: errors.append('selection-owned pivot policy missing')
 if policy.get('rotationKeepsExplicitPivotRegistered') is not True: errors.append('rotation pivot registration policy missing')
except Exception as e: errors.append('W61C contract invalid: '+str(e))
gizmo=t('apps/haven_editor_native/src/app/transform_gizmo.rs'); ops=t('crates/haven_pixel/src/document_operations.rs'); commands=t('apps/haven_editor_native/src/app/command_registry.rs'); menu=t('apps/haven_editor_native/src/app/editor_menu.rs')
for marker in ['TopLeft','TopRight','BottomLeft','BottomRight','RotateTopLeft','RotateTopRight','RotateBottomLeft','RotateBottomRight','Pivot','Move']:
 if marker not in gizmo: errors.append('gizmo handle missing '+marker)
for marker in ['transform_selection_nearest','rotate_selection_degrees','copy_selection_pixels','paste_pixel_clipboard','map_pivot_between_selections','mirrored_pivot']:
 if marker not in ops: errors.append('selection transform/clipboard primitive missing '+marker)
for marker in ['Mirror Selection Horizontal','Mirror Selection Vertical','Promote Selection to Asset']:
 if marker not in (commands+'\n'+menu): errors.append('selection command missing '+marker)
if errors:
 print('FAIL: W61C selection transform gizmo/clipboard'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W61C selection transform gizmo/clipboard (canonical command registry)')
