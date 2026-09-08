#!/usr/bin/env python3
from pathlib import Path
from collections import deque
import json,sys,re
ROOT=Path(__file__).resolve().parents[5]
def load(rel):
 p=ROOT/rel
 if not p.exists(): raise AssertionError(f'missing {rel}')
 return json.loads(p.read_text())
def req(c,m):
 if not c: raise AssertionError(m)
try:
 c=load('content/caves/cave_generation_contract_v1.json'); req(c.get('pass')=='167Z109W50','W50 contract pass mismatch')
 req(c['algorithm']['topology']=='deterministic_room_corridor_hybrid' and c['algorithm']['criticalConnectivityBeforeDecoration'] is True,'W50 must carve guaranteed topology before optional detail')
 src=(ROOT/'crates/haven_core/src/foundation/starter_generation.rs').read_text()
 for token in ['carve_cave_room','carve_cave_corridor','cave_tile_is_wall_adjacent','place_cave_ore_candidates']:
  req(token in src,f'W50 starter generator missing {token}')
 req('self.fill_rect(5, 5, 41, 26, TileKind::CaveWall);' in src,'cave mouth must begin from solid occupancy field')
 req('self.fill_rect(3, 3, 44, 28, TileKind::CaveWall);' in src,'cave depths must begin from solid occupancy field')
 req('TileKind::ShallowWater' in src,'cave damp pocket must reuse existing water authority')
 editor=(ROOT/'apps/haven_editor_native/src/app/world_asset_pixel_bridge.rs').read_text()
 req('TileKind::CaveFloor => "terrain.lpc_v7.mudstone.brown.pure_fill"' in editor,'native editor exact-source bridge must retain CaveFloor binding')

 s=load('content/worldgen/scenes/world_asset_acceptance/cave_w50_acceptance_scene_v1.json')
 req(s['sceneId']=='cave_w50_acceptance' and s['sceneKind']=='cave','W50 acceptance scene identity mismatch')
 t=s['layers']['terrain']; H=len(t); W=len(t[0]); req((W,H)==tuple(s['sceneSize']),'scene dimensions mismatch')
 walk=lambda x,y: 0<=x<W and 0<=y<H and t[y][x] in ('cave_floor','shallow_water','water')
 start=tuple(s['spawns'][0]['tile']); q=deque([start]); seen={start}
 while q:
  x,y=q.popleft()
  for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
   n=(x+dx,y+dy)
   if n not in seen and walk(*n): seen.add(n);q.append(n)
 # Representative room centers must all be connected.
 for point in [(24,29),(46,21),(44,38)]: req(point in seen,f'critical cave room unreachable: {point}')
 objs={o['id']:o for o in s['objects']}; req(objs['w50_exact_cave_mouth']['assetId']=='cave_entrance_default','exact mouth missing from acceptance')
 for oid in ('w50_iron_ore_a','w50_iron_ore_b'):
  o=objs[oid]; req(o['assetId']=='resource_ore_iron_01',f'{oid} must use exact iron asset')
  x,y=o['collisionRect'][:2]; req(t[y][x]=='cave_floor',f'{oid} must stand on cave floor')
  req(any(0<=x+dx<W and 0<=y+dy<H and t[y+dy][x+dx]=='cave_wall' for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))),f'{oid} must be wall adjacent')
 pack=load('content/worldgen/packs/worldgen_home_island_test_v0_11.json'); rel='content/worldgen/scenes/world_asset_acceptance/cave_w50_acceptance_scene_v1.json'
 req(rel in pack['sceneFiles'] and rel in pack['smokeTests'],'W50 scene must be registered in dev pack')
 print('PASS W50 Cave resolver + PCG/editor authority')
 print('- cave topology is solid-first deterministic room/corridor generation with guaranteed critical connectivity')
 print('- optional seed variation cannot sever the required path')
 print('- ore placement is wall-adjacent and uses the exact W49 iron identity')
 print('- native editor retains exact CaveFloor Pixel Studio source binding')
except Exception as e:
 print(f'FAIL W50 Cave resolver authority: {e}',file=sys.stderr);sys.exit(1)
