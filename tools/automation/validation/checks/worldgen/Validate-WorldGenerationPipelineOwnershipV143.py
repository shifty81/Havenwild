#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
PIPE=ROOT/'content/worldgen/world_generation_pipeline_v1.json'
MAN=ROOT/'content/validation/validation_manifest_v1.json'
LIB=ROOT/'crates/haven_world/src/lib.rs'
MOD=ROOT/'crates/haven_world/src/world_generation_pipeline.rs'
errors=[]
def load(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p}: {e}'); return {}
p=load(PIPE); vm=load(MAN)
if p.get('schema')!='havenwild.world_generation_pipeline.v1' or p.get('version')!=1: errors.append('wrong pipeline schema/version')
policy=p.get('policy',{})
for k in ('deterministicByDefault','undeclaredMutation','stageOrder','previewMustBeReversible','authoredOverridesSurviveRegeneration','playerDeltasSurviveRegeneration','futureStageRule'):
    if k not in policy: errors.append(f'missing policy {k}')
if policy.get('undeclaredMutation')!='forbidden': errors.append('undeclared mutation must be forbidden')
if not policy.get('authoredOverridesSurviveRegeneration') or not policy.get('playerDeltasSurviveRegeneration'): errors.append('authored overrides and player deltas must survive regeneration')
layers=p.get('layers',[]); stages=p.get('stages',[])
layer_ids=[x.get('id') for x in layers]; owners={x.get('id'):x.get('owner') for x in layers}
if len(layer_ids)!=len(set(layer_ids)): errors.append('duplicate layer id')
required_stage_fields=('id','order','status','seedDomain','deterministic','inputs','outputs','mayMutate','mustNotMutate','preview','runtimeRegeneration','persistenceInteraction','validator')
ids=[]; orders=[]; seeds=[]
for s in stages:
    for f in required_stage_fields:
        if f not in s: errors.append(f"{s.get('id','?')}: missing {f}")
    ids.append(s.get('id')); orders.append(s.get('order')); seeds.append(s.get('seedDomain'))
    if s.get('deterministic') and not s.get('seedDomain'): errors.append(f"{s.get('id')}: deterministic without seed domain")
    if not s.get('outputs') or not s.get('mayMutate'): errors.append(f"{s.get('id')}: outputs/mutation rights required")
    unknown=set(s.get('outputs',[])+s.get('mayMutate',[]))-set(layer_ids)
    if unknown: errors.append(f"{s.get('id')}: unknown layers {sorted(unknown)}")
    overlap=set(s.get('mayMutate',[])) & set(s.get('mustNotMutate',[]))
    if overlap: errors.append(f"{s.get('id')}: contradictory mutation rights {sorted(overlap)}")
    for out in s.get('outputs',[]):
        if owners.get(out)!=s.get('id'): errors.append(f"{s.get('id')}: does not own output layer {out}")
    if 'player_deltas' not in s.get('mustNotMutate',[]) and s.get('id')!='validate_and_bake_chunk_baseline': errors.append(f"{s.get('id')}: must protect player_deltas")
if len(ids)!=len(set(ids)): errors.append('duplicate stage id')
if len(orders)!=len(set(orders)): errors.append('duplicate stage order')
if sorted(orders)!=list(range(1,len(stages)+1)): errors.append('stage order must be contiguous and append-only')
if len(seeds)!=len(set(seeds)): errors.append('seed domains must be unique')
expected=['world_topology','archipelago_skeleton','ocean_depth_bands','macro_biomes','geological_form','rivers_and_watersheds','shore_normalization','roads_settlements_anchors','local_terrain_materialization','props_and_ecology','structures','validate_and_bake_chunk_baseline']
if ids!=expected: errors.append('authoritative world-generation order drifted')
active={s['id'] for s in stages if s.get('status')=='active'}
for req in ('world_topology','archipelago_skeleton','ocean_depth_bands','macro_biomes','shore_normalization','roads_settlements_anchors','local_terrain_materialization','validate_and_bake_chunk_baseline'):
    if req not in active: errors.append(f'{req}: must remain active')
if 'pub mod world_generation_pipeline;' not in LIB.read_text(encoding='utf-8'): errors.append('haven_world does not export pipeline module')
text=MOD.read_text(encoding='utf-8') if MOD.exists() else ''
for token in ('WORLD_GENERATION_PIPELINE_SCHEMA','undeclared_mutation','must_not_mutate','persistence_interaction','pub fn validate'):
    if token not in text: errors.append(f'Rust pipeline module missing {token}')
tasks={t.get('id'):t for t in vm.get('tasks',[])}
t=tasks.get('validate-worldgenerationpipelineownershipv143')
if not t or not t.get('enabled') or not t.get('required') or t.get('lifecycle')!='active': errors.append('Pass 143 validator not actively registered')
for s in stages:
    if s.get('validator') not in tasks: errors.append(f"{s.get('id')}: validator id {s.get('validator')} not in validation manifest")
if errors:
    print('Pass 143 world-generation pipeline ownership validation FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print(f'Pass 143 world-generation pipeline ownership validated: {len(stages)} ordered stages, {len(layers)} owned layers, mutation and persistence contracts clean')
