#!/usr/bin/env python3
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
checks={
'tools/build/Build.sh':['Promote-LpcExpandablePondsV87.py'],
'tools/build/Build.ps1':['Promote-LpcExpandablePondsV87.py'],
'crates/haven_assets/src/asset_registry.rs':['GeneratedAssetRegistry::load_default().expect("generated registry")','(1..=MAX_TILE_VISUAL_VARIANTS).contains'],
}
for rel,need in checks.items():
 s=(ROOT/rel).read_text(encoding='utf-8')
 for token in need:
  if token not in s: raise SystemExit(f'{rel} missing {token}')
print('Pass 145L Haven assets bootstrap/test normalization validated')
