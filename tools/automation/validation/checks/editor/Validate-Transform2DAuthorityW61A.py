#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/authoring/transform2d_w61a_v1.json'))
 if d.get('schema')!='havenwild.transform2d.w61a.v1': errors.append('W61A schema mismatch')
except Exception as e: errors.append('W61A contract invalid: '+str(e))
code=t('crates/haven_authoring/src/transform.rs'); lib=t('crates/haven_authoring/src/lib.rs')
for marker in ['pub struct Transform2D','pub struct TransformConstraints','pub enum TransformSpace','swing_door_left','tree_sway']:
 if marker not in code: errors.append('transform authority missing '+marker)
if 'pub mod transform' not in lib or 'Transform2D' not in lib: errors.append('transform authority not exported')
if errors:
 print('FAIL: W61A Transform2D authority'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W61A Transform2D authority')
