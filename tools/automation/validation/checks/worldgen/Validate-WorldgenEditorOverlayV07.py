#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
checks = []
errors = []
warnings = []

def check(name, ok, detail=''):
    checks.append({'name': name, 'status': 'ok' if ok else 'error', 'detail': detail})
    if not ok:
        errors.append(f'{name}: {detail}')

def load_json(rel):
    path = ROOT / rel
    try:
        data = json.loads(path.read_text())
        check(f'json:{rel}', True)
        return data
    except Exception as exc:
        check(f'json:{rel}', False, str(exc))
        return None

pack = load_json('content/worldgen/packs/worldgen_home_island_v0_7.json')
if pack:
    check('pack:id', pack.get('id') == 'worldgen_home_island_v0_7', str(pack.get('id')))
    check('pack:version', pack.get('version') == '0.7.0', str(pack.get('version')))
    check('pack:previous', pack.get('previousPack') == 'content/worldgen/packs/worldgen_home_island_v0_6.json', str(pack.get('previousPack')))
    profile_rel = pack.get('editorOverlayProfile') or pack.get('editor', {}).get('overlayProfile')
    check('pack:overlay-profile-key', bool(profile_rel), str(profile_rel))
    profile = load_json(profile_rel) if profile_rel else None
else:
    profile = None

if profile:
    check('profile:id', profile.get('id') == 'worldgen_editor_overlay_profile_v0_7', str(profile.get('id')))
    overlays = {item.get('id') for item in profile.get('overlays', [])}
    for required in ['visual_footprint', 'collision_footprint', 'blocked_tile', 'interaction_footprint', 'transition_footprint', 'placement_preview_valid', 'placement_preview_blocked']:
        check(f'profile:overlay:{required}', required in overlays, sorted(overlays))
    hotkeys = {item.get('key') for item in profile.get('hotkeys', [])}
    for key in ['H', 'C', 'I']:
        check(f'profile:hotkey:{key}', key in hotkeys, sorted(hotkeys))

core = '\n'.join(path.read_text(errors='ignore') for path in (ROOT / 'crates/haven_core/src').glob('*.rs'))
game = '\n'.join(path.read_text(errors='ignore') for path in (ROOT / 'crates/haven_game/src').glob('*.rs'))
for token in [
    'pub struct PlacementIssue',
    'pub fn placement_issues_for_object',
    'pub fn can_place_custom_object',
    'visual footprint outside scene',
    'collision footprint on blocked tile',
]:
    check(f'core:{token}', token in core)

for token in [
    'WORLDGEN_PACK_PATH: &str = "content/worldgen/packs/worldgen_home_island_v0_10.json"',
    'show_footprint_overlay',
    'show_collision_overlay',
    'show_interaction_overlay',
    'draw_editor_footprint_overlays',
    'draw_object_footprint_preview',
    'draw_tile_rect_lines',
    'placement_issues_for_object(preview)',
    'Cannot place',
    'KeyCode::H',
    'KeyCode::C',
    'KeyCode::I',
]:
    check(f'game:{token}', token in game)

# Confirm previous validators remain present so v0.7 can be run after the existing pipeline.
for rel in [
    'tools/automation/validation/checks/worldgen/Validate-WorldgenAssets.py',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenRuntimeIndex.py',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenFootprintsV06.py',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenAssets.ps1',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenRuntimeIndex.ps1',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenFootprintsV06.ps1',
]:
    check(f'exists:{rel}', (ROOT / rel).exists())

report = {
    'status': 'pass' if not errors else 'fail',
    'errorCount': len(errors),
    'warningCount': len(warnings),
    'errors': errors,
    'warnings': warnings,
    'checks': checks,
}
logs = ROOT / 'logs'
logs.mkdir(exist_ok=True)
(logs / 'worldgen_editor_overlay_validation_v0_7_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if not errors else 1)
