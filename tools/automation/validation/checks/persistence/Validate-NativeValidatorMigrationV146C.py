#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
reg=json.loads((ROOT/'content/build/validator_registry_v3.json').read_text(encoding='utf-8'))
errors=[]; vals=reg.get('validators',[])
if reg.get('schema')!='havenwild.validator.registry.v3': errors.append('registry v3 schema missing')
if len(vals)>25: errors.append(f'active validator count {len(vals)} exceeds 25')
required={'terrain.runtime.contract','terrain.water.lifecycle','terrain.promotion.contract','editor.authoring.contract','world.foundation.contract','architecture.validation-framework.native-contract-v146c'}
ids={v.get('id') for v in vals}
if missing:=sorted(required-ids): errors.append('missing native validators: '+', '.join(missing))
for v in vals:
 if v.get('read_only',True) is not True: errors.append(f"{v.get('id')} is not read-only")
for rel in ['tools/automation/validation/native.py','tools/automation/validation/readonly.py','tools/automation/validation/domains/framework_contract.py']:
 if not (ROOT/rel).is_file(): errors.append(f'missing {rel}')
runner=(ROOT/'tools/automation/validation/validation_runner.py').read_text(encoding='utf-8')
for token in ['validator_registry_v3.json','invoke_native','readonly_snapshot','HWV-QUALITY-001']:
 if token not in runner: errors.append(f'runner missing {token}')
if errors:
 print('Pass 146C native validator migration failed:\n'+'\n'.join(errors)); sys.exit(1)
print(f'Pass 146C native validator migration validated: {len(vals)} active validators, {sum(v.get("runner")=="native" for v in vals)} native')
