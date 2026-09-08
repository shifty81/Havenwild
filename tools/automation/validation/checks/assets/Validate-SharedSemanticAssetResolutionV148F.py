#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[5]
required=[
 'crates/haven_assets/src/semantic_asset_resolution.rs',
 'content/asset_packs/semantic_resolution_policy_v1.json',
 'docs/design/SHARED_SEMANTIC_ASSET_RESOLUTION_PASS148F.md',
]
missing=[p for p in required if not (ROOT/p).exists()]
if missing:
 print('Pass 148F FAILED: missing '+', '.join(missing)); sys.exit(1)
text=(ROOT/required[0]).read_text(encoding='utf-8')
for token in ['SemanticAssetResolver','SemanticAssetRequest','AssetResolutionContext','allow_reference_only','explicit_pack','required_tags']:
 if token not in text:
  print(f'Pass 148F FAILED: missing contract token {token}'); sys.exit(1)
policy=json.loads((ROOT/required[1]).read_text(encoding='utf-8'))
cons=set(policy.get('consumers',[]))
expected={'pcg','f3_editor','runtime_renderer','object_placement','character_animation','audio_events','ui_skinning','inventory_items'}
if not expected.issubset(cons):
 print('Pass 148F FAILED: semantic policy is not category-wide'); sys.exit(1)
if not policy.get('reference_only_requires_explicit_opt_in'):
 print('Pass 148F FAILED: reference-only packs must require opt-in'); sys.exit(1)
print('Pass 148F shared semantic asset resolution valid')
