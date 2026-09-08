#!/usr/bin/env python3
from pathlib import Path
import json
import random

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'content/worldgen/scenes/home_island/farmstead_scene_v0_3.json'
W, H = 96, 64
SEED = 167530814
rng = random.Random(SEED)


def load_pub():
    out = {}
    for p in sorted((ROOT / 'content/asset_packs/havenwild_objects').glob('published_*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception:
            continue
        if data.get('schema') == 'havenwild.published_world_asset_catalog.v1':
            for entry in data.get('entries', []):
                out[entry['id']] = entry
    return out


PUB = load_pub()


def obj(oid, aid, x, y, state=None, kind='inspect'):
    entry = PUB[aid]
    fp = entry['footprint']
    vo = fp.get('visual_offset', [0, 0])
    vs = fp['visual_size']
    co = fp.get('collision_offset', [0, 0])
    cs = fp.get('collision_size', [0, 0])
    io = fp.get('interaction_offset', [0, 0])
    ins = fp.get('interaction_size', [1, 1])
    out = {
        'id': oid,
        'assetId': aid,
        'visualRect': [x + vo[0], y + vo[1], vs[0], vs[1]],
        'collisionRect': [x + co[0], y + co[1], cs[0], cs[1]],
        'layer': 'tall_object' if fp.get('occludes_player') else 'low_object',
        'blocksMovement': fp.get('blocks_movement', True),
        'occludesPlayer': fp.get('occludes_player', False),
        'fadeWhenPlayerBehind': fp.get('fade_when_player_behind', False),
        'interactions': [{
            'id': f'{kind}_{oid}',
            'kind': kind,
            'rect': [x + io[0], y + io[1], ins[0], ins[1]],
        }],
    }
    if state is not None:
        out['state'] = state
    return out


def set_tile(layer, x, y, value):
    if 0 <= x < W and 0 <= y < H:
        layer[y][x] = value


def paint_disc(layer, cx, cy, rx, ry, value, jitter=0.0):
    for y in range(max(0, cy - ry - 1), min(H, cy + ry + 2)):
        for x in range(max(0, cx - rx - 1), min(W, cx + rx + 2)):
            dx = (x - cx) / max(rx, 1)
            dy = (y - cy) / max(ry, 1)
            noise = rng.uniform(-jitter, jitter) if jitter else 0.0
            if dx * dx + dy * dy <= 1.0 + noise:
                layer[y][x] = value


def paint_segment(layer, a, b, width, value):
    x, y = a
    tx, ty = b
    half = width // 2
    sx = 1 if tx >= x else -1
    while x != tx:
        for d in range(-half, half + 1):
            set_tile(layer, x, y + d, value)
        x += sx
    sy = 1 if ty >= y else -1
    while y != ty:
        for d in range(-half, half + 1):
            set_tile(layer, x + d, y, value)
        y += sy
    set_tile(layer, tx, ty, value)


def paint_route(layer, points, width=1, value='StonePath'):
    for a, b in zip(points, points[1:]):
        paint_segment(layer, a, b, width, value)


def reserved(x, y):
    # Keep the central homestead pad, main routes, gate and cave approach open.
    if 31 <= x <= 70 and 22 <= y <= 49:
        return True
    if 43 <= x <= 54 and 49 <= y <= 60:
        return True
    if 72 <= x <= 82 and 7 <= y <= 22:
        return True
    return False


def main():
    terrain = [['Grass'] * W for _ in range(H)]
    zones = [['none'] * W for _ in range(H)]
    levels = [[0] * W for _ in range(H)]

    # A continuous Level-2 decorative highland surrounds the initial Estate.
    # The south entrance is the only initial opening through that highland.
    for y in range(H):
        for x in range(W):
            high = y <= 5 or x <= 5 or x >= 90 or y >= 60
            if high:
                terrain[y][x] = 'Grass'
                levels[y][x] = 2

    for y in range(58, 64):
        for x in range(46, 51):
            levels[y][x] = 0
            terrain[y][x] = 'StonePath'
            zones[y][x] = 'public_path'

    # Narrow cave host is part of the Level-2 north highland. The lower tile
    # remains walkable and owns interaction/transition for the 1x2 aperture.
    for y in range(6, 9):
        for x in range(77, 80):
            terrain[y][x] = 'Grass'
            levels[y][x] = 2

    # Small organic soil/garden starter area, deliberately outside the central
    # building pad so farming can grow without fighting the home footprint.
    paint_disc(terrain, 22, 34, 9, 7, 'Dirt', jitter=0.12)
    for y in range(26, 42):
        for x in range(12, 32):
            if terrain[y][x] == 'Dirt':
                zones[y][x] = 'field'

    # Primary Estate route: south gate -> home clearing -> north-east cave.
    main_route = [(48, 62), (48, 55), (53, 50), (55, 43), (59, 36)]
    cave_route = [(59, 36), (64, 31), (68, 25), (73, 19), (77, 13), (78, 10)]
    paint_route(terrain, main_route, width=3)
    paint_route(terrain, cave_route, width=1)
    for y in (9, 10, 11):
        terrain[y][78] = 'Dirt'

    # A short western garden spur makes the field legible without bisecting it.
    paint_route(terrain, [(53, 50), (44, 46), (34, 42), (29, 39)], width=1)

    for y in range(H):
        for x in range(W):
            if terrain[y][x] in ('StonePath', 'MountainPath'):
                zones[y][x] = 'public_path'

    # Tall-grass detail is deterministic and constrained away from the central
    # build pad/routes. It is terrain detail, not an object substitute.
    for _ in range(260):
        x = rng.randint(8, 87)
        y = rng.randint(8, 57)
        if reserved(x, y):
            continue
        if terrain[y][x] == 'Grass' and rng.random() < 0.58:
            terrain[y][x] = 'TallGrass'

    objects = [obj('estate_cave_mouth', 'cave_entrance_default', 78, 8, 'open', 'enter')]
    objects[0]['interactions'][0]['rect'] = [78, 10, 1, 1]

    # Edge woodland frames the property while the center remains intentionally
    # open for the player's home, farming, crafting and future purchased growth.
    tree_pos = [
        (9, 11), (15, 9), (22, 12), (29, 9), (38, 11), (47, 9), (56, 12),
        (65, 9), (72, 12), (84, 12), (86, 20), (84, 29), (86, 39), (83, 49),
        (77, 55), (69, 53), (61, 55), (49, 54), (38, 55), (29, 53), (20, 55),
        (12, 52), (9, 45), (12, 38), (9, 30), (11, 22), (18, 18), (27, 17),
    ]
    for i, (x, y) in enumerate(tree_pos):
        objects.append(obj(f'estate_tree_{i + 1:02d}', f'tree_oak_mature_{i % 8 + 1:02d}', x, y, 'mature'))

    shrubs = [(17, 23), (25, 21), (14, 42), (24, 48), (36, 18), (74, 27), (80, 37), (76, 47)]
    for i, (x, y) in enumerate(shrubs):
        objects.append(obj(f'estate_shrub_{i + 1:02d}', f'shrub_berry_{i % 4 + 1:02d}', x, y))

    boulders = [(33, 14), (43, 15), (69, 15), (82, 24), (79, 43), (70, 51), (32, 51), (15, 47)]
    for i, (x, y) in enumerate(boulders):
        objects.append(obj(f'estate_boulder_{i + 1:02d}', f'resource_boulder_{i % 4 + 1:02d}', x, y))

    forage = [
        ('forage_mushroom_01', 13, 35), ('forage_mushroom_02', 18, 46),
        ('forage_mushroom_03', 28, 50), ('forage_mushroom_04', 82, 33),
        ('forage_wild_herb_01', 19, 20), ('forage_wild_herb_02', 35, 20),
        ('forage_wild_herb_03', 73, 50), ('flora_wildflower_01', 16, 16),
        ('flora_wildflower_02', 30, 14), ('flora_wildflower_03', 67, 17),
        ('flora_wildflower_01', 80, 29), ('flora_wildflower_02', 27, 45),
    ]
    for i, (aid, x, y) in enumerate(forage):
        objects.append(obj(f'estate_forage_{i + 1:02d}', aid, x, y))

    # W54F: leave the south structural opening visually clean. The previous fence
    # band sat on the Level-2 boundary and read as a duplicated cliff-top border.
    # A future gate assembly must be authored on Level 0 rather than decorating the cliff crest.

    scene = {
        'id': 'farmstead_scene_v0_3',
        'version': '0.9.0-w56h',
        'kind': 'worldgen_scene',
        'sceneId': 'farmstead',
        'title': 'Estate',
        'canonicalDisplayName': 'Estate',
        'legacySceneId': 'farmstead',
        'sceneKind': 'exterior',
        'biome': 'temperate',
        'role': 'player_home_estate',
        'sceneSize': [W, H],
        'tileSize': [32, 32],
        'edgePolicy': {
            'mustAvoidVoid': True,
            'boundedEstate': True,
            'fixedEntranceSide': 'south',
            'expandThroughEntranceSide': False,
            'resolvedBorders': {
                'north': 'decorative_highland',
                'south': 'decorative_highland_with_fixed_gate',
                'east': 'decorative_highland',
                'west': 'decorative_highland',
            },
        },
        'layers': {'terrain': terrain, 'structuralLevels': levels, 'zones': zones},
        'objects': objects,
        'transitions': [
            {'id': 'to_north_road', 'rect': [46, 62, 5, 2], 'toScene': 'north_road', 'toSpawn': [48, 46], 'returnRequired': True, 'returnTransitionId': 'to_farmstead'},
            {'id': 'to_cave_mouth', 'rect': [78, 10, 1, 1], 'toScene': 'cave_mouth', 'toSpawn': [48, 44], 'returnRequired': True, 'returnTransitionId': 'to_farmstead'},
        ],
        'spawns': [
            {'id': 'player_default', 'tile': [48, 55]},
            {'id': 'from_shared_world', 'tile': [48, 57]},
            {'id': 'from_cave', 'tile': [78, 11]},
        ],
        'estate': {
            'authority': 'content/estates/home_estate_contract_v1.json',
            'canonicalInstanceIdPolicy': 'per_player_portable',
            'fixedEntranceSide': 'south',
            'expandableDirections': ['north', 'east', 'west'],
            'initialBuildableRect': [10, 10, 76, 48],
            'starterCottageBuildingInstanceId': 'havenwild.estate.dev.starter_cottage',
            'starterCottagePolicy': 'development_fixture_or_progression_unlock',
            'composition': {
                'profile': 'w53e_edge_woodland_clear_center',
                'centralBuildPad': [31, 22, 40, 28],
                'cottageReservedRect': [53, 26, 12, 13],
                'gardenZone': [12, 26, 20, 16],
                'treeCount': len(tree_pos),
                'shrubCount': len(shrubs),
                'boulderCount': len(boulders),
                'forageCount': len(forage),
            },
            'quarantinedLegacyKindsExcluded': ['well', 'scarecrow', 'bench', 'log', 'greenhouse_marker', 'sign'],
        },
        'editor': {
            'showLayers': ['terrain', 'structural_levels', 'zones', 'objects', 'buildings', 'collision', 'interactions', 'transitions', 'scene_edges'],
            'defaultTool': 'inspect_select',
            'allowPaintTerrain': True,
            'allowMoveObjects': True,
            'allowBuildingInstanceAuthoring': True,
            'generatedBy': 'tools/automation/worldgen/Build-HomeEstateSceneW53.py',
            'generationSeed': SEED,
            'generationProfile': 'estate_generation_profile_v1',
            'legacyReferenceOnly': False,
            'terrainStyleLane': 'published_v7_lpc_authority',
            'displayName': 'Estate',
        },
        'validationRules': [
            'scene_size_matches_layers',
            'no_void_scene_edges',
            'fixed_south_entrance_remains_open',
            'decorative_highland_border_unreachable',
            'explicit_level2_highland_border',
            'cave_mouth_uses_exact_published_connector',
            'cave_transition_triggers_from_clear_approach_tile',
            'cave_return_spawn_is_outside_estate_transition_rect',
            'level2_highland_uses_grass_top_surface_not_mountainrock_plate',
            'south_cliff_crest_has_no_fence_band',
            'cave_aperture_is_1x2_on_level2_face',
            'all_object_asset_ids_resolve_published_world_assets',
            'quarantined_legacy_visuals_absent',
            'edge_woodland_preserves_central_build_pad',
            'object_clusters_preserve_gate_home_cave_routes',
            'starter_cottage_materializes_from_building_instance_registry',
            'no_separate_tavern_interior_transition',
            'user_facing_name_is_estate',
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scene, indent=2) + '\n', encoding='utf-8')
    print(f'WROTE {OUT.relative_to(ROOT)} objects={len(objects)} trees={len(tree_pos)} shrubs={len(shrubs)} boulders={len(boulders)} forage={len(forage)}')


if __name__ == '__main__':
    main()
