#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
AUTH=ROOT/'content/buildings/building_instance_authority_v1.json'
CONTRACT=ROOT/'content/buildings/building_instance_persistence_contract_v1.json'
CATALOG=ROOT/'content/buildings/building_instance_catalog_v1.json'
INSTANCE=ROOT/'content/buildings/instances/three_level_house_runtime_acceptance_v1.json'
RECIPE=ROOT/'content/buildings/recipes/three_level_house_prototype_v1.json'
SCENE=ROOT/'content/worldgen/scenes/world_asset_acceptance/building_instance_persistence_acceptance_scene_v1.json'
PACK=ROOT/'content/worldgen/packs/worldgen_home_island_test_v0_11.json'
ASSET_RUST=ROOT/'crates/haven_assets/src/building_instance.rs'
ASSET_AUTHORING=ROOT/'crates/haven_assets/src/building_instance/authoring.rs'
ASSET_PERSISTENCE=ROOT/'crates/haven_assets/src/building_instance/persistence.rs'
ASSET_WORLDGEN=ROOT/'crates/haven_assets/src/building_instance/worldgen.rs'
RECIPE_RUST=ROOT/'crates/haven_assets/src/building_recipe.rs'
GAME_BOOT=ROOT/'crates/haven_game/src/game_bootstrap.rs'
GAME_RUNTIME=ROOT/'crates/haven_game/src/building_instance_runtime.rs'
GAME_SYNC=ROOT/'crates/haven_game/src/building_instance_sync.rs'
GAME_MAIN=ROOT/'crates/haven_game/src/main.rs'
GAME_PERSIST=ROOT/'crates/haven_game/src/runtime_persistence.rs'
GAME_INTERACT=ROOT/'crates/haven_game/src/runtime_interactions.rs'
EDITOR_PREVIEW=ROOT/'apps/haven_editor_native/src/app/building_instance_preview.rs'
EDITOR_INPUT=ROOT/'apps/haven_editor_native/src/app/input.rs'
BUILD_PS=ROOT/'tools/build/Build.ps1'
BUILD_SH=ROOT/'tools/build/Build.sh'
COMMANDS=ROOT/'tools/control/ProjectCommandRegistry.ps1'
BUILDER=ROOT/'tools/automation/assets/Build-BuildingPersistenceAcceptanceSceneV1.py'


def need(value,msg):
    if not value:
        raise SystemExit('FAIL W46C BuildingInstance persistence authority: '+msg)


def world_pass_at_least(value, minimum):
    import re
    match=re.search(r'W(\d+)', str(value or ''))
    return bool(match and int(match.group(1)) >= minimum)

def load(path):
    need(path.is_file(),f'missing {path.relative_to(ROOT)}')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def text(path):
    need(path.is_file(),f'missing {path.relative_to(ROOT)}')
    return path.read_text(encoding='utf-8-sig')


def main():
    auth=load(AUTH); contract=load(CONTRACT); catalog=load(CATALOG); instance=load(INSTANCE)
    recipe=load(RECIPE); scene=load(SCENE); pack=load(PACK)
    need(auth.get('pass')=='167Z109W46C','instance authority pass drift')
    need(auth.get('authority')=='BuildingInstanceRegistry','BuildingInstanceRegistry is not placement/state authority')
    need(auth.get('recipeAuthority')=='BuildingRecipeRegistry','recipe authority drift')
    need(auth.get('visualAuthority')=='PublishedWorldAssetRegistry','visual authority drift')
    rules=auth.get('rules',{})
    for key in [
        'authoredPlacementUsesStableInstanceId','editorPlaceMoveDeleteMutatesBuildingInstanceAuthority',
        'continuousSurfacePlacementUsesGlobalAnchor','worldgenPlacementUsesBuildingInstanceRegistry',
        'saveStateUsesDeltaOverlay','persistentDoorStateOverridesRecipeDefault',
        'persistentStateNeverContainsCameraCutaway','multiplayerReplicatesAuthoritativeBuildingStateOnly',
        'viewActiveLevelAndInsideRemainCameraLocal','roofCutawayIsCameraLocal','wallCutawayIsCameraLocal',
        'multiplayerSequenceIsGlobalNotPerInstanceRevision','replicatedBuildingStateAppliesThroughBuildingInstanceRegistry'
    ]:
        need(rules.get(key) is True,f'authority rule {key} regressed')

    need(contract.get('schema')=='havenwild.building_instance_persistence_contract.v1','persistence contract schema drift')
    need(contract.get('pass')=='167Z109W46C','persistence contract pass drift')
    delta=contract.get('saveDelta',{})
    need(delta.get('schema')=='havenwild.building_instance_world_state.v1','save delta schema drift')
    forbidden=set(delta.get('forbidden',[]))
    need({'inside','activeLevel','roof visibility','wall cutaway visibility','camera state'} <= forbidden,'camera-local fields not explicitly forbidden from save state')
    net=contract.get('multiplayer',{})
    need(net.get('hostAuthoritative') is True,'building multiplayer state must be host authoritative')
    need(net.get('globalSequenceSeparateFromInstanceRevision') is True,'building network sequence is not separated from per-instance revision')
    need(net.get('replicaApplyUsesBuildingInstanceRegistry') is True,'building replica apply path bypasses BuildingInstanceRegistry')
    need({'inside','activeLevel','roof cutaway','front-wall cutaway'} <= set(net.get('cameraLocalNotReplicated',[])),'camera-local view state not excluded from network')

    need(world_pass_at_least(catalog.get('pass'),46),'catalog regressed behind W46C')
    need(instance.get('origin')=='diagnostic' and instance.get('placementSpace')=='scene_local','W46B diagnostic instance provenance/space not explicit')

    opening_ids=[]
    for level in recipe.get('levels',[]):
        opening_ids.extend(o['id'] for o in level.get('openings',[]))
    need(len(opening_ids)==len(set(opening_ids)),'recipe opening ids are not globally stable/unique')
    need('front_door' in opening_ids,'front_door acceptance opening missing')

    need(scene.get('sceneId')=='pcg_w46c_acceptance_0_0','W46C PCG acceptance scene id drift')
    need(scene.get('sceneSize')==[96,64],'W46C acceptance scene must be one full runtime partition')
    need(scene.get('objects')==[],'W46C scene must contain zero baked BuildingInstance object carriers')
    placements=scene.get('buildingInstances',[])
    need(len(placements)==1,'W46C acceptance must declare exactly one worldgen BuildingInstance')
    placement=placements[0]
    need(placement.get('id')=='havenwild.acceptance.pcg_three_level_house','worldgen stable instance id drift')
    need(placement.get('recipeId')=='havenwild.prototype.three_level_house','worldgen recipe reference drift')
    need(placement.get('placementSpace')=='continuous_surface','worldgen placement is not continuous-surface')
    need(placement.get('surfaceRegionId')=='w46c_acceptance','worldgen surface region drift')
    need(placement.get('globalAnchorTile')==placement.get('anchorTile')==[31,29],'worldgen/global anchor drift')
    acc=scene.get('acceptance',{})
    need(acc.get('pass')=='167Z109W46C','scene acceptance pass drift')
    need(acc.get('saveSchema')=='havenwild.building_instance_world_state.v1','scene save schema drift')
    need(acc.get('cameraLocalStateExcludedFromSave') is True and acc.get('cameraLocalStateExcludedFromReplication') is True,'scene camera-local acceptance split missing')
    rel=SCENE.relative_to(ROOT).as_posix()
    need(rel in pack.get('sceneFiles',[]) and rel in pack.get('smokeTests',[]),'W46C scene not registered in development test pack')
    tw=pack.get('testWorld',{})
    need(tw.get('buildingInstancePersistenceAcceptanceSceneId')=='pcg_w46c_acceptance_0_0','test-world W46C navigation id missing')
    need(tw.get('buildingInstancePersistenceAcceptanceScene')==rel,'test-world W46C navigation path missing')

    ar='\n'.join([text(ASSET_RUST), text(ASSET_AUTHORING), text(ASSET_PERSISTENCE), text(ASSET_WORLDGEN)])
    rr=text(RECIPE_RUST); gb=text(GAME_BOOT)
    gr=text(GAME_RUNTIME); gs=text(GAME_SYNC); gm=text(GAME_MAIN); gp=text(GAME_PERSIST); gi=text(GAME_INTERACT)
    ep=text(EDITOR_PREVIEW); ei=text(EDITOR_INPUT)
    bps=text(BUILD_PS); bsh=text(BUILD_SH); commands=text(COMMANDS)
    need(BUILDER.is_file(),'W46C acceptance builder missing')

    for token in [
        'pub enum BuildingInstanceOrigin','pub enum BuildingPlacementSpace',
        'pub struct BuildingInstancePersistentState','pub struct BuildingInstanceWorldStateFile',
        'pub fn resolved_for_scene','pub fn merge_worldgen_pack_placements',
        'pub fn save_world_state_to_path','pub fn apply_world_state_from_path',
        'pub fn place_authored_instance','pub fn move_authored_instance','pub fn delete_authored_instance',
        'pub fn effective_opening_state','pub fn set_opening_state','pub fn apply_replicated_opening_states','pub fn visible_pieces_for_instance'
    ]:
        need(token in ar,f'haven_assets BuildingInstance authority missing {token}')
    need('world_upserts:' in ar and 'removed_instance_ids:' in ar and 'persistent_states:' in ar,'delta overlay domains missing from registry')
    need('fnv1a64' in ar,'deterministic generated BuildingInstance id hash missing')
    need('pub fn opening(' in rr and 'duplicates persistent opening id' in rr,'BuildingRecipe opening ids are not persistence-safe')

    need('fn building_instance_save_path(' in gm,'runtime lacks BuildingInstance save-sidecar path helper')
    need('.join("buildings")' in gm and '.join("building_instance_deltas.json")' in gm,'BuildingInstance save sidecar path drift')
    need('building_instance_save_path(&save_paths.root)' in gb,'bootstrap does not derive BuildingInstance sidecar from canonical save root')
    need('building_instance_save_path(&self.save_paths.root)' in gp,'runtime persistence does not derive BuildingInstance sidecar from canonical save root')

    need('merge_worldgen_pack_placements' in gb and 'apply_world_state_from_path' in gb,'bootstrap does not converge generated placement + save overlay')
    for token in ['resolved_active_building_instances','effective_opening_state','try_interact_building_opening_at','set_opening_state','visible_pieces_for_instance']:
        need(token in gr,f'runtime BuildingInstance path missing {token}')
    need('try_interact_building_opening_at' in gi,'interaction dispatcher does not target BuildingRecipe openings')
    need('save_world_state_to_path' in gp and 'reload_building_instance_authority' in gp,'runtime save/load does not preserve BuildingInstance deltas')
    need('merge_worldgen_pack_placements' in gp and 'apply_world_state_from_path' in gp,'runtime worldgen/load does not re-converge BuildingInstance authority')

    need('pub(crate) struct BuildingInstanceStateSnapshot' in gs and 'pub(crate) struct BuildingInstanceStateEnvelope' in gs,'transport-neutral BuildingInstance replication envelope missing')
    snapshot=gs[gs.index('pub(crate) struct BuildingInstanceStateSnapshot'):gs.index('pub(crate) struct BuildingInstanceStateEnvelope')]
    need('inside' not in snapshot and 'active_level' not in snapshot and 'activeLevel' not in snapshot,'camera-local view leaked into building replication snapshot')
    need('opening_states' in snapshot and 'authoritative_anchor_tile' in snapshot,'authoritative building snapshot lacks state/placement data')
    for token in ['recipe_id','scene_id','origin','surface_region_id','removed']:
        need(token in snapshot,f'building replication snapshot cannot carry placement identity field {token}')
    need('host_authoritative' in gs and 'validate_for_client' in gs,'building replication adapter does not enforce host authority')
    need('host_building_instance_state_envelope' in gs and 'apply_replicated_building_instance_state' in gs,'runtime building host/replica sync adapter missing')
    need('upsert_world_instance' in gs and 'remove_world_instance' in gs and 'apply_replicated_opening_states' in gs,'replica apply path does not converge through BuildingInstanceRegistry')
    need('building_state_sequence' in gm and 'last_applied_building_state_sequence' in gm,'runtime lacks separate global building replication sequence state')
    need('sequence: self.building_state_sequence' in gs,'building host snapshot still uses per-instance revision as network sequence')

    for token in ['place_building_instance_at_scene_cursor','move_building_instance_at_scene_cursor','delete_building_instance_at_scene_cursor','ContinuousSurfaceManifest::for_world']:
        need(token in ep,f'native editor BuildingInstance authoring missing {token}')
    need(ep.count('save_authored_to_project_root(repo_root_dir())') >= 3,'editor place/move/delete does not immediately persist BuildingInstance source authority')
    need('EditorCommandKind::SceneMutation' in ep,'editor building authoring does not use the existing command-bus mutation lane')
    need('KeyCode::B' in ei and 'LeftAlt' in ei and 'delete_building_instance_at_scene_cursor' in ei,'native editor W46C building controls missing from exact SceneMap input lane')
    need('building_input_consumed' in ei,'building floor/move controls are not protected from overlapping SceneMap shortcuts')

    need('Build-BuildingPersistence' in bps and '"building-persistence"' in bps,'PowerShell build wrapper missing W46C command')
    need('building-persistence)' in bsh,'shell build wrapper missing W46C command')
    need("Id='46'" in commands and "Args=@('building-persistence')" in commands,'root utility command 46 missing')

    print('PASS W46C BuildingInstance placement/save/PCG convergence')
    print('- authored + worldgen + save-delta placements converge on BuildingInstanceRegistry')
    print('- continuous-surface placement resolves stable global anchors into active storage partitions')
    print('- door render/collision/interaction share persistent effective opening state')
    print('- editor place/move/delete persist authored instance catalog/files immediately; runtime save owns delta sidecar only')
    print('- multiplayer snapshot carries authoritative placement/opening state and excludes camera-local cutaway/floor view')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
