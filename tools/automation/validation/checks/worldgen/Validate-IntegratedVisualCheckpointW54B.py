#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def load(rel):
    p=ROOT/rel
    if not p.is_file(): raise AssertionError(f'missing {rel}')
    return json.loads(p.read_text(encoding='utf-8'))
def text(rel):
    p=ROOT/rel
    if not p.is_file(): raise AssertionError(f'missing {rel}')
    return p.read_text(encoding='utf-8')
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    cp=load('content/build/w54b_integrated_visual_checkpoint_v1.json')
    scene=load('content/worldgen/scenes/home_island/farmstead_scene_v0_3.json')
    cliff=load('content/terrain/cliff_height_runtime_contract_v1.json')
    exterior=load('content/buildings/exterior_grammar_contract_v1.json')
    recipe=load('content/buildings/recipes/estate_starter_cottage_v1.json')
    icat=load('content/buildings/building_instance_catalog_v1.json')
    pack=load('content/worldgen/packs/worldgen_home_island_test_v0_11.json')
    runtime=text('crates/haven_game/src/runtime_content_authority.rs')
    build_sh=text('tools/build/Build.sh')
    registry=text('tools/control/ProjectCommandRegistry.ps1')
    req(cp.get('pass')=='167Z109W54B','integrated checkpoint pass drifted')
    req(cliff['acceptance']['requiredDrops']==[1,2,3,4],'W53D 1/2/3/4 cliff acceptance missing')
    levels=scene['layers']['structuralLevels']; req(max(v for row in levels for v in row)==2,'Estate no longer has Level-2 highland')
    req(scene['estate']['composition']['treeCount']>=28 and scene['estate']['composition']['boulderCount']>=8,'W53E Estate composition was not retained')
    req(scene['estate']['starterCottagePolicy']=='development_fixture_or_progression_unlock','Estate cottage is not active as optional candidate')
    roof=recipe['roof']; req(roof.get('mode') in ('flat_nine_slice','authored_module'),'Estate cottage exact roof publication missing')
    req(next(e['status'] for e in icat['entries'] if e['id']=='havenwild.estate.dev.starter_cottage')=='candidate','starter cottage instance is not active candidate')
    req(exterior['rules']['wrongFacingWallReuseForbidden'] is True,'building facing fail-closed rule missing')
    req('DEV — W54D2 Estate |' in runtime and 'visual_test_active: true' in runtime,'runtime Estate visual-test identity/authority is missing')
    acc='content/worldgen/scenes/world_asset_acceptance/cliff_height_w53d_acceptance_scene_v1.json'
    req(acc in pack['sceneFiles'] and pack['testWorld']['cliffHeightAcceptanceSceneId']=='cliff_height_w53d_acceptance','W53D acceptance scene not registered')
    for cmd in ('cliff-height-grammar)','estate-composition)','building-exterior)','visual-checkpoint)'):
        req(cmd in build_sh,f'Build.sh missing W54B command {cmd}')
    for option in ("Id='55'","Id='56'","Id='57'","Id='58'"):
        req(option in registry,f'Control Center missing {option}')
    print('PASS W54B integrated visual checkpoint (forward-compatible)')
    print('- W53D cliff grammar and W53E Estate composition remain present while later cottage visual publications are allowed')
except Exception as exc:
    print(f'FAIL W54B integrated visual checkpoint: {exc}',file=sys.stderr); sys.exit(1)
