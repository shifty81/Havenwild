#!/usr/bin/env python3
from pathlib import Path
import tomllib,sys
ROOT = Path(__file__).resolve().parents[5]
data=tomllib.loads((ROOT/'Cargo.toml').read_text(encoding='utf-8'))
members=data.get('workspace',{}).get('members',[])
errors=[]
if len(members)<10: errors.append('workspace member coverage unexpectedly small')
for member in members:
 if not (ROOT/member/'Cargo.toml').is_file(): errors.append(f'missing member manifest: {member}')
arch=(ROOT/'crates/haven_world/src/archipelago_skeleton.rs').read_text(encoding='utf-8')
if 'use crate::open_world::WorldTileCoord;' not in arch: errors.append('archipelago WorldTileCoord import is not module-qualified')
if 'fn landmass(spec: LandmassSpec)' not in arch: errors.append('LandmassSpec constructor contract missing')
if '#[allow(clippy::too_many_arguments)]' in arch: errors.append('Clippy suppression is prohibited')
if errors: print('\n'.join('Pass 146 Rust workspace: '+e for e in errors)); sys.exit(1)
print(f'Pass 146 Rust workspace contract validated: {len(members)} members')
