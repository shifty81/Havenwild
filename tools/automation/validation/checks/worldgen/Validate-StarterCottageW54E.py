#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    recipe=load('content/buildings/recipes/estate_starter_cottage_v1.json')
    inst=load('content/buildings/instances/estate_starter_cottage_v1.json')
    contract=load('content/buildings/exterior_grammar_contract_v1.json')
    profile=load('content/estates/estate_generation_profile_v1.json')
    version=recipe.get('version')
    req(version in {'1.2.0-w54e','1.3.0-w54f','1.4.0-w54g','1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'},'starter cottage lost recognized W54E+ lineage')
    level=recipe['levels'][0]
    rooms={r['id']:r for r in level['rooms']}
    req(set(rooms)=={'bedroom','main_room'},'starter cottage must contain semantic bedroom + main_room')
    req(rooms['main_room']['label']=='Living / Crafting / Cooking','starter-home main-room program drifted')
    req(rooms['bedroom']['label'] in {'Bedroom','Bedroom Nook'},'starter-home bedroom semantic program drifted')
    req(any(w['edge']=='south' and w.get('visualAssetId') for w in level['wallRuns']),'exact south frontage missing')
    for side in ('north','east','west'):
        wall=next(w for w in level['wallRuns'] if w['id']==side)
        req(wall.get('visualAssetId') is None and wall.get('visualStatus')=='deferred_exact_facing' and wall.get('blocksMovement') is True,f'{side} must remain fail-closed')
    cut={x['id'] for x in recipe['cutawayGroups']}
    req(cut=={'building.roof.estate_cottage','building.wall_front.estate_cottage'},'starter-home cutaway must hide only roof + front facade')

    if version=='1.2.0-w54e':
        req(recipe['footprint']==[8,6] and inst['anchorTile']==[55,29],'historical W54E geometry drifted')
        req(recipe['roof']['family']=='roof.hipped_shingle_a.brown.twin_module','historical W54E roof drifted')
    elif version in {'1.3.0-w54f','1.4.0-w54g'}:
        req(recipe['footprint']==[10,8] and inst['anchorTile']==[54,29],'historical W54F/G reconstructed shell geometry drifted')
        req(recipe['roof']['family']=='roof.gable_shingle_a.brown.joined_twin_module','historical W54F/G joined roof drifted')
        req(any((w['id']=='room_divider' and w.get('visualAssetId')=='wall_drywall_simple') or w['id'].startswith('divider_cap_') for w in level['wallRuns']),'historical visible interior divider authority missing')
    else:
        req(recipe['footprint']==[9,9] and inst['anchorTile']==[55,28],'W57K8 architectural envelope/anchor drifted')
        roof=recipe['roof']
        req(roof['family']=='roof.gable_shingle_a.brown.shallow_7x4.front_gable_roofline_with_infill','W57K8 front-gable family drifted')
        req(len(roof.get('authoredModules',[]))==1 and roof['authoredModules'][0]['assetId']=='roof_gable_shingle_brown_shallow_7x4_roofline','W57K8 must consume one exact roofline module')
        req(not any(w['id']=='room_divider' or w['id'].startswith('divider_cap_') for w in level['wallRuns']),'W57K8 linked interior must remain open-plan')
        gable=[w for w in level['wallRuns'] if w['id'].startswith('gable_fill_')]
        by_id={w['id']:w for w in gable}
        req(by_id['gable_fill_peak']['start']==[4,3] and by_id['gable_fill_peak']['length']==1,'W57K8+ gable peak row drifted')
        req(by_id['gable_fill_mid']['start']==[3,4] and by_id['gable_fill_mid']['length']==3,'W57K8+ gable middle row drifted')
        base=[w for w in gable if w['start'][1]==5]
        req(sum(w['length'] for w in base)==5 and min(w['start'][0] for w in base)==2,'W57K8+ gable infill must retain five-cell triangular base')
        req(all((w.get('visualAssetId') or '').startswith('wall_siding_plain_cream_gable_fill') and w.get('blocksMovement') is False for w in gable),'W57K8+ gable infill must be visual-only exact siding family')
        nav=level.get('navigation',{})
        req(nav.get('protectedTiles')==[[4,8],[4,7],[4,6],[4,5],[4,4],[4,3],[4,2]],'W57K8 reserved entry circulation drifted')

    req(contract.get('pass') in {'167Z109W54E','167Z109W54F','167Z109W54G','167Z109W57K8'},'Estate exterior authority lineage drifted')
    req(profile.get('pass') in {'167Z109W54E','167Z109W54F','167Z109W57K8'},'Estate generation profile lineage drifted')
    print('PASS W54E starter cottage program (forward-compatible through W57K10)')
    print('- semantic Bedroom + Living/Crafting/Cooking program remains mandatory')
    print('- W57K8 narrows the wall plate beneath a source-authored front-gable roofline and reserves entry circulation')
except Exception as exc:
    print(f'FAIL W54E starter cottage program: {exc}',file=sys.stderr); sys.exit(1)
