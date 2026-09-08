#!/usr/bin/env python3
"""Build W46A exploded BuildingRecipe acceptance scene from source-controlled recipe data."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[3]
CATALOG = Path('content/buildings/building_recipe_catalog_v1.json')
OUT = Path('content/worldgen/scenes/world_asset_acceptance/building_recipe_acceptance_scene_v1.json')
PACK = Path('content/worldgen/packs/worldgen_home_island_test_v0_11.json')
RECIPE_ID = 'havenwild.prototype.three_level_house'


def load_published(root: Path) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    base = root / 'content/asset_packs/havenwild_objects'
    for path in sorted(base.glob('published*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        if data.get('schema') not in {'havenwild.published_world_asset_catalog.v1', 'havenwild.placeable_catalog.v1'}:
            continue
        for entry in data.get('entries', []):
            entries[entry['id']] = entry
            entries[entry.get('semantic_id', entry['id'])] = entry
            for alias in entry.get('aliases', []):
                entries[alias] = entry
    return entries


def load_recipe(root: Path) -> dict:
    catalog = json.loads((root / CATALOG).read_text(encoding='utf-8-sig'))
    item = next(entry for entry in catalog['entries'] if entry['id'] == RECIPE_ID)
    return json.loads((root / item['path']).read_text(encoding='utf-8-sig'))


def add_object(objects: list[dict], published: dict[str, dict], asset_id: str, x: int, y: int,
               *, state: str | None = None, label: str = '', level: int | None = None) -> None:
    entry = published[asset_id]
    fp = entry['footprint']
    vo = fp.get('visual_offset', [0, 0]); vs = fp.get('visual_size', [1, 1])
    co = fp.get('collision_offset', [0, 0]); cs = fp.get('collision_size', [0, 0])
    index = len(objects)
    obj = {
        'id': f'w46a_recipe_carrier_{index:04d}_{entry["id"]}',
        'assetId': entry['id'],
        'acceptanceLane': 'w46a_building_recipe',
        'acceptanceStatus': 'CANDIDATE',
        'visualRect': [x + vo[0], y + vo[1], vs[0], vs[1]],
        'collisionRect': [x + co[0], y + co[1], cs[0], cs[1]],
        'layer': 'low_object',
        'blocksMovement': bool(fp.get('blocks_movement', False)),
        'occludesPlayer': bool(fp.get('occludes_player', False)),
        'fadeWhenPlayerBehind': bool(fp.get('fade_when_player_behind', False)),
        'interactions': [{'id': f'inspect_w46a_{index:04d}', 'kind': 'inspect', 'rect': [x, y, 1, 1]}],
    }
    if state:
        obj['state'] = state
    if label:
        obj['recipePiece'] = label
    if level is not None:
        obj['buildingLevel'] = level
    objects.append(obj)


def expand_roof(recipe: dict) -> list[tuple[str, int, int]]:
    roof = recipe['roof']; components = roof['components']; x, y, w, h = roof['rect']
    out = []
    for dy in range(h):
        for dx in range(w):
            if dx == 0 and dy == 0: aid = components['northWestCorner']
            elif dx == w - 1 and dy == 0: aid = components['northEastCorner']
            elif dx == 0 and dy == h - 1: aid = components['southWestCorner']
            elif dx == w - 1 and dy == h - 1: aid = components['southEastCorner']
            elif dy == 0: aid = components['northEdge']
            elif dy == h - 1: aid = components['southEdge']
            elif dx == 0: aid = components['westEdge']
            elif dx == w - 1: aid = components['eastEdge']
            else: aid = components['field']
            out.append((aid, x + dx, y + dy))
    return out


def build_scene(root: Path) -> dict:
    recipe = load_recipe(root); published = load_published(root)
    W, H = 82, 34
    terrain = [['grass'] * W for _ in range(H)]
    objects: list[dict] = []
    level_offsets = {-1: (4, 8), 0: (22, 8), 1: (40, 8)}

    for level in recipe['levels']:
        level_no = level['level']; ox, oy = level_offsets[level_no]
        for fill in level.get('floorFills', []):
            x, y, w, h = fill['rect']
            for dy in range(h):
                for dx in range(w):
                    add_object(objects, published, fill['assetId'], ox + x + dx, oy + y + dy,
                               label=f'{level["id"]}:floor', level=level_no)
        door_tiles = {tuple(o['tile']) for o in level.get('openings', []) if o['kind'] in {'door', 'archway'}}
        for wall in level.get('wallRuns', []):
            aid = wall.get('visualAssetId')
            if not aid:
                continue
            sx, sy = wall['start']
            for offset in range(wall['length']):
                if wall['edge'] in {'north', 'south', 'interior'}:
                    tile = (sx + offset, sy)
                else:
                    tile = (sx, sy + offset)
                if tile in door_tiles:
                    continue
                add_object(objects, published, aid, ox + tile[0], oy + tile[1],
                           label=f'{level["id"]}:wall:{wall["id"]}', level=level_no)
        for opening in level.get('openings', []):
            tx, ty = opening['tile']
            add_object(objects, published, opening['assetId'], ox + tx, oy + ty,
                       state=opening.get('state'), label=f'{level["id"]}:opening:{opening["id"]}', level=level_no)
        for connector in recipe.get('connectors', []):
            if connector['fromLevel'] != level_no:
                continue
            tx, ty = connector['fromTile']
            add_object(objects, published, connector['assetId'], ox + tx, oy + ty,
                       label=f'connector:{connector["id"]}', level=level_no)

    roof_ox, roof_oy = 60, 8
    for asset_id, x, y in expand_roof(recipe):
        add_object(objects, published, asset_id, roof_ox + x, roof_oy + y,
                   label='roof:flat_nine_slice', level=recipe['roof']['level'])

    scene = {
        'id': 'building_recipe_acceptance_scene_v1',
        'version': '1.0.0',
        'kind': 'worldgen_scene',
        'sceneId': 'building_recipe_acceptance',
        'title': 'Building Recipe Acceptance — W46A',
        'sceneKind': 'exterior',
        'biome': 'temperate',
        'role': 'diagnostic_only',
        'sceneSize': [W, H],
        'tileSize': [32, 32],
        'edgePolicy': {'mustAvoidVoid': True, 'resolvedBorders': {'north': 'grass', 'south': 'grass', 'east': 'grass', 'west': 'grass'}},
        'layers': {'terrain': terrain},
        'objects': objects,
        'transitions': [],
        'spawns': [{'id': 'player_default', 'tile': [16, 27]}],
        'editor': {'notes': [
            'Exploded W46A view: cellar (-1), ground (0), upstairs (+1), then flat-nine-slice roof.',
            'All three structural levels belong to one BuildingInstance. This exploded layout is diagnostic presentation only.',
            'Only exact south-facing wall art is rendered. North/east/west logical walls remain authoritative collision but fail closed visually until exact facing variants are reviewed.',
            'Door/archway replaces the wall visual at its tile; windows overlay the wall visual.',
            'Roof/front-wall cutaway is per-camera presentation and never unloads or mutates the BuildingInstance.',
            'W46B native runtime/editor materialization now lives in building_instance_acceptance; this exploded W46A board remains a recipe-only diagnostic.'
        ]},
        'acceptance': {
            'pass': '167Z109W46A',
            'buildingRecipeId': RECIPE_ID,
            'buildingRecipeCatalog': str(CATALOG).replace('\\', '/'),
            'buildingAuthority': 'BuildingRecipeRegistry',
            'visualAuthority': 'PublishedWorldAssetRegistry',
            'structuralLevels': [-1, 0, 1],
            'ordinaryInteriorPolicy': 'same_world_building_instance',
            'candidateCount': len(objects)
        },
        'validationRules': [
            'recipe structural geometry is authoritative even when a facing-specific visual is deferred',
            'every rendered piece resolves through PublishedWorldAssetRegistry',
            'no wrong-facing visual substitutions are permitted',
            'ordinary upstairs/cellar remain levels of the same BuildingInstance',
            'roof/front-wall cutaway remains camera-local presentation',
            'diagnostic scene carriers are not production BuildingInstance authority'
        ]
    }
    return scene


def sync_pack(root: Path) -> None:
    path = root / PACK
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    rel = str(OUT).replace('\\', '/')
    exact_rel = 'content/worldgen/scenes/world_asset_acceptance/structure_exact_modules_acceptance_scene_v1.json'
    for key in ('sceneFiles', 'smokeTests'):
        values = data.setdefault(key, [])
        for item in (exact_rel, rel):
            if item not in values:
                values.append(item)
    test = data.setdefault('testWorld', {})
    test['buildingRecipeAcceptanceSceneId'] = 'building_recipe_acceptance'
    test['buildingRecipeAcceptanceScene'] = rel
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--root', type=Path, default=ROOT_DEFAULT)
    args = ap.parse_args(); root = args.root.resolve()
    scene = build_scene(root)
    out = root / OUT; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scene, indent=2) + '\n', encoding='utf-8')
    sync_pack(root)
    print(f'W46A building recipe acceptance: {scene["acceptance"]["candidateCount"]} materialized visual piece(s) -> {OUT}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
