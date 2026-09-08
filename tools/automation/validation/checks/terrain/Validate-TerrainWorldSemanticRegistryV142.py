#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[5]
REG=ROOT/'content/worldgen/terrain_world_semantic_registry_v1.json'
LEGACY=ROOT/'content/assets/terrain_material_registry_v0_1.json'
TILES=ROOT/'crates/haven_core/src/foundation/tile_object_catalog.rs'
BIOMES=ROOT/'content/worldgen/biome_registry_v0_1.json'
LOOKUP=ROOT/'content/worldgen/worldgen_asset_lookup_v0_4.json'
MANIFEST=ROOT/'content/validation/validation_manifest_v1.json'
errors=[]
def load(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: errors.append(f'{p}: {e}'); return {}
r=load(REG); legacy=load(LEGACY); biome=load(BIOMES); lookup=load(LOOKUP); vm=load(MANIFEST)
if r.get('schema')!='havenwild.terrain_world_semantic_registry.v1': errors.append('wrong semantic registry schema')
materials=r.get('materials',[])
for field in ('id','code','stableOrdinal','label','tileKind','runtimeMaterial','category','editor','ownership','runtime','transition','biomes','source','status','deprecatedAliases'):
    for m in materials:
        if field not in m: errors.append(f"{m.get('code','?')}: missing {field}")
for key in ('id','code','stableOrdinal','tileKind'):
    vals=[m.get(key) for m in materials]
    if len(vals)!=len(set(vals)): errors.append(f'duplicate {key}')
ordinals=sorted(m['stableOrdinal'] for m in materials)
if ordinals != list(range(1,len(materials)+1)): errors.append('stableOrdinal values must be contiguous and append-only')
legacy_codes={m['code'] for m in legacy.get('materials',[])}
new_codes={m['code'] for m in materials}
if legacy_codes != new_codes: errors.append(f'legacy/new registry code mismatch missing={sorted(legacy_codes-new_codes)} extra={sorted(new_codes-legacy_codes)}')
source=TILES.read_text(encoding='utf-8')
for m in materials:
    if not re.search(r'\b'+re.escape(m['tileKind'])+r'\b',source): errors.append(f"{m['code']}: TileKind {m['tileKind']} not found")
    life=m['ownership'].get('lifecycle'); regen=m['ownership'].get('regenerationPolicy'); mode=m['editor'].get('paintMode')
    if life=='generated' and regen!='recompute': errors.append(f"{m['code']}: generated must recompute")
    if mode=='generated' and life!='generated': errors.append(f"{m['code']}: generated paint mode requires generated lifecycle")
    if m['runtime'].get('waterDepthClass') and m['runtime'].get('terrainRole') not in ('water','shore'): errors.append(f"{m['code']}: water depth on non-water/shore role")
# All biome terrain references must resolve.
refs=set()
def walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ('requiredTerrain','generatedTerrain','base_tiles','shore_tiles') and isinstance(v,list): refs.update(z for z in v if isinstance(z,str))
            walk(v)
    elif isinstance(x,list):
        for v in x: walk(v)
walk(biome); walk(load(ROOT/'content/worldgen/biome_presets.json'))
aliases={a for m in materials for a in m.get('deprecatedAliases',[])}
unknown=sorted(refs-new_codes-aliases)
if unknown: errors.append(f'biome terrain references missing from registry: {unknown}')
# Production/direct semantics must have an asset lookup entry unless deferred/gameplay state.
asset_map={}
for v in lookup.values():
    if isinstance(v,dict) and 'grass' in v: asset_map=v; break
for m in materials:
    if m['editor']['paintMode']=='direct' and m['status']!='deferred' and m['code'] not in asset_map:
        errors.append(f"{m['code']}: direct terrain missing worldgen asset lookup")
# Registry task must be active and required.
tasks={t.get('id'):t for t in vm.get('tasks',[])}
t=tasks.get('validate-terrainworldsemanticregistryv142')
if not t or not t.get('enabled') or not t.get('required') or t.get('lifecycle')!='active': errors.append('Pass 142 validator not actively registered')
if errors:
    print('Pass 142 terrain/world semantic registry validation FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print(f'Pass 142 terrain/world semantic registry validated: {len(materials)} materials, {len(refs)} biome references, stable ids/ordinals clean')
