#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT = Path(__file__).resolve().parents[5]
registry=json.loads((ROOT/'content/build/validator_registry_v3.json').read_text(encoding='utf-8'))
legacy=json.loads((ROOT/'content/validation/validation_manifest_v1.json').read_text(encoding='utf-8'))
errors=[]; active=registry.get('validators',[]); ids={v.get('id') for v in active}
if registry.get('schema')!='havenwild.validator.registry.v4': errors.append('Registry V4 is not authoritative')

if len(ids)!=len(active): errors.append('duplicate V4 validator IDs')

profile_counts={name:sum(name in v.get('profiles',[]) for v in active) for name in ('build','source','framework','full')}
if profile_counts['build']!=2: errors.append(f"normal build validator count must be 2, got {profile_counts['build']}")
if profile_counts['source']!=4: errors.append(f"source validator count must be 4, got {profile_counts['source']}")
if profile_counts['framework']!=4: errors.append(f"framework validator count must be 4, got {profile_counts['framework']}")
if profile_counts['full']!=len(active): errors.append('full certification must include every registered validator')

if any('145a' in i.lower() or '145b' in i.lower() or '145c' in i.lower() for i in ids): errors.append('Pass 145 hotfix validator remains registered in V4')
required={'terrain.runtime.contract','terrain.water.lifecycle','terrain.promotion.contract','editor.authoring.contract','world.foundation.contract','architecture.validation-framework.native-contract-v146c'}
for tid in sorted(required-ids): errors.append(f'missing consolidated/native validator {tid}')
for profile in ('source','full'):
 if 'generator' in legacy['profiles'][profile]['includeKinds']: errors.append(f'{profile} compatibility profile still mixes generators with validators')
if errors:
 print('\n'.join('Pass 146 validator quality: '+e for e in errors)); sys.exit(1)
print(f"Validation profile quality validated: build={profile_counts['build']}, source={profile_counts['source']}, framework={profile_counts['framework']}, full={profile_counts['full']}")
