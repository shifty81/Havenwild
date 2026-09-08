#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'content/worldgen/scenes/world_asset_acceptance/cliff_height_w53d_acceptance_scene_v1.json'
W,H=48,32

def main():
    terrain=[['Grass']*W for _ in range(H)]
    zones=[['none']*W for _ in range(H)]
    levels=[[0]*W for _ in range(H)]
    # Four independent plateau strips. Their south edges exercise exact 1/2/3/4 drops.
    for level,x0,x1 in [(1,3,10),(2,13,20),(3,23,30),(4,33,40)]:
        for y in range(4,13):
            for x in range(x0,x1+1):
                levels[y][x]=level
                terrain[y][x]='MountainRock'
    # Stair-step south corners on each plateau force diagonal/terminal topology without
    # changing the vertical module count.
    for level,x0,x1 in [(1,3,10),(2,13,20),(3,23,30),(4,33,40)]:
        levels[13][x0]=level; terrain[13][x0]='MountainRock'
        levels[13][x1]=level; terrain[13][x1]='MountainRock'
    # Mixed edge proof: Level 2 host sees Level 1 to west and Level 0 south/east.
    for y in range(18,23):
        for x in range(14,20):
            levels[y][x]=2; terrain[y][x]='MountainRock'
    for y in range(18,23):
        for x in range(11,14):
            levels[y][x]=1; terrain[y][x]='MountainRock'
    # Exact ordinary cave: one tile wide, two levels tall, threshold is the Level 0 row below.
    cave_x,cave_y=17,22
    levels[cave_y][cave_x]=2; terrain[cave_y][cave_x]='MountainRock'
    levels[cave_y+1][cave_x]=0; terrain[cave_y+1][cave_x]='StonePath'
    cave_obj={
      'id':'w53d_cave_mouth','assetId':'cave_entrance_default',
      'visualRect':[cave_x,cave_y-2,1,3],
      'collisionRect':[cave_x,cave_y,1,1],
      'layer':'tall_object','blocksMovement':True,'occludesPlayer':False,
      'fadeWhenPlayerBehind':False,'state':'open',
      'interactions':[{'id':'enter_w53d_cave','kind':'enter','rect':[cave_x,cave_y+1,1,1]}]
    }
    scene={
      'id':'cliff_height_w53d_acceptance_scene_v1','version':'1.0.0-w53d','kind':'worldgen_scene',
      'sceneId':'cliff_height_w53d_acceptance','title':'W53D Cliff Height Acceptance',
      'sceneKind':'exterior','biome':'temperate','role':'development_acceptance','sceneSize':[W,H],
      'tileSize':[32,32],
      'layers':{'terrain':terrain,'structuralLevels':levels,'zones':zones},
      'objects':[cave_obj],'transitions':[],
      'spawns':[{'id':'player_default','tile':[24,27]}],
      'editor':{'showLayers':['terrain','structural_levels','objects','collision'],'defaultTool':'inspect_select','legacyReferenceOnly':False},
      'acceptance':{
        'contract':'content/terrain/cliff_height_runtime_contract_v1.json',
        'dropColumns':[
          {'label':'Level 1','hostLevel':1,'receiverLevel':0,'southHostRange':[3,10,12]},
          {'label':'Level 2','hostLevel':2,'receiverLevel':0,'southHostRange':[13,20,12]},
          {'label':'Level 3','hostLevel':3,'receiverLevel':0,'southHostRange':[23,30,12]},
          {'label':'Level 4','hostLevel':4,'receiverLevel':0,'southHostRange':[33,40,12]}
        ],
        'mixedEdgeHost':[14,22],
        'caveHost':[cave_x,cave_y],
        'caveThreshold':[cave_x,cave_y+1],
        'caveApertureTiles':[1,2]
      }
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    print(f'WROTE {OUT.relative_to(ROOT)}')
if __name__=='__main__': main()
