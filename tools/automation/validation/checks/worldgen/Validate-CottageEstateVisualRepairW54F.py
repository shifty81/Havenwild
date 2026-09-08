#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def text(rel): return (ROOT/rel).read_text(encoding='utf-8')
def req(ok,msg):
    if not ok: raise AssertionError(msg)
def in_rect(p,r):
    x,y=p; rx,ry,rw,rh=r
    return rx<=x<rx+rw and ry<=y<ry+rh
def published_assets():
    out={}
    for path in sorted((ROOT/'content/asset_packs/havenwild_objects').glob('published_*.json')):
        try: data=json.loads(path.read_text(encoding='utf-8-sig'))
        except Exception: continue
        if data.get('schema')!='havenwild.published_world_asset_catalog.v1': continue
        for e in data.get('entries',[]): out[e['id']]=e
    return out
try:
    recipe=load('content/buildings/recipes/estate_starter_cottage_v1.json')
    inst=load('content/buildings/instances/estate_starter_cottage_v1.json')
    contract=load('content/buildings/exterior_grammar_contract_v1.json')
    profile=load('content/estates/estate_generation_profile_v1.json')
    scene=load('content/worldgen/scenes/home_island/farmstead_scene_v0_3.json')
    runtime=text('crates/haven_game/src/runtime_content_authority.rs')
    published=published_assets()

    version=recipe.get('version')
    req(version in {'1.3.0-w54f','1.4.0-w54g','1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'},'W54F-or-later starter cottage version missing')
    level=recipe['levels'][0]
    rooms={r['id']:r for r in level['rooms']}
    openings={o['id']:o for o in level['openings']}
    walls={w['id']:w for w in level['wallRuns']}
    furn={f['id']:f for f in level['furnishings']}

    if version in {'1.3.0-w54f','1.4.0-w54g'}:
        req(recipe.get('footprint')==[10,8],'historical W54F/G cottage footprint drifted')
        req(inst.get('anchorTile')==[54,29],'historical W54F/G cottage anchor drifted')
        req(level['floorFills']==[{'assetId':'floor_wood_herringbone_light','rect':[1,1,8,6]}],'historical W54F/G floor shell drifted')
        req(rooms['bedroom']['rect']==[1,1,8,3] and rooms['main_room']['rect']==[1,4,8,3],'historical two-room rectangles drifted')
        req(openings['front_door']['tile']==[5,7] and openings['bedroom_door']['tile']==[5,4],'historical W54F/G door lane drifted')
        req([inst['anchorTile'][0]+5,inst['anchorTile'][1]+7]==[59,36],'historical front door world tile drifted')
        req(recipe['roof']['family']=='roof.gable_shingle_a.brown.joined_twin_module','historical joined-twin roof drifted')
    else:
        req(recipe.get('footprint')==[9,9],'W57K8 cottage architectural envelope must be 9x9')
        req(inst.get('anchorTile')==[55,28],'W57K8 cottage anchor must preserve the Estate doorway route')
        req(level['floorFills']==[{'assetId':'floor_wood_herringbone_light','rect':[1,1,7,7]}],'W57K8+ structural ground-floor fill drifted')
        req(rooms['bedroom']['rect']==[1,1,7,3] and rooms['main_room']['rect']==[1,4,7,4],'W57K8 open-plan room zones drifted')
        req(openings['front_door']['tile']==[4,8] and 'bedroom_door' not in openings,'W57K8 must use one unobstructed exterior door lane')
        req([inst['anchorTile'][0]+4,inst['anchorTile'][1]+8]==[59,36],'W57K8 front door must remain on Estate route endpoint [59,36]')
        req(not any(name=='room_divider' or name.startswith('divider_cap_') for name in walls),'W57K8 must not recreate the blocking interior divider')
        for side in ('north','east','west'):
            w=walls[side]
            req(w['visualAssetId'] is None and w['visualStatus']=='deferred_exact_facing' and w['blocksMovement'] is True,f'{side} must remain logical/fail-closed')
        req(walls['south_left']['start']==[2,8] and walls['south_repeat']['start']==[3,8] and walls['south_repeat']['length']==3 and walls['south_right']['start']==[6,8],'W57K8 centered five-tile frontage drifted')
        gable=[w for w in level['wallRuns'] if w['id'].startswith('gable_fill_')]
        gable_by_id={w['id']:w for w in gable}
        req(gable_by_id['gable_fill_peak']['start']==[4,3] and gable_by_id['gable_fill_peak']['length']==1,'W57K8+ gable peak drifted')
        req(gable_by_id['gable_fill_mid']['start']==[3,4] and gable_by_id['gable_fill_mid']['length']==3,'W57K8+ gable middle drifted')
        base=[w for w in gable if w['start'][1]==5]
        req(sum(w['length'] for w in base)==5 and min(w['start'][0] for w in base)==2,'W57K8+ gable infill must retain 1/3/5 geometry')
        req(all((w['visualAssetId'] or '').startswith('wall_siding_plain_cream_gable_fill') and w['blocksMovement'] is False and w['occlusionGroup'].startswith('building.gable_infill.') for w in gable),'W57K8+ gable infill authority drifted')

        roof=recipe['roof']; mods=roof['authoredModules']
        req(roof['mode']=='authored_module' and roof['family']=='roof.gable_shingle_a.brown.shallow_7x4.front_gable_roofline_with_infill','W57K8 front-gable roof family drifted')
        req([(m['id'],m['assetId'],m['tile']) for m in mods]==[('main_gable','roof_gable_shingle_brown_shallow_7x4_roofline',[4,5])],'W57K8 must use one front-gable roofline module')
        roof_asset=published.get('roof_gable_shingle_brown_shallow_7x4_roofline')
        fill_asset=published.get('wall_siding_plain_cream_gable_fill')
        req(roof_asset is not None and roof_asset['visual']['frames'][0]['source_rect']==[544,0,224,128],'W57K8 reviewed roofline source rect drifted')
        req(roof_asset.get('structure',{}).get('topology_role')=='front_gable_roofline','W57K8 roofline misclassified as a filled roof plane')
        req(fill_asset is not None and fill_asset['visual']['frames'][0]['source_rect']==[64,0,32,32],'W57K8 exact gable siding cell drifted')
        req(fill_asset.get('footprint',{}).get('blocks_movement') is False,'gable siding infill must be visual-only')
        socket=next(s for s in recipe['architecturalSockets'] if s['id']=='roof_wall_plate')['pixel']
        source=mods[0]['sourceSocketPx']
        req([socket[0]-source[0],socket[1]-source[1]]==[32,64],'W57K8 roof render origin drifted')
        req(not any(w.get('occlusionGroup','').startswith('building.gable_backing') for w in level['wallRuns']),'rectangular gable backing must remain forbidden')

        protected=level.get('navigation',{}).get('protectedTiles',[])
        req(protected==[[4,8],[4,7],[4,6],[4,5],[4,4],[4,3],[4,2]],'W57K8 protected entry lane drifted')
        req(all(f['tile'] not in protected for f in furn.values() if f.get('blocksNavigation')),'blocking furniture intersects the W57K8 protected entry lane')
        for f in furn.values():
            req(in_rect(tuple(f['tile']),rooms[f['roomId']]['rect']),f"{f['id']} is outside semantic room {f['roomId']}")

    levels=scene['layers']['structuralLevels']; terrain=scene['layers']['terrain']
    req(all(levels[0][x]==2 and terrain[0][x]=='Grass' for x in range(96)),'north highland must be Level-2 grass top')
    req(all(levels[y][0]==2 and terrain[y][0]=='Grass' for y in range(64)),'west highland must be Level-2 grass top')
    req(all(levels[y][95]==2 and terrain[y][95]=='Grass' for y in range(64)),'east highland must be Level-2 grass top')
    gate_ids=[o['id'] for o in scene['objects'] if o['id'].startswith('estate_gate_fence_') or o['id'].startswith('estate_gate_post_')]
    req(not gate_ids,f'old fence band still decorates the cliff crest: {gate_ids[:3]}')

    cave=profile['caveMouth']
    req(cave['apertureTiles']==[1,2] and cave['sourceEnvelopeTiles']==[1,3],'cave mouth must remain exactly 1 wide x 2 tall with 1x3 evidence envelope')
    req(cave['thresholdTile']==[78,9] and cave['interactionTile']==[78,10],'cave threshold/clear interaction approach split drifted')
    cave_obj=next(o for o in scene['objects'] if o['id']=='estate_cave_mouth')
    req(cave_obj['visualRect']==[78,6,1,3],'good cave mouth visual envelope changed')
    req(cave_obj['interactions'][0]['rect']==[78,10,1,1],'cave object interaction is not on clear approach tile')
    tr=next(t for t in scene['transitions'] if t['id']=='to_cave_mouth')
    req(tr['rect']==[78,10,1,1],'cave scene transition is not on clear approach tile')
    req(all(terrain[y][78]=='Dirt' for y in (9,10,11)),'cave receiver/approach apron must use a quiet dirt blend')

    req(contract.get('pass') in {'167Z109W54F','167Z109W54G','167Z109W57K8'},'exterior contract forward lineage drifted')
    req(profile.get('pass') in {'167Z109W54F','167Z109W57K8'},'Estate generation profile must retain W54F terrain/cave authority through K8')
    req('DEV — W54D2 Estate |' in runtime and 'visual_test_active: true' in runtime,'Estate visual-test runtime identity/authority missing')
    print('PASS W54F cottage/Estate visual reconstruction (forward-compatible through W57K10)')
    if version in {'1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'}:
        print('- 9x9 architectural envelope: centered 5-tile wall plate + one source-authored front-gable roofline + 1/3/5 gable siding infill')
        print('- linked interior is open-plan with a 7x7 floor and protected center circulation; no blocking divider remains')
    print('- Estate Level-2 highland and exact cave-mouth route remain unchanged')
except Exception as exc:
    print(f'FAIL W54F cottage/Estate visual reconstruction: {exc}',file=sys.stderr); sys.exit(1)
