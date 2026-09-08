#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
INVENTORY=ROOT/'content/assets/lpc/structure_source_inventory_v1.json'
CONTRACT=ROOT/'content/assets/lpc/structure_component_certification_contract_v1.json'
QUEUE=ROOT/'content/assets/lpc/structure_component_promotion_queue_v1.json'
CATALOG=ROOT/'content/assets/lpc/lpc_slice_catalog_v0_1.json'
REGISTRY=ROOT/'crates/haven_assets/src/placeable_asset_registry.rs'
LEGACY=ROOT/'crates/haven_assets/src/asset_registry.rs'
BUILDER=ROOT/'tools/automation/assets/Build-StructureSourceInventoryV1.py'
EXPECTED={
 'bridge':5,'building_reference':3,'door':13,'fence':3,'floor':16,'misc':5,
 'pillar':2,'platform':2,'roof':7,'sign':2,'stairs':6,'wall':20,'wall_border':7,'window':7,
}

def need(v,msg):
    if not v: raise SystemExit(f'FAIL W45A structure source inventory: {msg}')
def load(p):
    need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    inv=load(INVENTORY); contract=load(CONTRACT); queue=load(QUEUE); catalog=load(CATALOG)
    need(BUILDER.is_file(),'builder missing')
    need(inv.get('schema')=='havenwild.structure_source_inventory.v1','inventory schema drift')
    need(contract.get('schema')=='havenwild.structure_component_certification_contract.v1','contract schema drift')
    need(contract.get('authority')=='PublishedWorldAssetRegistry','structural promotion created a second registry')
    policy=inv.get('policy',{})
    need(policy.get('sourceSheetsAreNotPublishedComponents') is True,'source sheets are being treated as published components')
    need(policy.get('publishedComponentsUsePublishedWorldAssetRegistry') is True,'published structure authority not locked to PublishedWorldAssetRegistry')
    need(policy.get('requireExactSourceRectBeforePromotion') is True,'exact source rectangle is not required')

    entries=inv.get('entries',[])
    need(len(entries)==98,f'expected 98 pinned LPC Structure sheets, found {len(entries)}')
    paths=[e.get('sourcePath') for e in entries]
    need(len(set(paths))==98,'duplicate Structure source paths in inventory')
    need(all(str(p).startswith('assets/source/licensed/lpc_revised/Structure/') for p in paths),'non-Structure source leaked into inventory')
    counts=Counter(e.get('role') for e in entries)
    need(dict(sorted(counts.items()))==dict(sorted(EXPECTED.items())),f'role counts drifted: {dict(counts)}')
    need(inv.get('summary',{}).get('unclassified')==0,'unclassified Structure source families remain')
    allowed_status={'SOURCE_CANDIDATE','COMPONENT_CANDIDATE'}
    need(all(e.get('status') in allowed_status for e in entries),'unexpected structure source certification state')
    reviewed={e.get('sourcePath') for e in entries if e.get('certification',{}).get('componentRectsReviewed') is True}
    expected_w45b={
        'assets/source/licensed/lpc_revised/Structure/Doors/32x48px Doors/12 Panel Door A.png',
        'assets/source/licensed/lpc_revised/Structure/Stairs/Short Steps A.png',
        'assets/source/licensed/lpc_revised/Structure/Fences/Plain Fence A.png',
        'assets/source/licensed/lpc_revised/Structure/Signs/Sign Backgrounds A.png',
        'assets/source/licensed/lpc_revised/Structure/Signs/Sign Icons A.png',
    }
    expected_w45c=expected_w45b | {
        'assets/source/licensed/lpc_revised/Structure/Floor/Wood Floor B.png',
        'assets/source/licensed/lpc_revised/Structure/Walls/Drywall.png',
        'assets/source/licensed/lpc_revised/Structure/Walls/CutawayOverlay.png',
        'assets/source/licensed/lpc_revised/Structure/Walls/Panels A.png',
        'assets/source/licensed/lpc_revised/Structure/Windows/Ornamental Windows B.png',
    }
    pass_id=inv.get('pass')
    if pass_id=='167Z109W45A':
        need(not reviewed,'W45A baseline unexpectedly contains reviewed component rectangles')
    elif pass_id=='167Z109W45B':
        need(reviewed==expected_w45b,f'W45B reviewed source-sheet set drifted: {sorted(reviewed)}')
    elif pass_id=='167Z109W45C':
        need(reviewed==expected_w45c,f'W45C reviewed source-sheet set drifted: {sorted(reviewed)}')
    else:
        expected_w45c2=expected_w45c | {
            'assets/source/licensed/lpc_revised/Structure/Wall Borders/Formal Crown Molding.png',
        }
        if pass_id == '167Z109W45D2':
            expected_w45d2 = expected_w45c2 | {
                'assets/source/licensed/lpc_revised/Structure/Roofing/Flat Shingle Roof A.png',
                'assets/source/licensed/lpc_revised/Structure/Roofing/Gable Shingle Roof A.png',
                'assets/source/licensed/lpc_revised/Structure/Bridges/Drawbridge A.png',
                'assets/source/licensed/lpc_revised/Structure/Bridges/Wood Bridge A - No Rails.png',
                'assets/source/licensed/lpc_revised/Structure/Platforms/Dias with Steps A.png',
                'assets/source/licensed/lpc_revised/Structure/Pillars/Stone Pillar A.png',
                'assets/source/licensed/lpc_revised/Structure/Pillars/Floral Pillar A.png',
            }
            need(reviewed==expected_w45d2,f'{pass_id} reviewed source-sheet set drifted: {sorted(reviewed)}')
        else:
            need(pass_id in {'167Z109W45C2','167Z109W45C3A','167Z109W45D1'},f'unrecognized structure inventory progression pass {pass_id}')
            need(reviewed==expected_w45c2,f'{pass_id} reviewed source-sheet set drifted: {sorted(reviewed)}')
    need(all(e.get('status')=='COMPONENT_CANDIDATE' for e in entries if e.get('sourcePath') in reviewed),'reviewed sheets are not marked COMPONENT_CANDIDATE')

    source_catalog={s.get('source') for s in catalog.get('sheets',[]) if '/Structure/' in str(s.get('source',''))}
    need(set(paths)==source_catalog,'inventory no longer exactly matches pinned LPC Structure slice catalog')
    queue_entries=queue.get('entries',[])
    need(queue.get('schema')=='havenwild.structure_component_promotion_queue.v1','promotion queue schema drift')
    need(len(queue_entries)==98,'promotion queue does not cover all 98 Structure source sheets')
    need({e.get('sourcePath') for e in queue_entries}==set(paths),'promotion queue/source inventory mismatch')
    need(queue.get('currentBlockersFirst')==['door','stairs','fence','sign'],'W43 blocker-first structural priority drifted')
    need(all(e.get('promotionTarget')=='reference_only_decompose_into_building_recipe' for e in queue_entries if e.get('role')=='building_reference'),'building reference sheets are being promoted as raw structure components')
    if inv.get('pass')!='167Z109W45A':
        reviewed_queue={e.get('sourcePath') for e in queue_entries if e.get('nextAction')=='inspect_structure_acceptance_scene'}
        need(reviewed_queue==reviewed,'structure promotion queue/reviewed sheet mismatch')

    roles=set(contract.get('roles',[]))
    for required in ('floor','wall','door','window','roof','fence','bridge','stairs','structural_connector'):
        need(required in roles,f'certification contract missing role {required}')
    forbidden='\n'.join(contract.get('forbiddenShortcuts',[])).lower()
    for token in ('ladder art used as stairs','standing screen used as sign','whole source sheet'):
        need(token in forbidden,f'forbidden shortcut not locked: {token}')
    registry=REGISTRY.read_text(encoding='utf-8-sig')
    need('StructureComponent' in registry and 'StructuralConnector' in registry,'PublishedWorldAsset roles do not support structures/connectors')
    legacy=LEGACY.read_text(encoding='utf-8-sig')
    # W43B deliberately fails these legacy structure cells closed. W45 must not
    # restore unrelated visuals while source/component certification proceeds.
    for marker in ('ObjectKind::Stairs','ObjectKind::Fence','ObjectKind::Door'):
        need(marker in legacy,f'legacy disposition marker missing: {marker}')
    print('PASS W45A LPC structural source inventory + certification contract')
    print('- 98/98 pinned LPC Structure sheets inventoried')
    print('- 14 structural source roles classified with zero unclassified sheets')
    print(f'- exact component rectangles reviewed for {len(reviewed)}/98 source sheets; remaining sheets stay SOURCE_CANDIDATE')
    print('- future structural components remain on PublishedWorldAssetRegistry authority')
    return 0
if __name__=='__main__': raise SystemExit(main())
