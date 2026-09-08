#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
for rel in ['tools/automation/terrain/Ensure-BaseTerrainBootstrapV145D.py','tools/build/Build.sh','tools/build/Build.ps1']:
    if not (ROOT/rel).exists(): raise SystemExit(f'missing {rel}')
for rel in ['tools/build/Build.sh','tools/build/Build.ps1']:
    text=(ROOT/rel).read_text(encoding='utf-8')
    if 'Ensure-BaseTerrainBootstrapV145D.py' not in text: raise SystemExit(f'{rel} does not ensure base terrain bootstrap')
reg=json.loads((ROOT/'content/worldgen/terrain_world_semantic_registry_v1.json').read_text())
materials=reg.get('terrains') or reg.get('materials') or reg.get('entries')
if not materials: raise SystemExit('terrain registry empty')
print(f'Pass 145D base terrain bootstrap contract valid for {len(materials)} terrain semantics')
