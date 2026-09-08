#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[5]


def req(value, message):
    if not value:
        raise AssertionError(message)


def load(rel):
    path = ROOT / rel
    req(path.is_file(), f"missing {rel}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


try:
    authority = (ROOT / "crates/haven_game/src/runtime_content_authority.rs").read_text(encoding="utf-8")
    bootstrap = (ROOT / "crates/haven_game/src/game_bootstrap.rs").read_text(encoding="utf-8")
    entry = (ROOT / "crates/haven_game/src/client_entry.rs").read_text(encoding="utf-8")
    main = (ROOT / "crates/haven_game/src/main.rs").read_text(encoding="utf-8")
    scene_nav = (ROOT / "crates/haven_game/src/runtime_scene_navigation.rs").read_text(encoding="utf-8")
    runtime_draw = (ROOT / "crates/haven_game/src/runtime_draw.rs").read_text(encoding="utf-8")
    build = (ROOT / "tools/build/Build.sh").read_text(encoding="utf-8")
    commands = (ROOT / "tools/control/ProjectCommandRegistry.ps1").read_text(encoding="utf-8")
    pack = load("content/worldgen/packs/worldgen_home_island_test_v0_11.json")
    nav = load("content/worldgen/home_island_navigation_graph_v0_4.json")
    estate = load("content/worldgen/scenes/home_island/farmstead_scene_v0_3.json")
    cottage = load("content/buildings/recipes/estate_starter_cottage_v1.json")

    req('mod runtime_content_authority;' in main, "runtime content authority module not registered")
    for token in [
        'CONTENT_AUTHORITY_REVISION: &str = "167Z109W53B"',
        'legacy_scene_bank_rebased',
        'pre-w53b-content-authority',
        'filter_legacy_world_paint_deltas',
        'REFRESHED_LEGACY_SCENES',
        'RETIRED_INTERIOR_SCENES',
        'save_world_to_path(&save_paths.world, world)',
        'EstateVisualTest',
    ]:
        req(token in authority, f"runtime content convergence missing {token}")
    req('converge_runtime_content_authority' in bootstrap, "Game bootstrap does not converge scene content authority")
    req('content_authority.visual_test_active' in bootstrap, "visual test does not isolate persistent building deltas")
    req('Character scene {} is retired/unavailable' in bootstrap, "stale character scene relocation missing")
    req('content_authority.rebased_saved_world' in bootstrap, "rebased saved-world character relocation missing")
    req('canonical_authored_scene' in authority, "current authored scene reload helper missing")
    req('current authored W53B authority' in scene_nav, "scene reset can still manufacture stale starter terrain")
    req('use Control Center option 53' in scene_nav, "authored scene runtime regeneration is not blocked")
    req('Dev scene jump blocked' in scene_nav, "retired scene jump still panics instead of failing closed")
    req('if self.dev_mode {' in runtime_draw and 'self.draw_ui();' in runtime_draw, "developer diagnostics are not F3-gated")
    req(any(badge in runtime_draw for badge in ('DEV — W53B Estate Visual Test','DEV — W53C Estate Visual Test','DEV — W54B Estate Visual Test','DEV — W54D2 Estate Visual Test','DEV — W54E Estate Visual Test','DEV — W54F Estate Visual Test','DEV — W54G Estate Visual Test')), "clean visual test lacks a bounded identity badge")
    req('ESTATE_VISUAL_TEST_ARG' in entry and '--estate-visual-test' in entry, "isolated Estate client argument missing")
    req('world_w53b_estate_visual_test' in entry, "Estate visual test does not use isolated world id")
    req('character_w53b_estate_visual_test' in entry, "Estate visual test does not use isolated character id")
    req('estate-visual-test)' in build and '--estate-visual-test' in build, "Build.sh Estate visual test command missing")
    req("Id='54'" in commands and 'Run integrated Estate visual test' in commands, "Control Center option 54 missing")

    req(pack.get('version') in {'0.11.1-w53b','0.11.2-w54b'}, "home-island visual pack lineage mismatch")
    req(pack.get('requiresLegacySceneSet') is False, "W53B visual pack must not require retired interior scenes")
    retired_paths = {
        'content/worldgen/scenes/home_island/tavern_interior_scene_v0_3.json',
        'content/worldgen/scenes/home_island/cellar_scene_v0_3.json',
        'content/worldgen/scenes/home_island/guest_floor_scene_v0_3.json',
    }
    req(retired_paths.isdisjoint(pack.get('sceneFiles', [])), "retired parallel interior scene remains in W53B sceneFiles")
    req(retired_paths.isdisjoint(pack.get('smokeTests', [])), "retired parallel interior scene remains in W53B smokeTests")

    nav_ids = {node.get('sceneId') for node in nav.get('nodes', [])}
    req({'tavern_interior', 'cellar', 'guest_floor'}.isdisjoint(nav_ids), "retired interior remains in navigation graph")
    req(nav.get('ordinaryInteriorPolicy') == 'same_world_building_instance', "navigation graph lost same-world interior policy")

    req(estate.get('title') == 'Estate', "Estate title regressed")
    asset_ids = [obj.get('assetId') for obj in estate.get('objects', [])]
    tree_count = sum(1 for asset in asset_ids if isinstance(asset, str) and asset.startswith('tree_'))
    boulder_count = sum(1 for asset in asset_ids if isinstance(asset, str) and 'boulder' in asset)
    ground_flora_count = sum(1 for asset in asset_ids if isinstance(asset, str) and (asset.startswith('forage_') or asset.startswith('flora_') or asset.startswith('shrub_')))
    req(tree_count >= 18, f"Estate authored tree population regressed: {tree_count}")
    req(boulder_count >= 4, f"Estate authored boulder population regressed: {boulder_count}")
    req(ground_flora_count >= 10, f"Estate authored shrub/forage/flora population regressed: {ground_flora_count}")

    roof = cottage.get('roof', {})
    cottage_version = cottage.get('version')
    if cottage_version == '1.0.1-w53b':
        req(cottage.get('footprint') == [5, 5], "historical W53B cottage footprint drifted")
        req(roof.get('mode') == 'authored_module' and roof.get('authoredModuleAssetId') == 'roof_gable_shingle_brown_module', "historical W53B gable experiment drifted")
    elif cottage_version == '1.1.0-w54a':
        req(cottage.get('footprint') == [5, 6], "historical W54A cottage footprint drifted")
        req(roof.get('mode') == 'flat_nine_slice' and roof.get('family') == 'roof.flat_shingle_a.brown', "historical W54A replacement roof drifted")
        req((ROOT / 'content/buildings/exterior_grammar_contract_v1.json').is_file(), "forward cottage lacks explicit exterior grammar contract")
    elif cottage_version == '1.2.0-w54e':
        req(cottage.get('footprint') == [8, 6], "historical W54E two-room footprint drifted")
        req(roof.get('mode') == 'authored_module' and roof.get('family') == 'roof.hipped_shingle_a.brown.twin_module', "historical W54E authored hipped roof missing")
        req(len(roof.get('authoredModules', [])) == 2, "historical W54E cottage must keep both authored hipped roof modules")
        req((ROOT / 'content/buildings/exterior_grammar_contract_v1.json').is_file(), "forward cottage lacks explicit exterior grammar contract")
    elif cottage_version in {'1.3.0-w54f','1.4.0-w54g'}:
        req(cottage.get('footprint') == [10, 8], "historical W54F/W54G reconstructed two-room shell drifted")
        req(roof.get('mode') == 'authored_module' and roof.get('family') == 'roof.gable_shingle_a.brown.joined_twin_module', "historical W54F joined twin-gable roof missing")
        req(len(roof.get('authoredModules', [])) == 2, "historical W54F cottage must keep two edge-adjacent authored gable modules")
        req((ROOT / 'content/buildings/exterior_grammar_contract_v1.json').is_file(), "forward cottage lacks explicit exterior grammar contract")
    else:
        req(cottage_version in {'1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'} and cottage.get('footprint') == [9, 9], "forward cottage must use W57K8 9x9 architectural envelope")
        req(roof.get('mode') == 'authored_module' and roof.get('family') == 'roof.gable_shingle_a.brown.shallow_7x4.front_gable_roofline_with_infill', "W57K8 front-gable roofline family missing")
        req(len(roof.get('authoredModules', [])) == 1 and roof['authoredModules'][0].get('assetId') == 'roof_gable_shingle_brown_shallow_7x4_roofline', "W57K8 starter cottage must consume one exact front-gable roofline")
        req((ROOT / 'content/buildings/exterior_grammar_contract_v1.json').is_file(), "forward cottage lacks explicit exterior grammar contract")
    furnishings = [f for level in cottage.get('levels', []) for f in level.get('furnishings', [])]
    req(len(furnishings) == (6 if cottage_version in {'1.2.0-w54e','1.3.0-w54f','1.4.0-w54g','1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'} else 4), "starter cottage furnishing layout drifted")

    print('PASS W53B runtime scene/content convergence repair')
    print(f'- Estate source proves current population: {tree_count} trees, {boulder_count} boulders, {ground_flora_count} shrubs/forage/flora')
    print('- old saved legacy SceneMaps rebase once per W53B content revision with backups and legacy-paint filtering')
    print('- Tavern/Cellar/Guest Floor parallel scenes are retired in favor of same-world BuildingInstance levels')
    print('- isolated option 54 visual test bypasses normal saves and forces current authored Estate content')
    print('- authored-scene reset reloads current source; retired starter regeneration and missing-scene jump fail closed')
    print('- full diagnostics are F3/dev-only; production view keeps the bottom HUD and a tiny isolated-test badge only')
    print('- historical cottage layouts remain recognized; W57K8 advances the starter cottage to one front-gable roofline over an independent 9x9 architectural envelope')
except Exception as exc:
    print(f'FAIL W53B runtime scene/content convergence repair: {exc}', file=sys.stderr)
    sys.exit(1)
