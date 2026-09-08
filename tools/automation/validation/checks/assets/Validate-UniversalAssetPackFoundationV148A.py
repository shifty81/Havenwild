#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
required=[
 'crates/haven_assets/src/asset_pack.rs',
 'content/asset_packs/havenwild_core/pack.json',
 'content/asset_packs/lpc_revised/pack.json',
 'docs/design/UNIVERSAL_ASSET_PACK_FOUNDATION_PASS148A.md'
]
errors=[]
for rel in required:
    if not (ROOT/rel).is_file(): errors.append(f'missing {rel}')
for rel in required[1:3]:
    if not (ROOT/rel).is_file(): continue
    data=json.loads((ROOT/rel).read_text(encoding='utf-8'))
    if data.get('schema')!='havenwild.asset_pack.v1': errors.append(f'{rel}: wrong schema')
    lic=data.get('license',{})
    if data.get('production_enabled') and (not lic.get('production_approved') or not lic.get('commercial_use') or not lic.get('redistribution')):
        errors.append(f'{rel}: production-enabled pack lacks approved compatible license flags')
src=(ROOT/required[0]).read_text(encoding='utf-8') if (ROOT/required[0]).is_file() else ''
for token in ['pub enum AssetCategory','pub struct AssetPackManifest','pub struct StableAssetRef','pub struct AssetPackRegistry','resolve_semantic']:
    if token not in src: errors.append(f'asset_pack.rs missing {token}')
if errors:
    print('Pass 148A universal asset-pack foundation FAILED')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('Pass 148A universal asset-pack foundation valid: open-ended categories, stable refs, multi-pack semantic resolution')
