#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[5]
module = ROOT / 'crates/haven_assets/src/runtime_asset_adapters.rs'
policy = ROOT / 'content/asset_packs/runtime_adapter_policy_v1.json'
lib = ROOT / 'crates/haven_assets/src/lib.rs'
errors=[]
legacy = subprocess.run([sys.executable, str(ROOT / 'tools/automation/validation/checks/assets/Validate-SharedSemanticAssetResolutionV148F.py')], cwd=ROOT)
if legacy.returncode != 0:
    errors.append('Pass 148F shared semantic resolver contract failed')
if not module.is_file(): errors.append('missing runtime adapter module')
else:
    text=module.read_text(encoding='utf-8')
    for token in ['RuntimeAssetConsumer','RuntimeAssetRequest','terrain_semantic_id','terrain_request','object_request','SemanticAssetResolver']:
        if token not in text: errors.append(f'missing adapter contract: {token}')
    for semantic in ['terrain.path.road','terrain.path.stone','terrain.path.mountain']:
        if semantic not in text: errors.append(f'missing distinct path semantic: {semantic}')
if not policy.is_file(): errors.append('missing runtime adapter policy')
else:
    data=json.loads(policy.read_text(encoding='utf-8'))
    consumers=set(data.get('consumers',[]))
    required={'pcg','f3_editor','renderer','object_placement','character','animation','audio','ui','inventory'}
    if not required <= consumers: errors.append('runtime adapter policy omits required consumers')
    rules=data.get('rules',{})
    if not rules.get('pcg_f3_share_terrain_semantic_mapping'): errors.append('PCG/F3 shared mapping not required')
    if rules.get('legacy_lookup_policy') != 'explicit_fallback_only': errors.append('legacy lookup policy must be explicit fallback only')
if 'pub mod runtime_asset_adapters;' not in lib.read_text(encoding='utf-8'):
    errors.append('runtime adapter module not exported')
if errors:
    print('Pass 148G runtime adapter migration FAILED')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('Pass 148G runtime adapter migration valid: 9 consumers share the semantic registry')
