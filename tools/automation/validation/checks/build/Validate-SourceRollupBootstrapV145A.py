#!/usr/bin/env python3
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[5]
required=[
 'content/assets/intake/lpc_source_lock_v0_1.json',
 'content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json',
 'content/assets/intake/lpc_terrain_summer_complete_map_v0_1.json',
 'content/assets/intake/lpc_terrain_family_mapping_v0_3.json',
 'content/assets/intake/lpc_terrain_promotion_v0_2.json',
 'content/assets/intake/asset_intake_catalog_v0_1.json',
 'content/editor/assets/asset_intake_atlas_authoring_contract_v0_1.json',
 'assets/source/original/cave_entrance_96.png',
 'tools/automation/dependencies/Ensure-LpcDependency.py',
 'content/validation/validation_manifest_v1.json',
 'tools/build/Build.sh','tools/build/Build.ps1'
]
missing=[p for p in required if not (ROOT/p).is_file()]
if missing:
 raise SystemExit('Missing required source-rollup bootstrap files:\n- '+'\n- '.join(missing))
lock=json.loads((ROOT/required[0]).read_text(encoding='utf-8'))
assert lock.get('schema')=='havenwild.lpc_source_lock.v0_1'
assert lock.get('commit')
assert lock.get('lockedFiles')
print(f"Pass 145A source-rollup bootstrap validated ({len(required)} required files)")
