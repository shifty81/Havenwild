#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / 'content/buildings/building_recipe_catalog_v1.json'
AUTHORITY = ROOT / 'content/buildings/building_recipe_authority_v1.json'
MATERIAL = ROOT / 'content/buildings/building_recipe_materialization_contract_v1.json'
RECIPE = ROOT / 'content/buildings/recipes/three_level_house_prototype_v1.json'
VISIBILITY = ROOT / 'content/buildings/building_level_visibility_contract_v1.json'
SCENE = ROOT / 'content/worldgen/scenes/world_asset_acceptance/building_recipe_acceptance_scene_v1.json'
TEST_PACK = ROOT / 'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
RUST = ROOT / 'crates/haven_assets/src/building_recipe.rs'
LIB = ROOT / 'crates/haven_assets/src/lib.rs'
CATEGORY = ROOT / 'crates/haven_assets/src/category_metadata.rs'
BUILDER = ROOT / 'tools/automation/assets/Build-BuildingRecipeAcceptanceSceneV1.py'


def need(value, message):
    if not value:
        raise SystemExit('FAIL W46A building recipe authority: ' + message)


def world_pass_at_least(value, minimum):
    import re
    match=re.search(r'w(\d+)', str(value or ''), re.IGNORECASE)
    return bool(match and int(match.group(1)) >= minimum)

def load(path: Path):
    need(path.is_file(), f'missing {path.relative_to(ROOT)}')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def published_entries() -> dict[str, dict]:
    result = {}
    base = ROOT / 'content/asset_packs/havenwild_objects'
    for path in sorted(base.glob('published*.json')):
        data = load(path)
        if data.get('schema') not in {'havenwild.published_world_asset_catalog.v1', 'havenwild.placeable_catalog.v1'}:
            continue
        for entry in data.get('entries', []):
            result[entry['id']] = entry
            result[entry.get('semantic_id', entry['id'])] = entry
            for alias in entry.get('aliases', []):
                result[alias] = entry
    return result


def referenced_assets(recipe: dict) -> set[str]:
    refs = set()
    for level in recipe['levels']:
        refs |= {fill['assetId'] for fill in level.get('floorFills', [])}
        refs |= {wall['visualAssetId'] for wall in level.get('wallRuns', []) if wall.get('visualAssetId')}
        refs |= {opening['assetId'] for opening in level.get('openings', [])}
    refs |= {connector['assetId'] for connector in recipe.get('connectors', [])}
    roof = recipe['roof']
    refs |= set((roof.get('components') or {}).values())
    if roof.get('authoredModuleAssetId'):
        refs.add(roof['authoredModuleAssetId'])
    refs |= {m['assetId'] for m in roof.get('authoredModules', [])}
    return refs


def main() -> int:
    catalog = load(CATALOG); authority = load(AUTHORITY); material = load(MATERIAL)
    recipe = load(RECIPE); visibility = load(VISIBILITY); scene = load(SCENE); pack = load(TEST_PACK)
    need(BUILDER.is_file(), 'acceptance-scene builder missing')
    need(RUST.is_file(), 'Rust BuildingRecipe authority missing')

    need(catalog.get('schema') == 'havenwild.building_recipe_catalog.v1', 'catalog schema drift')
    need(world_pass_at_least(catalog.get('pass'),46), 'catalog pass drift')
    need(catalog.get('authority') == 'BuildingRecipeRegistry', 'catalog authority drift')
    entries = {entry.get('id'): entry for entry in catalog.get('entries', [])}
    need(entries.get('havenwild.prototype.three_level_house') == {
        'id': 'havenwild.prototype.three_level_house',
        'path': 'content/buildings/recipes/three_level_house_prototype_v1.json',
        'status': 'candidate',
    }, 'diagnostic three-level prototype entry drift')

    need(authority.get('schema') == 'havenwild.building_recipe_authority.v1', 'authority contract schema drift')
    need(authority.get('authority') == 'BuildingRecipeRegistry', 'BuildingRecipeRegistry not authoritative')
    need(authority.get('visualIdentityAuthority') == 'PublishedWorldAssetRegistry', 'visual identity must remain PublishedWorldAssetRegistry')
    rules = authority.get('rules', {})
    need(rules.get('ordinaryInteriorPolicy') == 'same_world_building_instance', 'ordinary interior policy regressed')
    need(rules.get('ordinaryUpperFloorsRemainSameInstance') is True, 'upstairs split into another instance')
    need(rules.get('ordinaryBasementsRemainSameInstance') is True, 'basement split into another instance')
    need(rules.get('cutawayIsCameraLocalPresentation') is True, 'cutaway is no longer camera-local')
    need(rules.get('missingVisualMustFailClosed') is True, 'missing visuals no longer fail closed')
    need(rules.get('deferredVisualStatus') == 'deferred_exact_facing', 'deferred visual marker drift')

    need(material.get('schema') == 'havenwild.building_recipe_materialization_contract.v1', 'materialization contract schema drift')
    mrules = material.get('rules', {})
    need(mrules.get('deferredFacingWallEmitsNoWrongVisual') is True, 'materializer permits wrong-facing wall substitution')
    need(mrules.get('flatNineSliceRoofUsesExactTopologyRoles') is True, 'roof materialization lost topology role authority')
    need(mrules.get('materializedPieceReferencesPublishedWorldAssetByCanonicalAlias') is True, 'materialized visual identity duplicated outside PublishedWorldAssetRegistry')

    need(recipe.get('schema') == 'havenwild.building_recipe.v1', 'recipe schema drift')
    need(recipe.get('id') == 'havenwild.prototype.three_level_house', 'recipe identity drift')
    need(recipe.get('classification', {}).get('diagnosticOnly') is True, 'prototype must remain diagnostic-only')
    need(recipe.get('footprint') == [9, 7], 'prototype footprint drift')
    need(recipe.get('defaultLevel') == 0, 'default structural level must remain ground level 0')
    levels = recipe.get('levels', [])
    need([level['level'] for level in levels] == [-1, 0, 1], 'prototype must exercise cellar/ground/upstairs as -1/0/+1')
    need([level['id'] for level in levels] == ['cellar', 'ground', 'upstairs'], 'level identities drift')
    persistence = recipe.get('persistence', {})
    need(persistence.get('interiorPolicy') == 'same_world_building_instance', 'recipe interior policy regressed')
    need(persistence.get('allLevelsAuthoritative') is True, 'all levels must remain simulated/authoritative')
    need(persistence.get('separateScene') is False, 'ordinary prototype cannot use separate scene')
    need(persistence.get('portableInstanceIdentity') is True, 'building instance identity must remain persistence-safe')
    need('interiorScene' not in json.dumps(recipe), 'legacy interiorScene authority leaked into recipe')
    need('ObjectKind' not in json.dumps(recipe), 'ObjectKind leaked into BuildingRecipe visual identity')

    connectors = recipe.get('connectors', [])
    need({(c['fromLevel'], c['toLevel']) for c in connectors} == {(-1, 0), (0, 1)}, 'stair connectors do not cover basement/ground/upstairs')
    need(all(c['assetId'] == 'stairs_short_run_gray' and c.get('reversible') is True for c in connectors), 'connector component/reversibility drift')
    roof = recipe.get('roof', {})
    need(roof.get('mode') == 'flat_nine_slice', 'initial roof must exercise exact flat-nine-slice resolver')
    need(roof.get('family') == 'roof.flat_shingle_a.gray', 'initial exact roof family drift')
    need(roof.get('cameraLocalOcclusion') is True, 'recipe roof cutaway must remain local to camera')
    expected_roof = {
        'field': ('roof_flat_gray_field', 'field'),
        'northEdge': ('roof_flat_gray_north_eave', 'north_eave'),
        'southEdge': ('roof_flat_gray_south_eave', 'south_eave'),
        'westEdge': ('roof_flat_gray_west_edge', 'west_rake'),
        'eastEdge': ('roof_flat_gray_east_edge', 'east_rake'),
        'northWestCorner': ('roof_flat_gray_corner_nw', 'outer_corner_nw'),
        'northEastCorner': ('roof_flat_gray_corner_ne', 'outer_corner_ne'),
        'southWestCorner': ('roof_flat_gray_corner_sw', 'outer_corner_sw'),
        'southEastCorner': ('roof_flat_gray_corner_se', 'outer_corner_se'),
    }
    need(set(roof.get('components', {})) == set(expected_roof), 'roof component-role set drift')

    published = published_entries()
    for asset_id in referenced_assets(recipe):
        need(asset_id in published, f'recipe references unknown PublishedWorldAsset {asset_id}')
        entry = published[asset_id]
        need(entry.get('certification') not in {'rejected', 'missing', 'placeholder'}, f'recipe references unusable component {asset_id}')
        need(entry.get('structure'), f'recipe references non-structural component {asset_id}')
    for key, (asset_id, topology_role) in expected_roof.items():
        need(roof['components'][key] == asset_id, f'roof {key} component drift')
        need(published[asset_id]['structure']['topology_role'] == topology_role, f'roof {asset_id} topology role mismatch')
    need(published['stairs_short_run_gray']['structure']['level_delta'] == 1, 'stair component level_delta drift')

    for level in levels:
        deferred = [wall for wall in level.get('wallRuns', []) if not wall.get('visualAssetId')]
        need(all(wall.get('visualStatus') == 'deferred_exact_facing' for wall in deferred), f'{level["id"]} has a silent missing wall visual')
        resolved = [wall for wall in level.get('wallRuns', []) if wall.get('visualAssetId')]
        need(all(wall['edge'] == 'south' and wall['visualAssetId'] == 'wall_drywall_simple' for wall in resolved), 'wrong-facing wall visual substitution detected')
        need(level.get('rooms'), f'{level["id"]} has no room zone')
    need({o['kind'] for o in levels[1]['openings']} == {'door', 'window'}, 'ground floor must exercise door/window openings')

    need(visibility.get('defaultInteriorPolicy') == 'same_world_building_instance', 'W45C visibility contract regressed')
    need(visibility.get('cameraPresentation', {}).get('visibilityIsPerClientCamera') is True, 'W45C camera-local visibility contract regressed')

    rust = RUST.read_text(encoding='utf-8')
    need('pub struct BuildingRecipeRegistry' in rust, 'Rust registry type missing')
    need('pub struct BuildingRecipeDefinition' in rust, 'Rust recipe definition missing')
    need('materialize_structural_pieces' in rust, 'Rust deterministic materializer missing')
    need('validate_against_assets' in rust, 'Rust PublishedWorldAsset validation missing')
    need('same_world_building_instance' in rust, 'Rust same-world policy guard missing')
    need('deferred_exact_facing' in rust, 'Rust fail-closed wall-facing guard missing')
    need('pub mod building_recipe;' in LIB.read_text(encoding='utf-8'), 'haven_assets does not export building_recipe module')
    category = CATEGORY.read_text(encoding='utf-8')
    need('pub building_recipe: Option<String>' in category, 'BuildingMetadata lacks W46 recipe reference')
    need('Ordinary interiors/upstairs/basements use building_recipe instead' in category, 'legacy interior_scene semantics are not documented')

    object_pack = load(ROOT / 'content/asset_packs/havenwild_objects/pack.json')
    need(object_pack.get('version') in {'0.7.0-w46a', '0.8.0-w46b'} or world_pass_at_least(object_pack.get('version'),46), 'havenwild_objects pack version predates W46A authority')
    sources = {source.get('id'): source for source in object_pack.get('sources', [])}
    need(sources.get('building_recipe_catalog_w46a', {}).get('path') == CATALOG.relative_to(ROOT).as_posix(), 'building recipe catalog sidecar missing from object pack')
    semantic = {(asset.get('semantic_id'), asset.get('category')): asset for asset in object_pack.get('assets', [])}
    recipe_asset = semantic.get(('building.recipe.catalog.default', 'editor_template'))
    need(recipe_asset is not None, 'building recipe catalog is not discoverable as an editor template')
    need(recipe_asset.get('metadata', {}).get('authority') == 'BuildingRecipeRegistry', 'pack recipe authority drift')
    need(recipe_asset.get('metadata', {}).get('visualAuthority') == 'PublishedWorldAssetRegistry', 'pack visual authority drift')

    need(scene.get('sceneId') == 'building_recipe_acceptance' and scene.get('role') == 'diagnostic_only', 'acceptance scene identity drift')
    acc = scene.get('acceptance', {})
    need(acc.get('pass') == '167Z109W46A', 'acceptance pass drift')
    need(acc.get('buildingRecipeId') == recipe['id'], 'acceptance scene recipe mismatch')
    need(acc.get('buildingAuthority') == 'BuildingRecipeRegistry', 'acceptance scene building authority drift')
    need(acc.get('visualAuthority') == 'PublishedWorldAssetRegistry', 'acceptance scene visual authority drift')
    need(acc.get('structuralLevels') == [-1, 0, 1], 'acceptance scene does not exercise all three levels')
    need(acc.get('candidateCount') == len(scene.get('objects', [])) == 199, 'acceptance materialization count drift')
    need({o.get('assetId') for o in scene['objects']} <= set(published), 'acceptance scene contains an unresolved published asset')

    rel = SCENE.relative_to(ROOT).as_posix(); exact_rel = 'content/worldgen/scenes/world_asset_acceptance/structure_exact_modules_acceptance_scene_v1.json'
    need(rel in pack.get('sceneFiles', []) and rel in pack.get('smokeTests', []), 'building recipe acceptance not in sceneFiles/smokeTests')
    need(exact_rel in pack.get('sceneFiles', []) and exact_rel in pack.get('smokeTests', []), 'W45D2 exact-module acceptance remains undiscoverable')
    tw = pack.get('testWorld', {})
    need(tw.get('buildingRecipeAcceptanceSceneId') == 'building_recipe_acceptance', 'test-world recipe navigation id missing')
    need(tw.get('buildingRecipeAcceptanceScene') == rel, 'test-world recipe navigation path missing')

    print('PASS W46A BuildingRecipe authority foundation')
    print('- one BuildingRecipeRegistry owns structural assembly; PublishedWorldAssetRegistry remains visual/source authority')
    print('- diagnostic prototype exercises cellar -1, ground 0, upstairs +1 in one same-world BuildingInstance')
    print('- unresolved north/east/west wall visuals fail closed instead of substituting the south-facing wall art')
    print('- exact flat-nine-slice roof and stair connectors are validated against PublishedWorldAsset topology')
    print('- building_recipe_acceptance materializes 199 evidence-backed visual pieces for editor/client inspection')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
