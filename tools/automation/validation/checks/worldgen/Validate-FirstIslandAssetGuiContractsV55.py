#!/usr/bin/env python3
from pathlib import Path
import json, sys
root = Path(__file__).resolve().parents[5]
checks = [
    ('content/worldgen/first_island_generation_profile_v0_1.json', 'haven.first_island_generation_profile.v0_1'),
    ('content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json', 'haven.tile_extraction_workbench.v0_1'),
    ('content/ui/havenwild_gui_generation_contract_v0_1.json', 'haven.gui_generation_contract.v0_1'),
]
errors=[]
for rel, schema in checks:
    p=root/rel
    if not p.exists():
        errors.append(f'missing {rel}')
        continue
    try:
        data=json.loads(p.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'invalid json {rel}: {exc}')
        continue
    if data.get('schema') != schema:
        errors.append(f'{rel} schema mismatch')

profile=json.loads((root/'content/worldgen/first_island_generation_profile_v0_1.json').read_text(encoding='utf-8'))
if profile.get('canonicalTilePixels') != [32,32]:
    errors.append('first island profile must keep 32x32 canonical tile pixels')
if profile.get('targetSceneTiles') != [96,64]:
    errors.append('first island profile must define target 96x64 scene tiles')
if profile.get('playerFacingZoomTarget',0) <= 1.0:
    errors.append('playerFacingZoomTarget should zoom in above 1.0')
extract=json.loads((root/'content/assets/tile_extraction/tile_extraction_workbench_contract_v0_1.json').read_text(encoding='utf-8'))
for required in ['grid_realignment','tile_record_authoring','license_gate','promote_to_project_asset']:
    if required not in extract.get('workbenchModes', []):
        errors.append(f'tile extraction workbench missing mode {required}')
gui=json.loads((root/'content/ui/havenwild_gui_generation_contract_v0_1.json').read_text(encoding='utf-8'))
for required in ['inventory_panel','asset_browser_panel','tool_rail_button']:
    if required not in gui.get('requiredWidgetFamilies', []):
        errors.append(f'GUI contract missing widget family {required}')

for rel in [
    'docs/worldgen/FIRST_ISLAND_GENERATION_AND_LARGE_SCENE_PASS45.md',
    'docs/assets/TILE_EXTRACTION_WORKBENCH_PASS45.md',
    'docs/ui/HAVENWILD_GUI_GENERATION_PASS45.md',
]:
    if not (root/rel).exists():
        errors.append(f'missing doc {rel}')
if errors:
    print('First island / asset / GUI contract validation failed:')
    for e in errors:
        print(' -', e)
    sys.exit(1)
print('First island / asset / GUI contract validation passed.')
