#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
CAT=ROOT/'content/asset_packs/havenwild_objects/published_structure_exact_modules_v1.json'
PACK=ROOT/'content/asset_packs/havenwild_objects/pack.json'
ROOF=ROOT/'content/buildings/roof_exact_region_publication_v1.json'
SUPPORT=ROOT/'content/buildings/structure_support_exact_region_publication_v1.json'
ROOF_TOPO=ROOT/'content/buildings/roof_topology_contract_v1.json'
SUPPORT_TOPO=ROOT/'content/buildings/structure_support_topology_contract_v1.json'
INV=ROOT/'content/assets/lpc/structure_source_inventory_v1.json'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/structure_exact_modules_acceptance_scene_v1.json'
TEST=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
BUILDER=ROOT/'tools/automation/assets/Build-ExactStructureModuleAcceptanceSceneV1.py'

EXPECTED_IDS={
 'roof_flat_gray_field','roof_flat_gray_north_eave','roof_flat_gray_south_eave',
 'roof_flat_gray_west_edge','roof_flat_gray_east_edge',
 'roof_flat_gray_corner_nw','roof_flat_gray_corner_ne','roof_flat_gray_corner_sw','roof_flat_gray_corner_se',
 'roof_gable_shingle_gray_module','roof_gable_shingle_brown_module',
 'bridge_drawbridge_oak_leaf','bridge_wood_oak_flat_module','bridge_wood_oak_arch_module','bridge_wood_oak_vertical_module',
 'platform_dais_steps_light','pillar_stone_gray_narrow','pillar_floral_white',
}
DEFERRED_TOKENS={'roof.hipped_shingle_a','bridge.rope_a.no_rails','bridge.rope_a.rails','bridge.wood_a.rails','platform.cement_a'}

W54A_BROWN_ROOF_IDS={
 'roof_flat_brown_field','roof_flat_brown_north_eave','roof_flat_brown_south_eave',
 'roof_flat_brown_west_edge','roof_flat_brown_east_edge',
 'roof_flat_brown_corner_nw','roof_flat_brown_corner_ne','roof_flat_brown_corner_sw','roof_flat_brown_corner_se',
}

def need(v,msg):
    if not v: raise SystemExit('FAIL W45D2 exact structure publication: '+msg)
def load(p):
    need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    cat=load(CAT); pack=load(PACK); roof=load(ROOF); support=load(SUPPORT); inv=load(INV); scene=load(SCENE); test=load(TEST)
    need(BUILDER.is_file(),'acceptance-scene builder missing')
    need(cat.get('schema')=='havenwild.published_world_asset_catalog.v1','catalog schema drift')
    entries=cat.get('entries',[])
    ids={e.get('id') for e in entries}
    need(EXPECTED_IDS <= ids,f'historical W45D2 exact-module baseline missing: {sorted(EXPECTED_IDS-ids)}')
    need(ids <= EXPECTED_IDS | W54A_BROWN_ROOF_IDS,f'unreviewed exact-module extension leaked in: {sorted(ids-(EXPECTED_IDS|W54A_BROWN_ROOF_IDS))}')
    need(len(entries) in {18,27},'expected historical 18 candidates or W54A 27-candidate extension')
    need(all(e.get('certification')=='candidate' for e in entries),'exact modules were auto-certified')
    need(all(e.get('role') in {'structure_component','structural_connector'} for e in entries),'unexpected published role')
    need(all(e.get('provenance',{}).get('authority')=='lpc_revised_exact_structure_component' for e in entries),'non-exact provenance leaked')
    need(all(e.get('provenance',{}).get('source_rect') for e in entries),'source rectangle missing')
    need(all(e.get('provenance',{}).get('source_path','').startswith('assets/source/licensed/lpc_revised/Structure/') for e in entries),'non-pinned Structure source path leaked')
    # Visuals point directly at the immutable source sheets in W45D2.
    need(all(e.get('visual',{}).get('frames',[{}])[0].get('source_rect')==e.get('provenance',{}).get('source_rect') for e in entries),
         'runtime visual rectangle must equal exact external source rectangle')
    roof_entries=[e for e in entries if e['id'].startswith('roof_')]
    historical_roof_entries=[e for e in roof_entries if e['id'] in EXPECTED_IDS]
    need(len(historical_roof_entries)==11,'expected 11 historical W45 roof candidates')
    if W54A_BROWN_ROOF_IDS <= ids:
        need(len(roof_entries)==20,'W54A should extend roof candidates from 11 to 20')
    need(all(e.get('structure',{}).get('camera_local_occlusion') is True for e in roof_entries),'roof cutaway must remain camera-local')
    need(all(e.get('structure',{}).get('visibility_role')=='roof' for e in roof_entries),'roof visibility role drift')
    bridge_entries=[e for e in entries if e['id'].startswith('bridge_')]
    need(len(bridge_entries)==4,'expected four bridge module candidates')
    need(all(e.get('footprint',{}).get('blocks_movement') is False for e in bridge_entries),'bridge visual module is incorrectly blocking traversal')
    pillars=[e for e in entries if e['id'].startswith('pillar_')]
    need(len(pillars)==2 and all(e['footprint']['collision_size']==[1,1] for e in pillars),'pillar foot-tile collision drift')
    need(roof.get('schema')=='havenwild.roof_exact_region_publication.v1' and roof.get('pass')=='167Z109W45C3B','roof publication identity drift')
    need(support.get('schema')=='havenwild.structure_support_exact_region_publication.v1' and support.get('pass')=='167Z109W45D2','support publication identity drift')
    need(set(roof.get('acceptedAssetIds',[]))=={e['id'] for e in historical_roof_entries},'historical roof publication/catalog mismatch')
    historical_support=EXPECTED_IDS-{e['id'] for e in historical_roof_entries}
    need(set(support.get('acceptedAssetIds',[]))==historical_support,'historical support publication/catalog mismatch')

    expected_roof_hashes={
        'roof.flat_shingle_a':'9e0e44086d5ae9528473e58c5a66d2b2d943e40d7f0208a7832d937e913b7d98',
        'roof.gable_shingle_a':'d78e0a048e9b449e1f45ae5bfd31878d9979c879f53a4332a7f3713e9c089ca7',
    }
    expected_support_hashes={
        'bridge.drawbridge_a':'23c7805444acd46dfa6c1bf4f3c9e4b2a3241029eab4ac64c6075ec79351a5ad',
        'bridge.wood_a.no_rails':'f514822ea07fad29cdcf53c3e819f3c38fd49c20d9f74962cef806ed53425093',
        'platform.dais_steps_a':'27c0a3705906ced8cd3824799e36c9853f9a2ad4a7c9c123e0d67307c279d70c',
        'pillar.stone_a':'9fa1c4e00ca64ab47834b9ada4eee4dd21d675a90b257eb84bb8d0a1bc2c2b11',
        'pillar.floral_a':'8e5e37e4e298b04c965c7a9629cb43f926c7db87114abcb816c2ae9a1bece2d0',
    }
    need(roof.get('sourceEvidence')==expected_roof_hashes,'roof evidence source hashes drift')
    need(support.get('sourceEvidence')==expected_support_hashes,'support evidence source hashes drift')
    deferred={d.get('family') for d in roof.get('deferredFamilies',[])}|{d.get('family') for d in support.get('deferredFamilies',[])}
    need(DEFERRED_TOKENS <= deferred,'required ambiguous families are not explicitly deferred')
    # Ensure no deferred family was smuggled into exact source provenance.
    all_paths='\n'.join(e['provenance']['source_path'] for e in entries).lower()
    for token in ('hipped shingle','rope bridge a - rails.png','wood bridge a - rails.png','cement platform'):
        need(token not in all_paths,f'deferred source was silently published: {token}')
    need(inv.get('pass')=='167Z109W45D2','structure inventory not advanced to W45D2')
    need(inv.get('summary',{}).get('reviewedComponentSourceSheets')==18,'expected 18/98 exact-reviewed Structure source sheets')
    sources={s['id']:s for s in pack.get('sources',[])}
    for sid in ('published_structure_exact_modules_catalog','lpc_roof_flat_shingle_a','lpc_roof_gable_shingle_a',
                'lpc_bridge_drawbridge_a','lpc_bridge_wood_a_no_rails','lpc_platform_dais_steps_a','lpc_pillar_stone_a','lpc_pillar_floral_a'):
        need(sid in sources,f'pack source missing {sid}')
    need(sources['published_structure_exact_modules_catalog']['path']==CAT.relative_to(ROOT).as_posix(),'catalog sidecar source path drift')
    semantic={(a.get('semantic_id'),a.get('category')):a for a in pack.get('assets',[])}
    for e in entries:
        need(any(key[0]==e['source_semantic_id'] for key in semantic),f"source semantic binding missing {e['source_semantic_id']}")
    need(('world_asset.catalog.structure_exact_modules','editor_template') in semantic,'published exact-module catalog asset missing')
    need(scene.get('role')=='diagnostic_only' and scene.get('sceneId')=='structure_exact_modules_acceptance','acceptance scene identity drift')
    scene_ids={o.get('assetId') for o in scene.get('objects',[])}
    need(scene_ids==EXPECTED_IDS,'historical W45 acceptance scene baseline drifted')
    tw=test.get('testWorld',{})
    need(tw.get('structureExactModulesAcceptanceSceneId')=='structure_exact_modules_acceptance','test-world navigation id missing')
    need(tw.get('structureExactModulesAcceptanceScene')==SCENE.relative_to(ROOT).as_posix(),'test-world acceptance path missing')
    roof_topo=load(ROOF_TOPO); support_topo=load(SUPPORT_TOPO)
    need(roof_topo.get('buildingIntegration',{}).get('roofOcclusionIsCameraLocal') is True,'roof camera-local policy drift')
    need(support_topo.get('bridgePolicy',{}).get('collisionFollowsWalkableDeckNotVisualRails') is True,'bridge collision/rail separation drift')
    print('PASS W45C3B/W45D2 exact roof + structural-support module publication')
    print('- historical 18 exact PublishedWorldAsset candidates remain intact; W54A may add 9 palette-parallel brown flat-roof cells')
    print('- Structure exact-reviewed source progress: 18/98')
    print('- hipped/rope/railed/cement-platform ambiguous families remain explicitly deferred')
    return 0
if __name__=='__main__': raise SystemExit(main())
