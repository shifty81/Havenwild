#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'content/worldgen/scenes/world_asset_acceptance/structural_connector_acceptance_scene_v1.json'
W,H=64,40
terrain=[['grass' for _ in range(W)] for _ in range(H)]
# Cave lane.
for y in range(6,18):
 for x in range(4,18): terrain[y][x]='cave_wall'
for y in range(10,17):
 for x in range(7,15): terrain[y][x]='cave_floor'
# Bridge lane over existing water authority.
for y in range(10,16):
 for x in range(34,55): terrain[y][x]='deep_water'
for y in range(10,16):
 for x in list(range(30,34))+list(range(55,59)): terrain[y][x]='grass'
objects=[
 {'id':'w51_cave_mouth','assetId':'cave_entrance_default','acceptanceLane':'w51_connectors','acceptanceStatus':'CANDIDATE','visualRect':[8,8,1,3],'collisionRect':[8,10,0,0],'layer':'high_object','blocksMovement':False,'occludesPlayer':True,'fadeWhenPlayerBehind':True,'interactions':[{'id':'inspect_cave_mouth','kind':'inspect','rect':[8,10,1,1]}]},
 {'id':'w51_stair_run','assetId':'stairs_short_run_gray','acceptanceLane':'w51_connectors','acceptanceStatus':'CANDIDATE','visualRect':[24,8,1,5],'collisionRect':[24,12,0,0],'layer':'high_object','blocksMovement':False,'occludesPlayer':False,'fadeWhenPlayerBehind':False,'interactions':[{'id':'inspect_stairs','kind':'inspect','rect':[24,12,1,1]}]},
 {'id':'w51_bridge_flat','assetId':'bridge_wood_oak_flat_module','acceptanceLane':'w51_connectors','acceptanceStatus':'CANDIDATE','visualRect':[39,10,4,3],'collisionRect':[41,12,0,0],'layer':'low_object','blocksMovement':False,'occludesPlayer':False,'fadeWhenPlayerBehind':False,'interactions':[{'id':'inspect_bridge_flat','kind':'inspect','rect':[41,12,1,1]}]},
 {'id':'w51_bridge_arch','assetId':'bridge_wood_oak_arch_module','acceptanceLane':'w51_connectors','acceptanceStatus':'CANDIDATE','visualRect':[47,10,3,3],'collisionRect':[48,12,0,0],'layer':'low_object','blocksMovement':False,'occludesPlayer':False,'fadeWhenPlayerBehind':False,'interactions':[{'id':'inspect_bridge_arch','kind':'inspect','rect':[48,12,1,1]}]}
]
scene={'id':'structural_connector_acceptance_scene_v1','version':'1.0.0-w51','kind':'worldgen_scene','sceneId':'structural_connector_acceptance','title':'W51 Structural Connector Acceptance','sceneKind':'exterior','biome':'temperate','role':'diagnostic_only','sceneSize':[W,H],'tileSize':32,'edgePolicy':'bounded','layers':{'terrain':terrain},'objects':objects,'transitions':[],'spawns':[{'id':'player_default','tile':[20,20]}],'editor':{'notes':['Compare exact cave mouth, short stair run and wood bridge modules under one connector semantic lane.','Cave-depth transition remains logical/deferred until exact source evidence exists.']},'acceptance':{'pass':'167Z109W51','profileCount':6,'visibleExactCandidateCount':4,'logicalDeferredCount':1},'validationRules':['connector visuals resolve through PublishedWorldAssetRegistry','BuildingRecipe remains building-connector placement authority','scene/worldgen remains cave-portal placement authority','same-instance stairs do not change SceneMap','continuous-surface bridge does not create a scene teleport']}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(scene,indent=2)+'\n');print(f'WROTE {OUT.relative_to(ROOT)}')
