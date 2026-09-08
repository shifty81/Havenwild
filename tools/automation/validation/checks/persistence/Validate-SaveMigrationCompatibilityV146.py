#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
ROOT = Path(__file__).resolve().parents[5]
src=(ROOT/'crates/haven_save/src/lib.rs').read_text(encoding='utf-8')
contract=json.loads((ROOT/'content/worldgen/chunk_persistence_contract_v1.json').read_text(encoding='utf-8'))
m=re.search(r'CURRENT_CLIENT_GENERATION_VERSION\s*:\s*u32\s*=\s*(\d+)',src)
errors=[]
if not m: errors.append('current client generation version not declared')
else:
 current=int(m.group(1))
 text=json.dumps(contract)
 if str(current) not in text: errors.append(f'current generation v{current} absent from migration contract')
 if current>1 and str(current-1) not in text: errors.append(f'previous generation v{current-1} absent from migration contract')
if errors: print('\n'.join('Pass 146 save migration: '+e for e in errors)); sys.exit(1)
print(f'Pass 146 save migration compatibility validated at generation v{m.group(1)}')
