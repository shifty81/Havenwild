#!/usr/bin/env python3
from pathlib import Path
from collections import deque
import json, sys

ROOT=Path(__file__).resolve().parents[5]
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def req(ok,msg):
    if not ok: raise AssertionError(msg)

def reachable(scene,start):
    terrain=scene['layers']['terrain']; w,h=scene['sceneSize']; blocked=set()
    for o in scene.get('objects',[]):
        if not o.get('blocksMovement'): continue
        x,y,ow,oh=o.get('collisionRect',[0,0,0,0])
        for yy in range(y,y+oh):
            for xx in range(x,x+ow): blocked.add((xx,yy))
    blocked.discard((78,8))
    q=deque([tuple(start)]); seen={tuple(start)}
    while q:
        x,y=q.popleft()
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if not (0<=nx<w and 0<=ny<h) or (nx,ny) in seen or (nx,ny) in blocked: continue
            if terrain[ny][nx] == 'MountainRock': continue
            seen.add((nx,ny)); q.append((nx,ny))
    return seen

try:
    scene=load('content/worldgen/scenes/home_island/farmstead_scene_v0_3.json')
    profile=load('content/estates/estate_generation_profile_v1.json')
    contract=load('content/estates/home_estate_contract_v1.json')
    req(scene.get('version') in {'0.5.0-w53e','0.6.0-w54a','0.7.0-w54b','0.8.0-w54f','0.9.0-w56h'},'Estate scene no longer carries W53E composition lineage')
    comp=scene['estate']['composition']; req(comp['profile']=='w53e_edge_woodland_clear_center','Estate composition profile drifted')
    req(profile.get('pass') in {'167Z109W53E','167Z109W54A','167Z109W54B','167Z109W54E','167Z109W54F','167Z109W57K8'} and contract.get('pass') in {'167Z109W53E','167Z109W54A','167Z109W54B','167Z109W54E','167Z109W54F'},'Estate profile/contract lost W53E-or-later composition lineage')
    objects=scene.get('objects',[])
    ids=[o['id'] for o in objects]
    counts={
      'trees':sum(i.startswith('estate_tree_') for i in ids),
      'shrubs':sum(i.startswith('estate_shrub_') for i in ids),
      'boulders':sum(i.startswith('estate_boulder_') for i in ids),
      'forage':sum(i.startswith('estate_forage_') for i in ids),
    }
    req(counts['trees']>=28,'Estate still too sparse: expected at least 28 trees')
    req(counts['shrubs']>=8 and counts['boulders']>=8 and counts['forage']>=12,'Estate secondary ground population is below W53E baseline')
    req(comp['treeCount']==counts['trees'] and comp['shrubCount']==counts['shrubs'] and comp['boulderCount']==counts['boulders'] and comp['forageCount']==counts['forage'],'Estate composition metadata/counts disagree')
    # No blocking object may occupy the reserved center/home pad.
    bx,by,bw,bh=comp['centralBuildPad']
    for o in objects:
        if not o.get('blocksMovement') or o['id']=='estate_cave_mouth': continue
        x,y,w,h=o.get('collisionRect',[0,0,0,0])
        overlap=not (x+w<=bx or bx+bw<=x or y+h<=by or by+bh<=y)
        req(not overlap, f"blocking Estate object intrudes into reserved central build pad: {o['id']}")
    spawn=next(s['tile'] for s in scene['spawns'] if s['id']=='player_default')
    seen=reachable(scene,spawn)
    for label,p in {'south gate':(48,62),'home approach':(59,36),'cave threshold':(78,9),'garden spur':(29,39)}.items():
        req(p in seen,f'W53E critical route is blocked: {label} {p}')
    terrain=scene['layers']['terrain']
    # Route has no accidental raised/rock interruption between its anchor points.
    for point in [(48,55),(53,50),(55,43),(59,36),(64,31),(68,25),(73,19),(77,13)]:
        x,y=point; req(terrain[y][x]=='StonePath',f'W53E route anchor lost path surface at {point}')
    cave_surface = 'Dirt' if profile.get('pass') in {'167Z109W54F','167Z109W57K8'} else 'StonePath'
    req(terrain[9][78] == cave_surface, 'W53E-or-later cave threshold approach surface drifted')
    req(contract.get('compositionPolicy',{}).get('centralBuildPadReserved') is True,'Estate contract missing central build-pad policy')
    print('PASS W53E Estate composition authority')
    print(f"- published population: {counts['trees']} trees / {counts['shrubs']} shrubs / {counts['boulders']} boulders / {counts['forage']} forage")
    print('- edge woodland and secondary object clusters frame the property without occupying the central build pad')
    print('- south gate, home approach, garden spur and 1x2 cave threshold remain reachable')
except Exception as exc:
    print(f'FAIL W53E Estate composition authority: {exc}',file=sys.stderr); sys.exit(1)
