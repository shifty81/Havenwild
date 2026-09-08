#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
CONTRACT=ROOT/'content/buildings/interior_grammar_contract_v1.json'
HOUSE=ROOT/'content/buildings/recipes/three_level_house_prototype_v1.json'
RECIPE_RUST=ROOT/'crates/haven_assets/src/building_recipe.rs'
INTERIOR_RUST=ROOT/'crates/haven_assets/src/building_recipe/interior.rs'
INSTANCE_RUST=ROOT/'crates/haven_assets/src/building_instance/interior.rs'
PERSIST_RUST=ROOT/'crates/haven_assets/src/building_instance/persistence.rs'
GAME_RUNTIME=ROOT/'crates/haven_game/src/building_instance_runtime.rs'
GAME_SYNC=ROOT/'crates/haven_game/src/building_instance_sync.rs'
GAME_INTERACT=ROOT/'crates/haven_game/src/runtime_interactions.rs'

def need(v,msg):
    if not v: raise SystemExit('FAIL W47 Building interior grammar: '+msg)
def load(p):
    need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8-sig'))
def text(p):
    need(p.is_file(),f'missing {p.relative_to(ROOT)}')
    return p.read_text(encoding='utf-8-sig')

def published():
    out={}
    for p in sorted((ROOT/'content/asset_packs/havenwild_objects').glob('published*.json')):
        d=load(p)
        for e in d.get('entries',[]):
            out[e['id']]=e
            for a in e.get('aliases',[]): out[a]=e
    return out

def main():
    c=load(CONTRACT); house=load(HOUSE); pub=published()
    need(c.get('schema')=='havenwild.building_interior_grammar.v1','contract schema drift')
    need(c.get('pass')=='167Z109W47','contract pass drift')
    need(c.get('authority')=='BuildingRecipeRegistry','recipe authority drift')
    need(c.get('instanceAuthority')=='BuildingInstanceRegistry','instance authority drift')
    need(c.get('visualAuthority')=='PublishedWorldAssetRegistry','visual authority drift')
    rules=c.get('rules',{})
    for k in ['roomsRemainRecipeOwned','furnishingsRemainRecipeOwned','furnishingVisualsResolveThroughPublishedWorldAssetRegistry','furnishingStatePersistsInBuildingInstanceDelta','furnishingStateReplicatesHostAuthoritatively','cameraCutawayNeverPersistsAsFurnitureState','navigationUsesRoomAndFurnishingAuthority','wallMountedAssetsRequireWallAttachment','unresolvedVisualsFailClosedAsDeferredExactSource','ordinaryInteriorsNeverRequireSeparateScene']:
        need(rules.get(k) is True,f'contract rule {k} regressed')
    need(c.get('persistentState',{}).get('field')=='furnishingStates','persistent furnishing field drift')

    furnishings=[f for level in house.get('levels',[]) for f in level.get('furnishings',[])]
    need(len(furnishings)==7,'prototype house must exercise seven W47 furnishings')
    need(len({f['id'] for f in furnishings})==7,'prototype furnishing ids are not globally unique')
    need(all(level.get('navigation',{}).get('walkableRects') for level in house['levels']),'prototype levels lack explicit navigation authority')
    for f in furnishings:
        aid=f.get('assetId'); need(aid in pub,f'prototype furnishing references unknown PublishedWorldAsset {aid}')
        e=pub[aid]
        need(e.get('certification') not in {'rejected','missing','placeholder'},f'prototype furnishing uses unusable asset {aid}')
        if f.get('state'):
            need(f['state'] in e.get('states',[]),f'{f["id"]} state {f["state"]} unsupported by {aid}')

    rr=text(RECIPE_RUST); ir=text(INTERIOR_RUST); bi=text(INSTANCE_RUST); pr=text(PERSIST_RUST); gr=text(GAME_RUNTIME); gs=text(GAME_SYNC); gi=text(GAME_INTERACT)
    for token in ['pub furnishings: Vec<BuildingFurnishingPlacement>','pub navigation: BuildingLevelNavigation','Furnishing,','materialize_level_furnishings','validate_interior_assets']:
        need(token in rr,f'BuildingRecipe W47 field/path missing {token}')
    for token in ['pub enum BuildingFurnishingKind','pub struct BuildingFurnishingPlacement','pub struct BuildingInteractionSocket','deferred_exact_source','wallAttachment']:
        need(token in ir,f'interior grammar implementation missing {token}')
    for token in ['navigation_allows_world_tile','furnishing_blocks_world_tile','furnishing_interaction_at']:
        need(token in bi,f'BuildingInstance interior resolver missing {token}')
    for token in ['furnishing_states','effective_furnishing_state','set_furnishing_state','apply_replicated_furnishing_states']:
        need(token in pr,f'furnishing persistent state path missing {token}')
    need('furnishing_states:' in gs and 'apply_replicated_furnishing_states' in gs,'host/replica furnishing state missing')
    snapshot=gs[gs.index('pub(crate) struct BuildingInstanceStateSnapshot'):gs.index('pub(crate) struct BuildingInstanceStateEnvelope')]
    need('inside' not in snapshot and 'active_level' not in snapshot,'camera-local state leaked into replicated furnishing snapshot')
    for token in ['furnishing_blocks_world_tile','try_interact_building_furnishing_at','set_furnishing_state','host_building_instance_state_envelope']:
        need(token in gr,f'runtime interior integration missing {token}')
    need('try_interact_building_furnishing_at' in gi,'interaction dispatcher bypasses BuildingInstance furnishings')

    print('PASS W47 Building interior grammar authority')
    print('- rooms/furnishings/navigation remain BuildingRecipe-owned inside the same multi-level BuildingInstance')
    print('- furnishing visuals resolve through PublishedWorldAssetRegistry; unresolved visuals fail closed')
    print('- furnishing state shares BuildingInstance save deltas and host-authoritative replication')
    print('- prototype house now exercises 7 real furnishings across cellar/ground/upstairs')
    return 0
if __name__=='__main__': raise SystemExit(main())
