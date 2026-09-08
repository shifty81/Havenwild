#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MAP_W = 48
MAP_H = 32

checks = []
errors = []
warnings = []

def check(name, ok, detail=''):
    checks.append({'name': name, 'status': 'ok' if ok else 'error', 'detail': detail})
    if not ok:
        errors.append(f'{name}: {detail}')

def warn(message):
    warnings.append(message)


def load_json(rel):
    path = ROOT / rel
    try:
        data = json.loads(path.read_text())
        check(f'json:{rel}', True)
        return data
    except Exception as exc:
        check(f'json:{rel}', False, str(exc))
        return None


def parse_rect(obj, key):
    rect = obj.get(key)
    if not isinstance(rect, list) or len(rect) < 2:
        return None
    x = int(rect[0])
    y = int(rect[1])
    w = int(rect[2]) if len(rect) > 2 else 1
    h = int(rect[3]) if len(rect) > 3 else 1
    return x, y, w, h


def rect_has_in_bounds(rect):
    if rect is None:
        return False
    x, y, w, h = rect
    for ty in range(y, y + max(h, 0)):
        for tx in range(x, x + max(w, 0)):
            if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
                return True
    return False


def rect_oob_cells(rect):
    if rect is None:
        return []
    x, y, w, h = rect
    out = []
    for ty in range(y, y + max(h, 0)):
        for tx in range(x, x + max(w, 0)):
            if not (0 <= tx < MAP_W and 0 <= ty < MAP_H):
                out.append((tx, ty))
    return out

pack = load_json('content/worldgen/packs/worldgen_home_island_v0_6.json')
if pack:
    check('pack:id', pack.get('id') == 'worldgen_home_island_v0_6', str(pack.get('id')))
    check('pack:version', pack.get('version') == '0.6.0', str(pack.get('version')))
    check('pack:footprint-runtime-key', bool(pack.get('objectFootprintRuntime')), str(pack.get('objectFootprintRuntime')))
    runtime = load_json(pack.get('objectFootprintRuntime', 'content/worldgen/worldgen_object_footprint_runtime_v0_6.json'))
else:
    runtime = None

scene_count = 0
object_count = 0
custom_footprint_count = 0
if pack:
    for rel in pack.get('sceneFiles', []):
        data = load_json(rel)
        if not data:
            continue
        scene_count += 1
        scene_id = data.get('sceneId', rel)
        objects = data.get('objects', [])
        for obj in objects:
            object_count += 1
            oid = obj.get('id', '<unnamed>')
            visual = parse_rect(obj, 'visualRect')
            collision = parse_rect(obj, 'collisionRect')
            interaction = None
            interactions = obj.get('interactions') or []
            if interactions:
                interaction = parse_rect(interactions[0], 'rect')
            if visual or collision or interaction:
                custom_footprint_count += 1
            check(f'object:{scene_id}:{oid}:has-footprint', bool(visual or collision or interaction))
            if collision:
                oob = rect_oob_cells(collision)
                check(f'object:{scene_id}:{oid}:collision-in-bounds', not oob, str(oob[:5]))
            if interaction:
                check(f'object:{scene_id}:{oid}:interaction-reachable', rect_has_in_bounds(interaction), str(interaction))
            if visual:
                if not rect_has_in_bounds(visual):
                    warn(f'{scene_id}:{oid} visual rect has no in-bounds tile: {visual}')
                if visual[2] > 1 or visual[3] > 1:
                    check(f'object:{scene_id}:{oid}:multitile-visual', True, f'{visual[2]}x{visual[3]}')

core = (ROOT / 'crates/haven_core/src/lib.rs').read_text(errors='ignore')
loader = (ROOT / 'crates/haven_core/src/worldgen_loader.rs').read_text(errors='ignore')
editor = (ROOT / 'crates/haven_editor/src/lib.rs').read_text(errors='ignore')
game = (ROOT / 'crates/haven_game/src/main.rs').read_text(errors='ignore')

required_core = [
    'pub struct ObjectFootprint',
    'pub fn visual_rect',
    'pub fn collision_rect',
    'pub fn interaction_rect',
    'pub fn blocking_object_at',
    'pub fn interaction_object_at',
    'pub fn is_cell_walkable',
    'pub fn place_custom_object',
]
for token in required_core:
    check(f'rust-core:{token}', token in core)

required_loader = ['parse_rect(value.get("visualRect"))', 'parse_rect(value.get("collisionRect"))', 'PlacedObject::with_footprint']
for token in required_loader:
    check(f'rust-loader:{token}', token in loader)

required_editor = ['Footprint:', 'blocking_object_at', 'validate_object_footprints', 'scene.is_cell_walkable']
for token in required_editor:
    check(f'rust-editor:{token}', token in editor)

required_game = ['interaction_object_at', 'object.visual_rect()', 'object.sort_y()', 'is_cell_walkable']
for token in required_game:
    check(f'rust-game:{token}', token in game)
check(
    'rust-game:WORLDGEN_PACK_PATH-v0-6-or-newer',
    'WORLDGEN_PACK_PATH: &str = "content/worldgen/packs/worldgen_home_island_v0_6.json"' in game
    or 'WORLDGEN_PACK_PATH: &str = "content/worldgen/packs/worldgen_home_island_v0_7.json"' in game,
)

check('scenes:count', scene_count == 9, str(scene_count))
check('objects:count', object_count >= 10, str(object_count))
check('objects:custom-footprints', custom_footprint_count == object_count and object_count > 0, f'{custom_footprint_count}/{object_count}')

report = {
    'status': 'pass' if not errors else 'fail',
    'errorCount': len(errors),
    'warningCount': len(warnings),
    'sceneCount': scene_count,
    'objectCount': object_count,
    'customFootprintCount': custom_footprint_count,
    'errors': errors,
    'warnings': warnings,
    'checks': checks,
}

logs = ROOT / 'logs'
logs.mkdir(exist_ok=True)
(logs / 'worldgen_footprint_validation_v0_6_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
raise SystemExit(0 if not errors else 1)
