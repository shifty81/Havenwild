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

pack = load_json('content/worldgen/packs/worldgen_home_island_v0_8.json')
if pack:
    check('pack:id', pack.get('id') == 'worldgen_home_island_v0_8', str(pack.get('id')))
    check('pack:version', pack.get('version') == '0.8.0', str(pack.get('version')))
    check('pack:previous', pack.get('previousPack') == 'content/worldgen/packs/worldgen_home_island_v0_7.json', str(pack.get('previousPack')))
    outliner_rel = pack.get('editorObjectOutlinerProfile') or pack.get('editor', {}).get('objectOutlinerProfile')
    check('pack:object-outliner-profile-key', bool(outliner_rel), str(outliner_rel))
    profile = load_json(outliner_rel) if outliner_rel else None
else:
    profile = None

if profile:
    check('profile:id', profile.get('id') == 'worldgen_editor_object_outliner_profile_v0_8', str(profile.get('id')))
    operations = {item.get('id') for item in profile.get('editOperations', [])}
    for required in ['nudge_up', 'nudge_down', 'nudge_left', 'nudge_right', 'anchor_to_cursor', 'delete_selected']:
        check(f'profile:operation:{required}', required in operations, sorted(operations))
    hooks = set(profile.get('runtimeHooks', []))
    for hook in [
        'TavernMap::placement_issues_for_object_excluding',
        'TavernMap::move_object_to',
        'TavernMap::remove_object_index',
        'Game::draw_objects_editor_tab',
        'Game::handle_objects_tab_click',
        'Game::handle_selected_object_hotkeys',
    ]:
        check(f'profile:hook:{hook}', hook in hooks, sorted(hooks))

core = '\n'.join(path.read_text(errors='ignore') for path in (ROOT / 'crates/haven_core/src').glob('*.rs'))
game = '\n'.join(path.read_text(errors='ignore') for path in (ROOT / 'crates/haven_game/src').glob('*.rs'))
for token in [
    'pub fn placement_issues_for_object_excluding',
    'pub fn can_place_custom_object_excluding',
    'pub fn move_object_to',
    'pub fn remove_object_index',
    'Some(index) == ignore_index',
]:
    check(f'core:{token}', token in core)

for token in [
    'WORLDGEN_PACK_PATH: &str = "content/worldgen/packs/worldgen_home_island_v0_10.json"',
    'selected_object_index: Option<usize>',
    'object_list_offset: usize',
    'draw_objects_editor_tab',
    'handle_objects_tab_click',
    'handle_selected_object_hotkeys',
    'move_selected_object_to',
    'delete_selected_object',
    'placement_issues_for_object_excluding(moved, Some(index))',
    'EditorTab::Objects',
    'KeyCode::Delete',
    'KeyCode::Backspace',
]:
    check(f'game:{token}', token in game)

for rel in [
    'content/worldgen/packs/worldgen_home_island_v0_7.json',
    'content/worldgen/worldgen_editor_overlay_profile_v0_7.json',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenEditorOverlayV07.ps1',
    'tools/automation/validation/checks/worldgen/Validate-WorldgenEditorOverlayV07.py',
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
(logs / 'worldgen_object_outliner_validation_v0_8_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if not errors else 1)
