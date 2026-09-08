#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
p=ROOT/'content/build/generated_output_registry_v2.json'
errors=[]
try: data=json.loads(p.read_text(encoding='utf-8'))
except Exception as exc: print(f'Pass 146 generated-output registry unreadable: {exc}'); raise SystemExit(1)
if data.get('schema')!='havenwild.generated_output_registry.v2': errors.append('invalid schema')
seen=set()
for i,row in enumerate(data.get('outputs',[])):
    out=row.get('output'); gen=row.get('generator'); inputs=row.get('inputs',[])
    if not out or out in seen: errors.append(f'output[{i}] missing or duplicate: {out}')
    seen.add(out)
    if not gen or not (ROOT/gen).is_file(): errors.append(f'{out}: missing generator {gen}')
    if not inputs: errors.append(f'{out}: no declared inputs')
    for rel in inputs:
        # Generated prerequisites may not exist before generation, but must themselves be registered.
        if not (ROOT/rel).exists() and rel not in seen and not any(x.get('output')==rel for x in data.get('outputs',[])):
            errors.append(f'{out}: undeclared/missing input {rel}')
    if row.get('stage') not in {'asset_generation','optional_full_catalog'}: errors.append(f'{out}: invalid stage')
    if row.get('packaging') not in {'regenerate','cache-or-regenerate'}: errors.append(f'{out}: invalid packaging policy')
if len(seen)<8: errors.append('registry must cover core generated outputs')
if errors:
    print('\n'.join('Pass 146 build graph: '+e for e in errors)); sys.exit(1)
print(f'Pass 146 generated asset build graph validated: {len(seen)} outputs')
