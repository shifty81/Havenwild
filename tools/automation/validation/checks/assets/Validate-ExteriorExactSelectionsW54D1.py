#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
SELECTIONS = ROOT / 'content/buildings/exterior_exact_region_selections_w54d1.json'
CONTRACT = ROOT / 'content/buildings/exterior_exact_region_review_contract_v1.json'
EXTERIOR = ROOT / 'content/buildings/exterior_grammar_contract_v1.json'
def need(v,msg):
    if not v: raise SystemExit('FAIL W54D1 exterior exact selection: '+msg)
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def main():
    for p in (SELECTIONS,CONTRACT,EXTERIOR): need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    s=load(SELECTIONS); c=load(CONTRACT); e=load(EXTERIOR)
    need(s.get('schema')=='havenwild.exterior_exact_region_selections.v1','schema drift')
    need(s.get('pass')=='167Z109W54D1','pass drift')
    need(s.get('sourceCommit')==c.get('sourceCommit'),'pinned source commit mismatch')
    rules=s.get('rules',{})
    for k in ('wrongFacingRotationForbidden','wrongFacingMirroringForbidden','wholeBuildingSheetsReferenceOnly','sideOrBackFacingInferenceForbidden','complexRoofAssemblyCellGuessingForbidden'):
        need(rules.get(k) is True,f'rule {k} must remain true')
    sels=s.get('selections',[]); need(len(sels)==6,'expected six selected Siding, Plain frontage strips')
    expected={
      'wall_siding_plain_cream_front_left':([0,0,32,96],['c0r0','c0r1','c0r2']),
      'wall_siding_plain_cream_front_repeat':([64,0,32,96],['c2r0','c2r1','c2r2']),
      'wall_siding_plain_cream_front_right':([128,0,32,96],['c4r0','c4r1','c4r2']),
      'wall_siding_plain_blue_front_left':([160,0,32,96],['c5r0','c5r1','c5r2']),
      'wall_siding_plain_blue_front_repeat':([224,0,32,96],['c7r0','c7r1','c7r2']),
      'wall_siding_plain_blue_front_right':([288,0,32,96],['c9r0','c9r1','c9r2'])}
    for x in sels:
        need(x.get('sourcePath','').endswith('Structure/Walls/Siding, Plain.png'),'unexpected selected source')
        need(x.get('semanticRole','').startswith('south_frontage_'),'selection must remain frontage-only')
        rect,cells=expected[x['selectionId']]; need(x.get('sourceRect')==rect,f"source rect drift: {x['selectionId']}"); need(x.get('cellIds')==cells,f"cell ids drift: {x['selectionId']}")
    need(e['rules']['wrongFacingWallReuseForbidden'] is True,'later exterior publication weakened fail-closed facing rule')
    need(e.get('estateStarterCottage',{}).get('deferredExactFacings')==['north','east','west'],'side/back facings were incorrectly inferred')
    unresolved=json.dumps(s.get('explicitlyUnresolved',[]))
    for role in ('wall_back_repeat','wall_side_west_repeat','wall_side_east_repeat','roof_hip','roof_valley'):
        need(role in unresolved,f'unresolved evidence role lost: {role}')
    print('PASS W54D1 exterior exact selection authority (historical evidence retained)')
    print('- the six human-reviewed siding rectangles remain immutable evidence; later passes may publish the selected south-frontage subset')
    return 0
if __name__=='__main__': raise SystemExit(main())
