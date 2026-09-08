#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
CONTRACT=ROOT/'content/buildings/tavern_production_contract_v1.json'
RECIPE=ROOT/'content/buildings/recipes/tavern_standard_three_level_v1.json'
INSTANCE=ROOT/'content/buildings/instances/tavern_runtime_acceptance_v1.json'
RCAT=ROOT/'content/buildings/building_recipe_catalog_v1.json'
ICAT=ROOT/'content/buildings/building_instance_catalog_v1.json'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/tavern_building_acceptance_scene_v1.json'
PACK=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
BUILDER=ROOT/'tools/automation/assets/Build-TavernBuildingAcceptanceSceneV1.py'

def need(v,msg):
    if not v: raise SystemExit('FAIL W48 Production tavern authority: '+msg)
def world_pass_at_least(value, minimum):
    import re
    match=re.search(r'W(\d+)', str(value or ''))
    return bool(match and int(match.group(1)) >= minimum)

def load(p):
    need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8-sig'))
def published():
    out={}
    for p in sorted((ROOT/'content/asset_packs/havenwild_objects').glob('published*.json')):
        d=load(p)
        for e in d.get('entries',[]):
            out[e['id']]=e
            for a in e.get('aliases',[]): out[a]=e
    return out

def main():
    c=load(CONTRACT); r=load(RECIPE); inst=load(INSTANCE); rcat=load(RCAT); icat=load(ICAT); s=load(SCENE); pack=load(PACK); pub=published()
    need(BUILDER.is_file(),'acceptance builder missing')
    need(c.get('schema')=='havenwild.tavern_production_contract.v1' and c.get('pass') in {'167Z109W48','167Z109W52'},'contract schema/pass drift')
    need(c.get('recipeId')==r.get('id')=='havenwild.tavern.standard_three_level','tavern recipe identity drift')
    need(c.get('acceptanceInstanceId')==inst.get('id')=='havenwild.acceptance.standard_tavern','tavern instance identity drift')
    need(c.get('acceptanceSceneId')==inst.get('sceneId')=='tavern_building_acceptance','tavern scene identity drift')
    req=c.get('requirements',{})
    for k in ['sameWorldBuildingInstance','cameraLocalRoofAndWallCutaway','stairsConnectMinusOneZeroPlusOne','persistentDoorState','persistentFurnishingState','publishedFurnitureOnly']:
        need(req.get(k) is True,f'tavern requirement {k} regressed')
    need(req.get('separateInteriorScene') is False,'tavern incorrectly uses separate interior scene')
    need([x['level'] for x in r.get('levels',[])]==[-1,0,1],'tavern must contain cellar/ground/guest levels')
    need(r.get('classification',{}).get('diagnosticOnly') is False,'tavern recipe is still diagnostic-only')
    p=r.get('persistence',{})
    need(p.get('interiorPolicy')=='same_world_building_instance' and p.get('separateScene') is False,'tavern persistence policy drift')
    need({(x['fromLevel'],x['toLevel']) for x in r.get('connectors',[])}=={(-1,0),(0,1)},'tavern stair connectivity drift')
    need(r.get('roof',{}).get('mode')=='flat_nine_slice','tavern roof resolver drift')

    fs=[f for level in r['levels'] for f in level.get('furnishings',[])]
    backed=[f for f in fs if f.get('assetId')]; deferred=[f for f in fs if not f.get('assetId')]
    need(len(fs)==23 and len(backed)==23 and len(deferred)==0,'W52 Tavern visual-closure counts drift')
    need(c.get('knownDeferredVisuals',[])==[],'W52 Tavern must not retain deferred furnishing visuals')
    for f in backed:
        e=pub.get(f['assetId']); need(e is not None,f'unknown PublishedWorldAsset {f["assetId"]}')
        need(e.get('certification') not in {'rejected','missing','placeholder'},f'unusable tavern asset {f["assetId"]}')
        if f.get('state'): need(f['state'] in e.get('states',[]),f'unsupported state {f["state"]} on {f["id"]}')
    for f in deferred:
        need(f.get('visualStatus')=='deferred_exact_source',f'{f["id"]} does not fail closed')
        need(f.get('blocksNavigation') is True,f'{f["id"]} must preserve logical collision while visual is deferred')
        need(f.get('interactionSockets'),f'{f["id"]} lost logical interaction socket')

    rentries={x.get('id'):x for x in rcat.get('entries',[])}; ientries={x.get('id'):x for x in icat.get('entries',[])}
    need(world_pass_at_least(rcat.get('pass'),48) and r['id'] in rentries,'recipe catalog not advanced to W48')
    need(world_pass_at_least(icat.get('pass'),48) and inst['id'] in ientries,'instance catalog not advanced to W48')
    need(inst.get('placementSpace')=='scene_local' and inst.get('origin')=='diagnostic','acceptance instance placement drift')

    need(s.get('sceneId')=='tavern_building_acceptance' and s.get('objects')==[],'tavern acceptance must runtime-materialize with zero baked objects')
    a=s.get('acceptance',{})
    need(a.get('pass') in {'167Z109W48','167Z109W52'} and a.get('runtimeMaterialized') is True,'tavern acceptance metadata drift')
    need(a.get('structuralLevels')==[-1,0,1],'tavern acceptance does not exercise all levels')
    need(a.get('furnishingPlacementCount')==23 and a.get('publishedVisualFurnishingCount')==23 and a.get('deferredExactSourceCount')==0,'tavern acceptance furnishing counts drift')
    rel=SCENE.relative_to(ROOT).as_posix()
    need(rel in pack.get('sceneFiles',[]) and rel in pack.get('smokeTests',[]),'tavern acceptance not registered in dev world pack')
    tw=pack.get('testWorld',{})
    need(tw.get('productionTavernAcceptanceSceneId')=='tavern_building_acceptance' and tw.get('productionTavernAcceptanceScene')==rel,'tavern test-world navigation missing')

    print('PASS W48 Production tavern BuildingInstance authority')
    print('- production-shaped three-level tavern uses one same-world BuildingInstance')
    print('- W52 visual closure: 23/23 Tavern furnishings resolve to published exact-source candidates')
    print('- cellar, taproom/kitchen/service and guest floor remain connected by same-scene stairs')
    print('- tavern_building_acceptance contains zero baked structure/furniture carriers')
    return 0
if __name__=='__main__': raise SystemExit(main())
