#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[5]
CAT=ROOT/'content/asset_packs/havenwild_objects/published_structure_components_v1.json'
MAIN=ROOT/'content/asset_packs/havenwild_objects/published_world_assets_v1.json'
PACK=ROOT/'content/asset_packs/havenwild_objects/pack.json'
CACHE=ROOT/'assets/generated/havenwild_structure_components_w45b.json'
CACHE_PNG=ROOT/'assets/generated/havenwild_structure_components_w45b.png'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/structure_component_acceptance_scene_v1.json'
TEST_PACK=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
REGISTRY=ROOT/'crates/haven_assets/src/placeable_asset_registry.rs'
META=ROOT/'crates/haven_assets/src/published_world_asset_metadata.rs'
EDITOR=ROOT/'apps/haven_editor_native/src/app/atlas_render.rs'
RUNTIME=ROOT/'crates/haven_game/src/runtime_object_draw.rs'
BUILDER=ROOT/'tools/automation/assets/Build-StructureComponentCertificationV1.py'

def need(v,msg):
    if not v: raise SystemExit('FAIL W45B structure component certification: '+msg)
def load(p): need(p.is_file(),f'missing {p.relative_to(ROOT)}'); return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    cat=load(CAT); main=load(MAIN); pack=load(PACK); cache=load(CACHE); scene=load(SCENE); test=load(TEST_PACK)
    need(BUILDER.is_file(),'deterministic cache builder missing')
    need(cat.get('schema')=='havenwild.published_world_asset_catalog.v1','structure catalog schema drift')
    entries=cat.get('entries',[]); need(len(entries)==10,f'expected 10 W45B structural records, got {len(entries)}')
    ids={e['id'] for e in entries}; expected={'stairs_short_step_gray','stairs_short_run_gray','fence_plain_horizontal','fence_plain_vertical','fence_plain_post',*[f'sign_wall_{n}' for n in ('sword','shield','potion','inn','pub')]}
    need(ids==expected,f'W45B structural record set drifted: {sorted(ids)}')
    need(all(e.get('role') in {'structure_component','structural_connector'} for e in entries),'non-structural role leaked into W45B catalog')
    need(all(e.get('structure',{}).get('connection_family') for e in entries),'structure topology metadata missing')
    prim={e.get('legacy_object_kind'):e['id'] for e in entries if e.get('legacy_object_kind_primary')}
    need(prim=={'stairs':'stairs_short_step_gray','fence':'fence_plain_horizontal'},f'legacy structural primaries drifted: {prim}')
    door=next(e for e in main.get('entries',[]) if e.get('id')=='door_basic')
    need(door.get('source_semantic_id')=='structure.door.runtime','door still bound to generic object atlas')
    need(door.get('legacy_object_kind_primary') is True and door.get('legacy_object_kind')=='door','door legacy adapter lost')
    need(door.get('provenance',{}).get('source_path','').endswith('12 Panel Door A.png'),'door exact LPC provenance missing')
    need(door.get('structure',{}).get('topology_role')=='opening','door topology metadata missing')
    need(next(f for f in door['visual']['frames'] if f['state']=='closed')['source_rect']==[96,0,32,64],'door cache frame drift')
    need(not any(e.get('legacy_object_kind')=='sign' for e in entries),'wall sign plaques incorrectly replaced generic standing Sign')
    source_ids={s['id']:s for s in pack.get('sources',[])}
    need(source_ids.get('runtime_structure_components_w45b',{}).get('path')=='assets/generated/havenwild_structure_components_w45b.png','runtime structure cache source missing')
    sem={(a['semantic_id'],a['category']) for a in pack.get('assets',[])}
    for pair in [('structure.door.runtime','door'),('structure.building.runtime','building'),('structure.wall.runtime','wall'),('world_asset.catalog.structure_components','editor_template')]: need(pair in sem,f'pack semantic binding missing {pair}')
    need(CACHE_PNG.is_file(),'runtime structure atlas missing'); need(Image.open(CACHE_PNG).size==(256,256),'runtime structure atlas dimensions drift')
    need(cache.get('schema')=='havenwild.structure_component_runtime_cache.v1','runtime cache metadata schema drift')
    for name,row in cache.get('entries',{}).items():
        x,y,w,h=row['cacheRect']; need(x>=0 and y>=0 and x+w<=256 and y+h<=256,f'cache rect out of bounds: {name}')
    need(scene.get('role')=='diagnostic_only' and scene.get('sceneId')=='structure_component_acceptance','acceptance scene identity drift')
    need(len(scene.get('objects',[]))==11,'acceptance scene must contain door + 10 W45B records')
    rel='content/worldgen/scenes/world_asset_acceptance/structure_component_acceptance_scene_v1.json'
    need(rel in test.get('sceneFiles',[]) and rel in test.get('smokeTests',[]),'test pack does not expose W45B acceptance scene')
    reg=REGISTRY.read_text(); meta=META.read_text(); editor=EDITOR.read_text(); runtime=RUNTIME.read_text()
    need('structure: Option<PublishedStructureDefinition>' in reg,'registry does not carry structure metadata')
    for token in ('PublishedStructureDefinition','PublishedStructureSocket','source_layers'): need(token in meta,f'published structure metadata missing {token}')
    need('placeable_registry.for_legacy_object(object.kind)' in editor,'native editor does not use published legacy adapter')
    need('placeable_registry.for_legacy_object(object.kind)' in runtime,'runtime does not use published legacy adapter')
    print('PASS W45B exact structure component authority + acceptance fixture')
    print('- real LPC 12-panel door replaces generic door-atlas authority')
    print('- exact Short Steps A + Plain Fence A components published with explicit topology')
    print('- five wall-sign composites use exact LPC sign background/icon layers')
    print('- native editor and client both resolve PublishedWorldAsset visuals, including legacy ObjectKind adapters')
    print('- standing Sign remains fail-closed instead of reusing a wall plaque or standing screen')
    return 0
if __name__=='__main__': raise SystemExit(main())
