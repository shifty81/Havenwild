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

pack = load_json('content/worldgen/packs/worldgen_home_island_v0_9.json')
profile = None
if pack:
    check('pack:id', pack.get('id') == 'worldgen_home_island_v0_9', str(pack.get('id')))
    check('pack:version', pack.get('version') == '0.9.0', str(pack.get('version')))
    check('pack:previous', pack.get('previousPack') == 'content/worldgen/packs/worldgen_home_island_v0_8.json', str(pack.get('previousPack')))
    profile_rel = pack.get('editorFootprintEditorProfile') or pack.get('editor', {}).get('objectFootprintEditorProfile')
    check('pack:footprint-editor-profile-key', bool(profile_rel), str(profile_rel))
    profile = load_json(profile_rel) if profile_rel else None
    features = set(pack.get('v09FootprintEditorFeatures', []))
    for text in ['Objects tab exposes Visual, Collision, and Interaction footprint edit targets.', 'Every edit is validated against scene bounds, terrain blocking, and other object collisions before commit.']:
        check(f'pack:feature:{text[:24]}', text in features, sorted(features))

if profile:
    check('profile:id', profile.get('id') == 'worldgen_editor_footprint_editor_profile_v0_9', str(profile.get('id')))
    targets = {item.get('id') for item in profile.get('targets', [])}
    for required in ['visual', 'collision', 'interaction']:
        check(f'profile:target:{required}', required in targets, sorted(targets))
    buttons = {item.get('id') for item in profile.get('buttons', [])}
    for required in ['x_minus', 'x_plus', 'y_minus', 'y_plus', 'w_minus', 'w_plus', 'h_minus', 'h_plus', 'block', 'occl', 'fade', 'reset', 'default']:
        check(f'profile:button:{required}', required in buttons, sorted(buttons))
    hooks = set(profile.get('relatedRuntimeTypes', []))
    for hook in ['ObjectFootprint', 'PlacedObject', 'TavernMap::placement_issues_for_object_excluding']:
        check(f'profile:hook:{hook}', hook in hooks, sorted(hooks))

core = (ROOT / 'crates/haven_core/src/lib.rs').read_text(errors='ignore')
game = (ROOT / 'crates/haven_game/src/main.rs').read_text(errors='ignore')
for token in [
    'pub struct ObjectFootprint',
    'pub fn placement_issues_for_object_excluding',
    'Some(index) == ignore_index',
    'pub fn move_object_to',
]:
    check(f'core:{token}', token in core)

for token in [
    'WORLDGEN_PACK_PATH: &str = "content/worldgen/packs/worldgen_home_island_v0_9.json"',
    'enum FootprintEditTarget',
    'footprint_edit_target: FootprintEditTarget',
    'fn adjust_selected_object_footprint',
    'fn toggle_selected_object_blocking',
    'fn toggle_selected_object_occlusion',
    'fn toggle_selected_object_fade',
    'fn reset_selected_object_footprint_rect',
    'fn reset_selected_object_to_default_footprint',
    'fn apply_selected_object_candidate',
    'placement_issues_for_object_excluding(object, Some(index))',
    'self.push_undo_snapshot();',
    'Footprint Edit:',
    '"Default", panel_x',
]:
    check(f'game:{token}', token in game)

for rel in [
    'content/worldgen/packs/worldgen_home_island_v0_8.json',
    'content/worldgen/worldgen_editor_footprint_editor_profile_v0_9.json',
    'docs/engineering/worldgen_editor_footprint_editor_v0_9.md',
    'WORLDGEN_V0_9_APPLY_NOTES.md',
]:
    check(f'exists:{rel}', (ROOT / rel).exists())

# Lightweight brace sanity for patched game file.
balance = 0
for ch in game:
    if ch == '{':
        balance += 1
    elif ch == '}':
        balance -= 1
check('game:brace-balance', balance == 0, f'balance={balance}')

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
(logs / 'worldgen_footprint_editor_validation_v0_9_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if not errors else 1)
