from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[5]
errors = []
warnings = []

def require(path):
    p = root / path
    if not p.exists():
        errors.append(f"missing {path}")
    return p

pack = require('content/worldgen/packs/worldgen_home_island_v0_10.json')
profile = require('content/worldgen/worldgen_scene_export_profile_v0_10.json')
exporter = require('crates/haven_core/src/worldgen_exporter.rs')
loader = require('crates/haven_core/src/worldgen_loader.rs')
core = require('crates/haven_core/src/foundation.rs')
game_root = require('crates/haven_game/src/main.rs').parent

if pack.exists():
    data = json.loads(pack.read_text())
    if data.get('version') != '0.10.0': errors.append('v0.10 pack version is not 0.10.0')
    if data.get('sceneExportProfile') != 'content/worldgen/worldgen_scene_export_profile_v0_10.json': errors.append('pack missing sceneExportProfile')
    if 'v10SceneJsonExportFeatures' not in data: errors.append('pack missing v10SceneJsonExportFeatures')

if profile.exists():
    data = json.loads(profile.read_text())
    if data.get('exportPack') != 'content/worldgen/packs/worldgen_home_island_runtime_export_v0_10.json': errors.append('profile exportPack mismatch')
    if 'objects[].collisionRect' not in data.get('roundTripFields', []): errors.append('profile missing collisionRect round-trip field')

if exporter.exists():
    text = exporter.read_text()
    for needle in ['export_worldgen_pack_to_path', 'backup_existing_export', 'scene_to_json', 'object_to_json', 'blocksMovement', 'occludesPlayer', 'fadeWhenPlayerBehind', '"structuralLevels": structural_levels', 'structural level mismatch for']:
        if needle not in text: errors.append(f'exporter missing {needle}')

if loader.exists():
    text = loader.read_text()
    for needle in ['blocksMovement', 'occludesPlayer', 'fadeWhenPlayerBehind', 'parse_structural_levels(']:
        if needle not in text: errors.append(f'loader does not parse {needle}')

if core.exists():
    text = core.read_text()
    for needle in ['pub mod worldgen_exporter;', 'WorldgenExportReport', 'export_worldgen_pack_to_path']:
        if needle not in text: errors.append(f'core missing {needle}')

if game_root.exists():
    text = '\n'.join(path.read_text(errors='ignore') for path in game_root.glob('*.rs'))
    for needle in ['WORLDGEN_PACK_PATH', 'runtime_worldgen_pack_path', 'WORLDGEN_EXPORT_PACK_PATH', 'runtime_worldgen_export_path', 'KeyCode::F11', 'export_worldgen_json', '"Export" => self.export_worldgen_json()']:
        if needle not in text: errors.append(f'game missing {needle}')

print('Worldgen scene export v0.10 validation')
if errors:
    print('FAIL')
    for e in errors: print('ERROR:', e)
    sys.exit(1)
print('PASS')
if warnings:
    for w in warnings: print('WARNING:', w)
print('Checks:', 38)
