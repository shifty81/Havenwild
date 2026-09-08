#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/authoring/animation_hinge_metadata_w61d_v1.json'))
 if d.get('schema')!='havenwild.animation_hinge_metadata.w61d.v1': errors.append('W61D schema mismatch')
except Exception as e: errors.append('W61D contract invalid: '+str(e))
types=t('crates/haven_pixel/src/animation/types.rs'); studio=t('apps/haven_editor_native/src/app/animation_studio.rs'); inp=t('apps/haven_editor_native/src/app/animation_studio_input.rs')
for marker in ['Hinge','Handle']:
 if marker not in types: errors.append('animation socket kind missing '+marker)
for marker in ['HingePivot','Place Hinge Pivot']:
 if marker not in studio: errors.append('Animation Studio hinge UI missing '+marker)
for marker in ['AnimationPlacementMode::HingePivot','AnimationSocketKind::Hinge','frame.pivot']:
 if marker not in inp: errors.append('hinge placement behavior missing '+marker)
# Compile-safety acceptance: every HingePivot placement path must also have an
# explicit completion/status arm. This catches enum growth that is wired into
# placement behavior but omitted from a later exhaustive match.
if 'AnimationPlacementMode::HingePivot => {' not in inp or 'Placed hinge pivot/socket' not in inp:
 errors.append('hinge placement completion/status arm missing')
if errors:
 print('FAIL: W61D animation hinge metadata'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W61D animation hinge metadata')
