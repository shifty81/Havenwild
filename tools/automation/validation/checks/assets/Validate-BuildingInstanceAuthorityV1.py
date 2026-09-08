#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
CATALOG=ROOT/'content/buildings/building_instance_catalog_v1.json'
AUTH=ROOT/'content/buildings/building_instance_authority_v1.json'
INSTANCE=ROOT/'content/buildings/instances/three_level_house_runtime_acceptance_v1.json'
RECIPE=ROOT/'content/buildings/recipes/three_level_house_prototype_v1.json'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/building_instance_acceptance_scene_v1.json'
PACK=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
OBJECT_PACK=ROOT/'content/asset_packs/havenwild_objects/pack.json'
RUST=ROOT/'crates/haven_assets/src/building_instance.rs'
LIB=ROOT/'crates/haven_assets/src/lib.rs'
GAME_MAIN=ROOT/'crates/haven_game/src/main.rs'
GAME_BOOT=ROOT/'crates/haven_game/src/game_bootstrap.rs'
GAME_RUNTIME=ROOT/'crates/haven_game/src/building_instance_runtime.rs'
GAME_MOVE=ROOT/'crates/haven_game/src/runtime_scene_navigation.rs'
GAME_INTERACT=ROOT/'crates/haven_game/src/runtime_interactions.rs'
GAME_DRAW=ROOT/'crates/haven_game/src/runtime_draw.rs'
EDITOR_MOD=ROOT/'apps/haven_editor_native/src/app/mod.rs'
EDITOR_PREVIEW=ROOT/'apps/haven_editor_native/src/app/building_instance_preview.rs'
EDITOR_DRAW=ROOT/'apps/haven_editor_native/src/app/draw_scene_views.rs'
EDITOR_INPUT=ROOT/'apps/haven_editor_native/src/app/input.rs'
ATLAS=ROOT/'apps/haven_editor_native/src/app/atlas_render.rs'
BUILDER=ROOT/'tools/automation/assets/Build-BuildingInstanceAcceptanceSceneV1.py'

def need(v,msg):
    if not v: raise SystemExit('FAIL W46B BuildingInstance authority: '+msg)

def world_pass_at_least(value, minimum):
    import re
    match=re.search(r'w(\d+)', str(value or ''), re.IGNORECASE)
    return bool(match and int(match.group(1)) >= minimum)

def load(p):
    need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8-sig'))

def published():
    out={}
    for p in sorted((ROOT/'content/asset_packs/havenwild_objects').glob('published*.json')):
        d=load(p)
        if d.get('schema') not in {'havenwild.published_world_asset_catalog.v1','havenwild.placeable_catalog.v1'}: continue
        for e in d.get('entries',[]):
            out[e['id']]=e
            for a in e.get('aliases',[]): out[a]=e
    return out

def main():
    cat=load(CATALOG); auth=load(AUTH); inst=load(INSTANCE); recipe=load(RECIPE); scene=load(SCENE); pack=load(PACK); op=load(OBJECT_PACK)
    need(BUILDER.is_file(),'acceptance builder missing')
    need(cat.get('schema')=='havenwild.building_instance_catalog.v1','catalog schema drift')
    need(world_pass_at_least(cat.get('pass'),46),'catalog pass drift')
    need(cat.get('authority')=='BuildingInstanceRegistry','catalog authority drift')
    entries={entry.get('id'):entry for entry in cat.get('entries',[])}
    need(entries.get('havenwild.acceptance.three_level_house')=={'id':'havenwild.acceptance.three_level_house','path':'content/buildings/instances/three_level_house_runtime_acceptance_v1.json','status':'candidate'},'diagnostic house instance catalog drift')
    need(auth.get('schema')=='havenwild.building_instance_authority.v1','authority schema drift')
    need(auth.get('authority')=='BuildingInstanceRegistry','instance authority drift')
    need(auth.get('recipeAuthority')=='BuildingRecipeRegistry','recipe authority duplicated/drifted')
    need(auth.get('visualAuthority')=='PublishedWorldAssetRegistry','visual authority duplicated/drifted')
    r=auth.get('rules',{})
    for k in ['scenePlacementReferencesRecipeById','instanceOwnsOnePersistentIdentityAcrossLevels','ordinaryFloorsRemainSameScene','cameraViewStateIsPerClient','allLevelsRemainAuthoritative','stairTraversalMutatesLevelNotScene','roofCutawayIsCameraLocal','wallCutawayIsCameraLocal','wallCollisionUsesLogicalRecipeGeometry','missingFacingVisualDoesNotRemoveCollision','publishedWorldAssetRegistryRemainsVisualAuthority']:
        need(r.get(k) is True,f'authority rule {k} regressed')
    need(inst.get('schema')=='havenwild.building_instance.v1','instance schema drift')
    need(inst.get('recipeId')==recipe.get('id')=='havenwild.prototype.three_level_house','instance recipe mismatch')
    need(inst.get('sceneId')=='building_instance_acceptance','instance scene mismatch')
    need(inst.get('anchorTile')==[24,14] and inst.get('initialLevel')==0,'instance placement/default level drift')
    need(inst.get('diagnosticOnly') is True,'first runtime instance must remain diagnostic')
    levels={x['level']:x for x in recipe.get('levels',[])}
    need(set(levels)=={-1,0,1},'recipe lost -1/0/+1 structural levels')
    front=next(o for o in levels[0]['openings'] if o['id']=='front_door')
    need(front.get('state')=='closed','runtime acceptance door must start closed')
    connectors={c['id']:c for c in recipe.get('connectors',[])}
    need(connectors['cellar_to_ground']['fromTile']==[2,4] and connectors['cellar_to_ground']['toTile']==[2,4],'cellar connector placement drift')
    need(connectors['ground_to_upstairs']['fromTile']==[6,4] and connectors['ground_to_upstairs']['toTile']==[6,4],'upstairs connector placement drift')
    pub=published(); door=pub['door_basic']
    closed_geom=next(g['footprint'] for g in door['state_geometry'] if g['state']=='closed')
    need(closed_geom.get('blocks_movement') is True,'closed acceptance door must block movement')
    open_geom=next(g['footprint'] for g in door['state_geometry'] if g['state']=='open_left')
    need(open_geom.get('blocks_movement') is False and open_geom.get('collision_size')==[0,0],'open acceptance door still blocks movement')
    need(scene.get('sceneId')=='building_instance_acceptance' and scene.get('role')=='diagnostic_only','acceptance scene identity drift')
    need(scene.get('objects')==[],'W46B acceptance must not bake BuildingRecipe pieces into SceneMap objects')
    need(scene.get('spawns')==[{'id':'player_default','tile':[28,23]}],'acceptance spawn drift')
    acc=scene.get('acceptance',{})
    need(acc.get('pass')=='167Z109W46B' and acc.get('runtimeMaterialized') is True,'runtime materialization acceptance drift')
    need(acc.get('staticSceneObjectCount')==0,'static carrier count must remain zero')
    rel=SCENE.relative_to(ROOT).as_posix()
    need(rel in pack.get('sceneFiles',[]) and rel in pack.get('smokeTests',[]),'W46B scene absent from test pack')
    tw=pack.get('testWorld',{})
    need(tw.get('buildingInstanceAcceptanceSceneId')=='building_instance_acceptance' and tw.get('buildingInstanceAcceptanceScene')==rel,'W46B test-world navigation missing')
    need(op.get('version')=='0.8.0-w46b' or world_pass_at_least(op.get('version'),46), 'object pack not advanced to W46B')
    src={x.get('id'):x for x in op.get('sources',[])}
    need(src.get('building_instance_catalog_w46b',{}).get('path')==CATALOG.relative_to(ROOT).as_posix(),'instance catalog sidecar missing')
    sem={(x.get('semantic_id'),x.get('category')):x for x in op.get('assets',[])}
    item=sem.get(('building.instance.catalog.default','editor_template'))
    need(item is not None,'instance catalog not discoverable')
    need(item.get('metadata',{}).get('authority')=='BuildingInstanceRegistry','pack instance authority drift')
    rust=RUST.read_text(); lib=LIB.read_text(); gm=GAME_MAIN.read_text(); gb=GAME_BOOT.read_text(); gr=GAME_RUNTIME.read_text(); mv=GAME_MOVE.read_text(); gi=GAME_INTERACT.read_text(); gd=GAME_DRAW.read_text(); em=EDITOR_MOD.read_text(); ep=EDITOR_PREVIEW.read_text(); ed=EDITOR_DRAW.read_text(); ei=EDITOR_INPUT.read_text(); ar=ATLAS.read_text()
    need('pub struct BuildingInstanceRegistry' in rust and 'pub struct BuildingInstanceViewState' in rust,'Rust instance/view authority missing')
    need('connector_traversal_at' in rust and 'wall_blocks_world_tile' in rust and 'visible_pieces' in rust,'Rust traversal/collision/view resolver missing')
    need('pub mod building_instance;' in lib,'haven_assets does not export building_instance')
    need('building_instance_registry:' in gm and 'building_instance_views:' in gm,'game lacks BuildingInstance runtime state')
    need('BuildingInstanceRegistry::load_from_project_root' in gb,'game bootstrap does not load instance authority')
    need('building_move_allowed' in mv and 'refresh_building_instance_views' in mv,'player movement not wired to building collision/view state')
    need('try_traverse_building_connector_at' in gi,'interaction path not wired to same-scene stair traversal')
    need('visible_building_draw_pieces' in gd and 'RenderCommand::BuildingPiece' in gd,'runtime draw path does not materialize building pieces')
    need('building_recipe_registry:' in em and 'building_instance_registry:' in em and 'building_preview_views:' in em,'native editor lacks building authority state')
    need('draw_building_instance_previews' in ep and 'cycle_building_preview_level' in ep and 'toggle_building_preview_cutaway' in ep,'native editor building preview controls missing')
    need('draw_building_instance_previews(scene)' in ed,'scene canvas does not render native building instances')
    need('KeyCode::PageUp' in ei and 'KeyCode::PageDown' in ei and 'KeyCode::Home' in ei,'native editor floor/cutaway preview controls missing')
    need('draw_published_asset_at_tile' in ar,'editor does not reuse PublishedWorldAsset visual authority')
    print('PASS W46B BuildingInstance runtime/editor authority')
    print('- scene placement references one BuildingRecipe; visual identity remains PublishedWorldAssetRegistry')
    print('- client materializes same-world building pieces with logical wall collision and camera-local cutaway state')
    print('- interact on dedicated stair tiles changes -1/0/+1 structural level without changing SceneMap identity')
    print('- native editor materializes the same instance and previews floors with PageUp/PageDown; Home toggles roof/cutaway view')
    print('- building_instance_acceptance contains zero baked structural object carriers')
    return 0
if __name__=='__main__': raise SystemExit(main())
