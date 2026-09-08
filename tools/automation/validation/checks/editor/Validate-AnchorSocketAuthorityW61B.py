#!/usr/bin/env python3
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[5]; errors=[]
def t(p): return (R/p).read_text(encoding='utf-8') if (R/p).is_file() else ''
try:
 d=json.loads(t('content/editor/authoring/anchor_socket_authority_w61b_v1.json'))
 if d.get('schema')!='havenwild.anchor_socket_authority.w61b.v1': errors.append('W61B schema mismatch')
except Exception as e: errors.append('W61B contract invalid: '+str(e))
code=t('crates/haven_authoring/src/transform.rs')
for marker in ['pub enum AnchorKind','HingePivot','FootLeft','FootRight','pub struct AuthoringAnchor','pub struct NamedSocket2D','pub struct TransformNode2D']:
 if marker not in code: errors.append('anchor/socket authority missing '+marker)
if errors:
 print('FAIL: W61B anchor/socket authority'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: W61B anchor/socket authority')
