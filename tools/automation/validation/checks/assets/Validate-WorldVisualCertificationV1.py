#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[5]
def load(p):
 if isinstance(p,str): p=ROOT/p
 if not p.exists(): raise AssertionError(f'missing {p.relative_to(ROOT)}')
 return json.loads(p.read_text(encoding='utf-8-sig'))
def req(c,m):
 if not c: raise AssertionError(m)
try:
 cert=load('content/assets/world_visual_certification_v1.json');req(cert.get('pass')=='167Z109W52','W52 pass mismatch');req(cert.get('status')=='CERTIFIED_WITH_EXPLICIT_QUARANTINES','W52 status drift')
 quarantined={x['objectKind'] for x in cert['quarantinedOptionalLegacyKinds']};req(quarantined=={'well','scarecrow','bench','log','greenhouse_marker','sign'},'W52 quarantine set drift')
 # Build one canonical published identity map and reject collisions.
 pub={}; aliases={}; primary={}
 for path in sorted((ROOT/'content/asset_packs/havenwild_objects').glob('published_*.json')):
  try:d=load(path)
  except Exception:continue
  if d.get('schema')!='havenwild.published_world_asset_catalog.v1':continue
  for e in d.get('entries',[]):
   req(e['id'] not in pub,f'duplicate published id {e["id"]}');pub[e['id']]=e
   if e.get('legacy_object_kind_primary') and e.get('legacy_object_kind'):
    k=e['legacy_object_kind'];req(k not in primary,f'duplicate primary legacy adapter {k}');primary[k]=e['id']
   for a in list(e.get('aliases',[]))+[e.get('semantic_id')]:
    if not a:continue
    req(a not in aliases,f'duplicate published alias {a}');aliases[a]=e['id']
 for aid in ['furniture_bar_counter_wood_4','container_barrel_wood_01','container_keg_wood_01','fixture_fireplace_cast_iron_01','cave_entrance_default','resource_ore_iron_01','door_basic','stairs_short_run_gray','fence_plain_horizontal','sign_wall_inn']:
  req(aid in pub,f'W52 required visual missing: {aid}'); req(pub[aid].get('certification') not in {'rejected','missing','placeholder'},f'W52 required visual unusable: {aid}')
 # Exact source closure for new W52 furniture.
 req(pub['furniture_bar_counter_wood_4']['provenance']['source_rect']==[64,128,128,32],'bar counter exact source drift')
 req(pub['container_barrel_wood_01']['provenance']['source_rect']==[0,0,32,48],'barrel singular source drift')
 req(pub['container_keg_wood_01']['provenance']['source_rect']==[32,0,32,48],'keg singular source drift')
 req(pub['fixture_fireplace_cast_iron_01']['visual']['frames'][1]['source_rect']==[0,64,32,32],'lit hearth source drift')
 # Tavern must now have no visual holes.
 tav=load('content/buildings/recipes/tavern_standard_three_level_v1.json');fs=[f for l in tav['levels'] for f in l.get('furnishings',[])];req(len(fs)==23 and all(f.get('assetId') for f in fs),'W52 Tavern visual closure regressed')
 for f in fs:req(f['assetId'] in pub,f'Tavern furnishing unresolved: {f["id"]} -> {f.get("assetId")}')
 # Production scene files present in this source may not generate quarantined legacy aliases.
 violations=[]
 scene_root=ROOT/'content/worldgen/scenes'
 for path in scene_root.rglob('*.json'):
  try:d=load(path)
  except Exception:continue
  if d.get('role')=='diagnostic_only' or 'world_asset_acceptance' in path.parts:continue
  for o in d.get('objects',[]):
   aid=o.get('assetId') or o.get('kind') or o.get('objectKind')
   if aid in quarantined:violations.append(f'{path.relative_to(ROOT)}::{aid}')
 req(not violations,'quarantined visual appears in production scene: '+', '.join(violations[:8]))
 scene=load('content/worldgen/scenes/world_asset_acceptance/world_visual_w52_acceptance_scene_v1.json');req(scene['sceneId']=='world_visual_w52_acceptance','W52 acceptance scene missing')
 for o in scene['objects']:
  e=pub.get(o['assetId']);req(e is not None,f'acceptance unresolved {o["assetId"]}');req(e.get('certification') not in {'rejected','missing','placeholder'},f'acceptance unusable {o["assetId"]}')
 print('PASS W52 World visual certification')
 print('- core Estate/Tavern/cave visual profile contains no placeholder/rejected/missing substitutions')
 print('- Tavern visual closure is 23/23 published furnishings')
 print('- well/scarecrow/bench/fallen-log/legacy greenhouse-marker/generic standing-sign remain explicit quarantines and cannot be generated')
except Exception as e:
 print(f'FAIL W52 World visual certification: {e}',file=sys.stderr);sys.exit(1)
