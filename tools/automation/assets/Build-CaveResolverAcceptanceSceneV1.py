#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'content/worldgen/scenes/world_asset_acceptance/cave_w50_acceptance_scene_v1.json'
W,H=64,48
terrain=[['cave_wall' for _ in range(W)] for _ in range(H)]

def room(x0,y0,x1,y1,t='cave_floor'):
 for y in range(y0,y1+1):
  for x in range(x0,x1+1): terrain[y][x]=t

def corridor(a,b,width=3):
 x,y=a; tx,ty=b; half=(max(width,1)-1)//2
 sx=1 if tx>=x else -1
 while x!=tx:
  for oy in range(-half,half+1): terrain[y+oy][x]='cave_floor'
  x+=sx
 sy=1 if ty>=y else -1
 while y!=ty:
  for ox in range(-half,half+1): terrain[y][x+ox]='cave_floor'
  y+=sy
 for oy in range(-half,half+1):
  for ox in range(-half,half+1): terrain[ty+oy][tx+ox]='cave_floor'

room(5,34,13,42); room(18,23,31,34); room(39,15,54,27); room(36,34,52,42)
corridor((11,37),(20,29),3); corridor((29,27),(41,21),3); corridor((29,32),(39,37),3)
room(7,37,10,40)
for y in (38,39):
 for x in (45,46): terrain[y][x]='shallow_water'

objects=[
 {'id':'w50_exact_cave_mouth','assetId':'cave_entrance_default','acceptanceLane':'w50_cave_resolver','acceptanceStatus':'CANDIDATE','visualRect':[8,35,1,3],'collisionRect':[8,37,0,0],'layer':'high_object','blocksMovement':False,'occludesPlayer':True,'fadeWhenPlayerBehind':True,'interactions':[{'id':'enter_cave','kind':'enter_scene','rect':[8,37,1,1]}]},
 {'id':'w50_iron_ore_a','assetId':'resource_ore_iron_01','acceptanceLane':'w50_cave_resolver','acceptanceStatus':'CANDIDATE','visualRect':[18,25,5,6],'collisionRect':[18,29,1,1],'layer':'low_object','blocksMovement':True,'occludesPlayer':False,'fadeWhenPlayerBehind':False,'interactions':[{'id':'mine_iron_a','kind':'inspect','rect':[17,28,3,3]}]},
 {'id':'w50_iron_ore_b','assetId':'resource_ore_iron_01','acceptanceLane':'w50_cave_resolver','acceptanceStatus':'CANDIDATE','visualRect':[39,17,5,6],'collisionRect':[39,21,1,1],'layer':'low_object','blocksMovement':True,'occludesPlayer':False,'fadeWhenPlayerBehind':False,'interactions':[{'id':'mine_iron_b','kind':'inspect','rect':[38,20,3,3]}]}
]
scene={
 'id':'cave_w50_acceptance_scene_v1','version':'1.0.0-w50','kind':'worldgen_scene','sceneId':'cave_w50_acceptance','title':'W50 Cave Resolver + PCG Acceptance','sceneKind':'cave','biome':'cave','role':'diagnostic_only','sceneSize':[W,H],'tileSize':32,'edgePolicy':'bounded',
 'layers':{'terrain':terrain},'objects':objects,'transitions':[],'spawns':[{'id':'player_default','tile':[10,39]}],
 'editor':{'notes':['Diagnostic-only deterministic room/corridor cave topology.','Cave wall tiles are occupancy/fill authority only; unresolved vertical cave-face artwork must remain fail-closed.','Objects exercise exact W49 cave-mouth and iron-ore PublishedWorldAsset identities.']},
 'acceptance':{'pass':'167Z109W50','resolver':'deterministic_room_corridor_hybrid','criticalPathGuaranteed':True,'wallAdjacentOreRequired':True,'exactCaveMouthAssetId':'cave_entrance_default','exactIronOreAssetId':'resource_ore_iron_01','verticalCaveFaceStatus':'deferred_exact_source'},
 'validationRules':['required rooms and connector landings are connected before optional detail','ore nodes occupy CaveFloor adjacent to CaveWall','unproven cave wall faces and ore material variants remain deferred','diagnostic scene does not become production cave layout authority']
}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(scene,indent=2)+'\n')
print(f'WROTE {OUT.relative_to(ROOT)}')
