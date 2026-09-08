#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def req(ok,msg):
    if not ok: raise AssertionError(msg)
try:
    contract=load('content/buildings/exterior_grammar_contract_v1.json')
    recipe=load('content/buildings/recipes/estate_starter_cottage_v1.json')
    inst=load('content/buildings/instances/estate_starter_cottage_v1.json')
    icat=load('content/buildings/building_instance_catalog_v1.json')
    req(recipe.get('id')=='havenwild.estate.starter_cottage','Estate cottage recipe identity drifted')
    req(recipe.get('classification',{}).get('diagnosticOnly') is False,'Estate cottage became diagnostic-only')
    req(next(e['status'] for e in icat['entries'] if e['id']==inst['id'])=='candidate','Estate cottage instance is not an active candidate')
    level=recipe['levels'][0]
    door=next(o for o in level['openings'] if o['id']=='front_door')
    world_door=[inst['anchorTile'][0]+door['tile'][0], inst['anchorTile'][1]+door['tile'][1]]
    req(world_door in ([59,34],[59,36]),'Estate cottage front doorway no longer aligns with the authored home route lineage')
    walls=level['wallRuns']
    for side in ('north','east','west'):
        candidates=[w for w in walls if w['id']==side]
        req(candidates and candidates[0]['visualAssetId'] is None and candidates[0]['visualStatus']=='deferred_exact_facing' and candidates[0]['blocksMovement'] is True,f'{side} exterior wall must remain logical/fail-closed')
    req(any(w['edge']=='south' and w.get('visualAssetId') for w in walls),'south frontage lost exact visual authority')
    roof=recipe['roof']
    req(roof.get('mode') in ('flat_nine_slice','authored_module'),'Estate cottage roof is not using a supported exact publication mode')
    mods=roof.get('authoredModules',[])
    req(not (len(mods)==1 and mods[0].get('assetId')=='roof_gable_shingle_brown_module'),'rejected single-gable shortcut returned to the Estate cottage')
    req(contract['rules']['wrongFacingWallReuseForbidden'] is True and contract['rules']['missingFacingVisualFailsClosedButRetainsCollision'] is True,'fail-closed exterior-facing policy missing')
    print('PASS W54A building exterior grammar (forward-compatible)')
    print('- Estate cottage retains exact south frontage, route-aligned door and fail-closed unsupported side/back facings')
    print('- later exact roof publications are allowed; W54F may use two edge-adjacent exact gable modules without reviving the rejected single-gable shortcut')
except Exception as exc:
    print(f'FAIL W54A building exterior grammar: {exc}',file=sys.stderr); sys.exit(1)
