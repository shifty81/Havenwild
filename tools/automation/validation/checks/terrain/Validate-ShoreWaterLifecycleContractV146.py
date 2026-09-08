#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[5]
resolver=(ROOT/'crates/haven_world/src/autotile/shoreline_resolver.rs').read_text(encoding='utf-8')
tests=(ROOT/'crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs').read_text(encoding='utf-8')
errors=[]
for token in ('normalize_shore_water_lifecycle_region','ShoreFoam','ShallowWater','DeepWater'):
 if token not in resolver: errors.append(f'resolver missing public behavior token {token}')
for token in ('TileKind::ShoreFoam','TileKind::ShallowWater','TileKind::DeepWater'):
 if token not in tests: errors.append(f'behavior tests missing {token}')
for retired in ('editor_neighbor_count','editor_cardinal_count','is_editor_water','is_editor_land_or_shore'):
 if retired in (ROOT/'crates/haven_game/src/runtime_editor_shell.rs').read_text(encoding='utf-8'): errors.append(f'retired duplicate helper returned: {retired}')
if errors: print('\n'.join('Pass 146 shore/water: '+e for e in errors)); sys.exit(1)
print('Pass 146 shore/water lifecycle contract validated through shared resolver and behavior tests')
