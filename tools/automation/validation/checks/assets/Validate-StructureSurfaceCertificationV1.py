#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[5]
CAT=ROOT/'content/asset_packs/havenwild_objects/published_structure_surfaces_v1.json'
PACK=ROOT/'content/asset_packs/havenwild_objects/pack.json'
CACHE=ROOT/'assets/generated/havenwild_structure_surfaces_w45c.json'
CACHE_PNG=ROOT/'assets/generated/havenwild_structure_surfaces_w45c.png'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/structure_surface_acceptance_scene_v1.json'
TEST=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
CONTRACT=ROOT/'content/buildings/building_level_visibility_contract_v1.json'
INV=ROOT/'content/assets/lpc/structure_source_inventory_v1.json'
PUB_ROOF=ROOT/'content/buildings/roof_exact_region_publication_v1.json'
META=ROOT/'crates/haven_assets/src/published_world_asset_metadata.rs'
BUILDER=ROOT/'tools/automation/assets/Build-StructureSurfaceCertificationV1.py'
SCENE_BUILDER=ROOT/'tools/automation/assets/Build-StructureSurfaceAcceptanceSceneV1.py'
ROOF_REVIEW_BUILDER=ROOT/'tools/automation/assets/Build-StructureRoofTrimReviewV1.py'

def need(v,msg):
    if not v: raise SystemExit('FAIL W45C structure surface certification: '+msg)
def load(p): need(p.is_file(),f'missing {p.relative_to(ROOT)}'); return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    cat=load(CAT); pack=load(PACK); cache=load(CACHE); scene=load(SCENE); test=load(TEST); contract=load(CONTRACT); inv=load(INV)
    need(BUILDER.is_file() and SCENE_BUILDER.is_file() and ROOF_REVIEW_BUILDER.is_file(),'deterministic W45C builder/review tool missing')
    need(cat.get('schema')=='havenwild.published_world_asset_catalog.v1','catalog schema drift')
    entries=cat.get('entries',[]); need(len(entries)==10,f'expected 10 W45C surface records, got {len(entries)}')
    ids={e['id'] for e in entries}
    expected={'floor_wood_herringbone_light','floor_wood_herringbone_dark','wall_drywall_simple','wall_panel_ornate_gold','wall_panel_ornate_blue','wall_cutaway_cap_left','wall_cutaway_cap_center','wall_cutaway_cap_right','wall_cutaway_cap_south','window_ornamental_tall'}
    need(ids==expected,f'W45C surface record set drifted: {sorted(ids)}')
    need(all(e.get('role')=='structure_component' for e in entries),'non-structure role leaked into surface catalog')
    need(all(e.get('certification')=='candidate' for e in entries),'W45C candidates were auto-certified without visual acceptance')
    need(all(e.get('provenance',{}).get('source_rect') for e in entries),'exact immutable source rectangle missing')
    cut=[e for e in entries if e['id'].startswith('wall_cutaway_cap_')]
    need(len(cut)==4,'cutaway topology set must contain four exact cells')
    need(all(e.get('structure',{}).get('visibility_role')=='cutaway_overlay' for e in cut),'cutaway visibility role drift')
    need(all(e.get('structure',{}).get('camera_local_occlusion') is True for e in cut),'cutaway must remain camera-local presentation')
    wall=next(e for e in entries if e['id']=='wall_drywall_simple')
    need(wall['footprint']['visual_offset']==[0,-2] and wall['footprint']['visual_size']==[1,3],'wall base-anchor/visual height drift')
    win=next(e for e in entries if e['id']=='window_ornamental_tall')
    need(win.get('states')==['unlit','day','lit'],'window state vocabulary drift')
    need([f['source_rect'] for f in win['visual']['frames']]==[[0,128,32,64],[32,128,32,64],[64,128,32,64]],'window runtime state rect drift')
    sources={s['id']:s for s in pack.get('sources',[])}
    need(sources.get('runtime_structure_surfaces_w45c',{}).get('path')=='assets/generated/havenwild_structure_surfaces_w45c.png','runtime surface source missing')
    need(sources.get('published_structure_surface_catalog',{}).get('path')==CAT.relative_to(ROOT).as_posix(),'surface catalog source missing')
    sem={(a['semantic_id'],a['category']) for a in pack.get('assets',[])}
    for pair in [('structure.floor.runtime','floor'),('structure.wall_surface.runtime','wall'),('structure.cutaway.runtime','wall'),('structure.window.runtime','wall'),('world_asset.catalog.structure_surfaces','editor_template')]: need(pair in sem,f'pack semantic binding missing {pair}')
    need(CACHE_PNG.is_file() and Image.open(CACHE_PNG).size==(256,256),'W45C runtime atlas missing/dimension drift')
    need(cache.get('schema')=='havenwild.structure_surface_runtime_cache.v1','cache metadata schema drift')
    need(len(cache.get('entries',{}))==12,'expected 12 cache frame/component records')
    for name,row in cache.get('entries',{}).items():
        x,y,w,h=row['cacheRect']; need(x>=0 and y>=0 and x+w<=256 and y+h<=256,f'cache rect out of bounds: {name}')
    need(scene.get('role')=='diagnostic_only' and scene.get('sceneId')=='structure_surface_acceptance','acceptance scene identity drift')
    need(len(scene.get('objects',[]))==10,'acceptance scene must expose all 10 W45C published candidates')
    rel=SCENE.relative_to(ROOT).as_posix(); need(rel in test.get('sceneFiles',[]) and rel in test.get('smokeTests',[]),'test pack does not expose W45C acceptance scene')
    need(test.get('testWorld',{}).get('structureSurfaceAcceptanceSceneId')=='structure_surface_acceptance','test-world navigation identity missing')
    need(contract.get('schema')=='havenwild.building_level_visibility_contract.v1','building level/cutaway contract schema drift')
    need(contract.get('defaultInteriorPolicy')=='same_world_building_instance','ordinary interiors reverted to separate-scene default')
    lvl=contract.get('levelModel',{}); need(lvl.get('groundLevel')==0 and lvl.get('stairsAndLaddersUseStructuralConnectors') is True,'multi-level building contract drift')
    cam=contract.get('cameraPresentation',{}); need(cam.get('visibilityIsPerClientCamera') is True and cam.get('visibilityNeverMutatesWorldState') is True,'roof/wall occlusion became shared simulation state')
    forbidden=' '.join(contract.get('forbiddenPatterns',[])).lower(); need('one scene per ordinary upstairs' in forbidden and 'one scene per ordinary cellar' in forbidden,'upstairs/basement same-building rule missing')
    reviewed={e['sourcePath'] for e in inv.get('entries',[]) if e.get('certification',{}).get('componentRectsReviewed')}
    for suffix in ('Floor/Wood Floor B.png','Walls/Drywall.png','Walls/CutawayOverlay.png','Walls/Panels A.png','Windows/Ornamental Windows B.png'):
        need(any(p.endswith(suffix) for p in reviewed),f'W45C reviewed source not preserved in source inventory: {suffix}')
    roof=[e for e in inv.get('entries',[]) if e.get('role')=='roof']; need(len(roof)==7,'roof source family count drift')
    reviewed_roof={e.get('sourcePath') for e in roof if e.get('certification',{}).get('componentRectsReviewed')}
    if PUB_ROOF.is_file():
        pub=load(PUB_ROOF)
        accepted=set(pub.get('acceptedFamilies',[]))
        family_to_path={f.get('id'):f.get('source') for f in load(ROOT/'content/buildings/roof_topology_contract_v1.json').get('roofFamilies',[])}
        expected={family_to_path[f] for f in accepted}
        need(reviewed_roof==expected,'roof review progression no longer matches W45C3B publication')
    else:
        need(not reviewed_roof,'roof source was marked reviewed before exact roof grammar acceptance')
    meta=META.read_text(encoding='utf-8')
    for token in ('visibility_role','occlusion_group','camera_local_occlusion'): need(token in meta,f'PublishedStructureDefinition missing {token}')
    print('PASS W45C exact floor/wall/cutaway/window surface authority + multi-level building visibility contract')
    print('- 10 PublishedWorldAsset structure surface candidates use exact pinned LPC source regions')
    print('- Sims-style roof/wall cutaway is camera-local presentation; ordinary upstairs/basements stay in one BuildingInstance')
    print(f"- {inv.get('summary',{}).get('reviewedComponentSourceSheets')}/98 LPC Structure sheets now have reviewed exact component regions")
    print('- W45C surface authority remains valid while later roof publication advances reviewed roof families')
    return 0
if __name__=='__main__': raise SystemExit(main())
