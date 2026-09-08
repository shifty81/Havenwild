#!/usr/bin/env python3
"""Certify W57K8 starter-cottage editor/exterior/interior presentation authority."""
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[5]

def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8-sig'))
def text(rel): return (ROOT/rel).read_text(encoding='utf-8')
def req(ok,msg):
    if not ok: raise AssertionError(msg)

def published():
    out={}
    for p in sorted((ROOT/'content/asset_packs/havenwild_objects').glob('published_*.json')):
        try: d=json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception: continue
        if d.get('schema')!='havenwild.published_world_asset_catalog.v1': continue
        for e in d.get('entries',[]): out[e['id']]=e
    return out

def collision_cells(entry, state, anchor):
    footprint=entry.get('footprint',{})
    for geo in entry.get('state_geometry',[]):
        if geo.get('state')==state:
            footprint=geo.get('footprint',footprint); break
    if not footprint.get('blocks_movement',False): return set()
    off=footprint.get('collision_offset',[0,0]); size=footprint.get('collision_size',[0,0])
    return {(anchor[0]+off[0]+x,anchor[1]+off[1]+y) for y in range(size[1]) for x in range(size[0])}

try:
    recipe=load('content/buildings/recipes/estate_starter_cottage_v1.json')
    inst=load('content/buildings/instances/estate_starter_cottage_v1.json')
    pack=load('content/asset_packs/havenwild_objects/pack.json')
    side=load('content/asset_packs/havenwild_objects/published_structure_front_gable_w57k8_v1.json')
    grammar=load('content/buildings/exterior_grammar_contract_v1.json')
    profile=load('content/estates/estate_generation_profile_v1.json')
    topology=load('content/buildings/roof_topology_contract_v1.json')
    assets=published()

    req(recipe.get('version') in {'1.4.0-w57k8','1.5.0-w57k9','1.6.0-w57k10'},'K8+ cottage recipe lineage missing')
    req(recipe.get('footprint')==[9,9] and inst.get('anchorTile')==[55,28],'K8 9x9 envelope/anchor drifted')
    level=recipe['levels'][0]; openings={o['id']:o for o in level['openings']}
    req(openings['front_door']['tile']==[4,8],'K8 front door local tile drifted')
    req([inst['anchorTile'][0]+4,inst['anchorTile'][1]+8]==[59,36],'K8 must preserve Estate front-door world tile [59,36]')

    source_ids={s['id'] for s in pack['sources']}; asset_ids={a['id'] for a in pack['assets']}
    req('published_structure_front_gable_w57k8_catalog' in source_ids,'K8 front-gable sidecar is not mounted')
    req('published_structure_front_gable_w57k8' in asset_ids,'K8 front-gable catalog asset is not mounted')
    req('published_structure_authored_roofs_w57k7_catalog' not in source_ids,'misclassified K7 roof sidecar remains active')
    req('published_structure_authored_roofs_w57k7' not in asset_ids,'misclassified K7 roof catalog remains active')

    pubs={e['id']:e for e in side['entries']}
    roof_asset=pubs['roof_gable_shingle_brown_shallow_7x4_roofline']
    fill_asset=pubs['wall_siding_plain_cream_gable_fill']
    req(roof_asset['visual']['frames'][0]['source_rect']==[544,0,224,128],'reviewed K8 roofline source rect drifted')
    req(roof_asset['structure']['topology_role']=='front_gable_roofline','roofline is misclassified as a filled roof/module')
    req(fill_asset['visual']['frames'][0]['source_rect']==[64,0,32,32] and fill_asset['footprint']['blocks_movement'] is False,'gable infill publication drifted')

    walls={w['id']:w for w in level['wallRuns']}
    req(walls['gable_fill_peak']['start']==[4,3] and walls['gable_fill_peak']['length']==1,'gable peak row drifted')
    req(walls['gable_fill_mid']['start']==[3,4] and walls['gable_fill_mid']['length']==3,'gable middle row drifted')
    base_runs=[walls[i] for i in ('gable_fill_base_left','gable_fill_base','gable_fill_base_right')] if all(i in walls for i in ('gable_fill_base_left','gable_fill_base','gable_fill_base_right')) else [walls['gable_fill_base']]
    req(sum(run['length'] for run in base_runs)==5 and min(run['start'][0] for run in base_runs)==2 and all(run['start'][1]==5 for run in base_runs),'gable base row no longer spans the certified five-cell base')
    req(walls['south_left']['start']==[2,8] and walls['south_right']['start']==[6,8],'five-tile wall plate drifted')
    roof=recipe['roof']; req(roof['rect']==[1,2,7,4],'seven-tile roof envelope drifted')
    req(len(roof['authoredModules'])==1 and roof['authoredModules'][0]['assetId']==roof_asset['id'],'starter cottage must consume one reviewed roofline')

    nav=level['navigation']; protected={tuple(t) for t in nav['protectedTiles']}
    req(protected=={(4,y) for y in range(2,9)},'protected center circulation lane drifted')
    req(not any(w['id']=='room_divider' or w['id'].startswith('divider_cap_') for w in level['wallRuns']),'blocking divider/cap presentation returned')
    rooms={r['id']:r for r in level['rooms']}
    for f in level['furnishings']:
        e=assets.get(f['assetId']); req(e is not None,f"unpublished furnishing {f['assetId']}")
        if f.get('blocksNavigation'):
            overlap=collision_cells(e,f.get('state'),f['tile']) & protected
            req(not overlap,f"{f['id']} collision footprint blocks protected circulation {sorted(overlap)}")
        rx,ry,rw,rh=rooms[f['roomId']]['rect']; x,y=f['tile']
        req(rx<=x<rx+rw and ry<=y<ry+rh,f"{f['id']} anchor is outside declared room")

    editor=text('apps/haven_editor_native/src/app/atlas_render.rs')
    editor_app=text('apps/haven_editor_native/src/app/mod.rs')
    runtime=text('crates/haven_game/src/runtime_terrain_base_draw.rs')
    core=text('crates/haven_core/src/enclosed_wall_topology.rs')
    interior=text('crates/haven_assets/src/building_recipe/interior.rs')
    bootstrap=text('crates/haven_game/src/game_bootstrap.rs')
    req('let root = repo_root_dir();' in editor and 'RuntimeAssetSession::discover_tolerant(&root)' in editor,'Native Editor textures do not use repository-root authority')
    req('published textures {}/{}' in editor,'Native Editor does not expose published texture readiness diagnostics')
    req('BuildingRecipeRegistry::load_from_project_root(&building_project_root)' in editor_app,'Native Editor building recipe loading is not repo-root anchored')
    req('HouseInteriorWallPresentation' in core and 'CutawayEdge' in core,'house interior semantic presentation resolver missing')
    req('side/front shell cells are collision-only' in runtime,'runtime still draws repeated side/front cutaway rails')
    req('protected_tiles' in interior and 'collision footprint reaches protected circulation tile' in interior,'Rust interior validator does not protect full furnishing collision footprints')
    req('existing.dimensions != materialized.scene.dimensions' in bootstrap and 'legacy_cottage_dimensions' in bootstrap,'generated linked-interior dimension migration missing')

    req(grammar.get('pass')=='167Z109W57K8' and profile.get('pass')=='167Z109W57K8' and topology.get('pass')=='167Z109W57K8','K8 building/profile/topology authority passes disagree')
    ref=topology['authoredAssemblyPolicy']['starterCottageReference']
    req(ref['requiresGableWallInfill'] is True and ref['gableWallInfillRows']==[1,3,5] and ref['sideEaveTiles']==1,'K8 roof topology reference lost wall-infill/eave rules')

    print('PASS W57K8 cottage presentation authority reset')
    print('- Native Editor building textures share repository-root discovery and report published texture readiness')
    print('- one reviewed 7x4 front-gable roofline sits over a five-tile wall plate with one-tile eaves and 1/3/5 siding infill')
    print('- linked interior keeps the K8 open-plan floor authority; K9 may extend playable depth independently of exterior footprint')
    print('- side/front interior shell collision is retained without repeating CutawayOverlay rails')
except Exception as exc:
    print(f'FAIL W57K8 cottage presentation authority reset: {exc}',file=sys.stderr); sys.exit(1)
