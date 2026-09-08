#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[5]
CAT=ROOT/'content/asset_packs/havenwild_objects/published_structure_roof_trim_v1.json'
PACK=ROOT/'content/asset_packs/havenwild_objects/pack.json'
CACHE=ROOT/'assets/generated/havenwild_structure_roof_trim_w45c2.json'
PNG=ROOT/'assets/generated/havenwild_structure_roof_trim_w45c2.png'
CONTRACT=ROOT/'content/buildings/roof_topology_contract_v1.json'
INV=ROOT/'content/assets/lpc/structure_source_inventory_v1.json'
PUB_ROOF=ROOT/'content/buildings/roof_exact_region_publication_v1.json'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/structure_roof_trim_acceptance_scene_v1.json'
TEST=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
META=ROOT/'crates/haven_assets/src/published_world_asset_metadata.rs'
BUILDER=ROOT/'tools/automation/assets/Build-StructureRoofTrimCertificationV1.py'
SCENE_BUILDER=ROOT/'tools/automation/assets/Build-StructureRoofTrimAcceptanceSceneV1.py'

def need(v,msg):
    if not v: raise SystemExit('FAIL W45C2 roof/trim certification: '+msg)
def load(p): need(p.is_file(),f'missing {p.relative_to(ROOT)}'); return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    cat=load(CAT); pack=load(PACK); cache=load(CACHE); contract=load(CONTRACT); inv=load(INV); scene=load(SCENE); test=load(TEST)
    need(BUILDER.is_file() and SCENE_BUILDER.is_file(),'deterministic W45C2 builders missing')
    need(cat.get('schema')=='havenwild.published_world_asset_catalog.v1','catalog schema drift')
    entries=cat.get('entries',[]); need(len(entries)==1,'W45C2 must publish exactly one reviewed wall-border component in this pass')
    e=entries[0]; need(e['id']=='wall_border_formal_crown_repeat','formal crown identity drift'); need(e.get('certification')=='candidate','wall border auto-certified without native visual acceptance')
    need(e.get('provenance',{}).get('source_rect')==[0,64,32,32],'exact Formal Crown source rect drift')
    st=e.get('structure',{}); need(st.get('topology_role')=='repeat_segment' and st.get('repeat_axis')=='x','repeat topology metadata drift')
    need(st.get('camera_local_occlusion') is True and st.get('occlusion_group')=='building.wall_finish','wall-border cutaway grouping drift')
    need(PNG.is_file() and Image.open(PNG).size==(64,64),'W45C2 cache missing/dimension drift')
    need(cache.get('schema')=='havenwild.structure_roof_trim_runtime_cache.v1','cache schema drift'); need(cache['entries']['wall_border_formal_crown_repeat']['sourceRect']==[0,64,32,32],'cache source rect drift')
    need(contract.get('schema')=='havenwild.roof_topology_contract.v1','roof topology contract schema drift')
    need(contract.get('defaultPolicy')=='topology_assembly_not_monolithic_sprite','roof reverted to monolithic sprite policy')
    bi=contract.get('buildingIntegration',{}); need(bi.get('belongsToBuildingInstance') is True and bi.get('roofOcclusionIsCameraLocal') is True and bi.get('roofOcclusionNeverMutatesWorldState') is True,'roof/building cutaway contract drift')
    roles=set(contract.get('requiredTopologyRoles',[]))
    for role in ('field','north_eave','south_eave','ridge_horizontal','gable_west','gable_east','hip_nw','valley_nw','trim_repeat'): need(role in roles,f'missing roof topology role {role}')
    need(len(contract.get('roofFamilies',[]))==7,'expected seven pinned roof source families')
    forbidden=' '.join(contract.get('forbiddenPatterns',[])).lower(); need('whole source sheet as one roof placeable' in forbidden and 'automatic promotion of any non-empty 32x32 cell' in forbidden,'roof anti-guess policy missing')
    reviewed={x['sourcePath'] for x in inv.get('entries',[]) if x.get('certification',{}).get('componentRectsReviewed')}
    need(any(p.endswith('Wall Borders/Formal Crown Molding.png') for p in reviewed),'Formal Crown review state not preserved in structure inventory')
    roof=[x for x in inv.get('entries',[]) if x.get('role')=='roof']; need(len(roof)==7,'roof source family count drift')
    reviewed_roof={x.get('sourcePath') for x in roof if x.get('certification',{}).get('componentRectsReviewed')}
    if PUB_ROOF.is_file():
        pub=load(PUB_ROOF); accepted=set(pub.get('acceptedFamilies',[]))
        family_to_path={f.get('id'):f.get('source') for f in contract.get('roofFamilies',[])}
        expected={family_to_path[f] for f in accepted}
        need(reviewed_roof==expected,'roof exact-reviewed progression no longer matches W45C3B publication')
    else:
        need(not reviewed_roof,'roof sheet falsely marked exact-reviewed before topology regions are accepted')
    need(scene.get('role')=='diagnostic_only' and scene.get('sceneId')=='structure_roof_trim_acceptance','acceptance scene identity drift'); need(len(scene.get('objects',[]))==5,'acceptance scene must expose five seam repeats')
    rel=SCENE.relative_to(ROOT).as_posix(); need(rel in test.get('sceneFiles',[]) and rel in test.get('smokeTests',[]),'test pack missing W45C2 acceptance scene')
    sources={s['id']:s for s in pack.get('sources',[])}; need(sources.get('runtime_structure_roof_trim_w45c2',{}).get('path')==PNG.relative_to(ROOT).as_posix(),'runtime roof/trim source missing'); need(sources.get('published_structure_roof_trim_catalog',{}).get('path')==CAT.relative_to(ROOT).as_posix(),'published roof/trim catalog source missing')
    sem={(a['semantic_id'],a['category']) for a in pack.get('assets',[])}; need(('structure.wall_border.runtime','wall') in sem,'runtime wall-border binding missing'); need(('world_asset.catalog.structure_roof_trim','editor_template') in sem,'published roof/trim catalog binding missing')
    meta=META.read_text(encoding='utf-8'); need('repeat_axis' in meta and 'assembly_family' in meta,'PublishedStructureDefinition lacks repeat/assembly metadata')
    print('PASS W45C2 roof topology contract + exact wall-border authority')
    print('- one exact Formal Crown Molding repeat cell is published as CANDIDATE')
    print('- W45C2 anti-guess roof grammar remains authoritative; later W45C3B exact regions may advance selected roof families')
    print('- roof occlusion remains camera-local inside the same multi-level BuildingInstance')
    return 0
if __name__=='__main__': raise SystemExit(main())
