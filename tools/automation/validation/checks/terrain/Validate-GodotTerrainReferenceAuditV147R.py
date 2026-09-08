#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
required=[
'docs/research/GODOT_TERRAIN_SYSTEM_REFERENCE.md',
'docs/audits/HAVENWILD_VS_GODOT_TERRAIN_MATRIX.md',
'docs/design/HAVENWILD_TERRAIN_SET_SCHEMA_V2.md',
'docs/design/HAVENWILD_TERRAIN_PATTERN_RESOLVER_V2.md',
'content/terrain/terrain_sets_v2.json',
'crates/haven_world/src/autotile/terrain_pattern_v2.rs',
'tools/automation/terrain/Audit-LpcTerrainPatternsV147R.py']
missing=[p for p in required if not (ROOT/p).is_file()]
if missing:
    raise SystemExit('Pass 147R missing: '+', '.join(missing))
data=json.loads((ROOT/'content/terrain/terrain_sets_v2.json').read_text())
ids={t['id'] for s in data['terrainSets'] for t in s['terrains']}
expected={'grass','sand','road','stone_path','shallow_water','deep_water'}
if ids != expected:
    raise SystemExit(f'Pass 147R prototype terrain mismatch: {sorted(ids)}')
print('Pass 147R Godot-reference terrain audit contract valid: six distinct prototype terrains')
