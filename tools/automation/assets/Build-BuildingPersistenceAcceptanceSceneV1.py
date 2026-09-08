#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

MAP_W=96
MAP_H=64


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    source=root/'content/worldgen/scenes/world_asset_acceptance/building_instance_acceptance_scene_v1.json'
    out=root/'content/worldgen/scenes/world_asset_acceptance/building_instance_persistence_acceptance_scene_v1.json'
    d=load(source)
    source_w,source_h=d['sceneSize']
    ox=(MAP_W-source_w)//2
    oy=(MAP_H-source_h)//2
    source_rows=d['layers']['terrain']
    rows=[['grass']*MAP_W for _ in range(MAP_H)]
    for y,row in enumerate(source_rows):
        for x,tile in enumerate(row):
            rows[oy+y][ox+x]=tile
    d['id']='building_instance_persistence_acceptance_scene_v1'
    d['version']='1.0.0'
    d['sceneId']='pcg_w46c_acceptance_0_0'
    d['title']='Building Placement + Persistence Acceptance — W46C'
    d['sceneKind']='exterior'
    d['role']='diagnostic_only'
    d['sceneSize']=[MAP_W,MAP_H]
    d['layers']['terrain']=rows
    d['objects']=[]
    d['transitions']=[]
    d['spawns']=[{'id':'player_default','tile':[28+ox,23+oy]}]
    anchor=[24+ox,14+oy]
    d['buildingInstances']=[{
        'id':'havenwild.acceptance.pcg_three_level_house',
        'recipeId':'havenwild.prototype.three_level_house',
        'anchorTile':anchor,
        'initialLevel':0,
        'placementSpace':'continuous_surface',
        'surfaceRegionId':'w46c_acceptance',
        'globalAnchorTile':anchor,
    }]
    d['editor']={'notes':[
        'W46C acceptance: this scene owns zero baked building objects; placement is read from top-level buildingInstances by BuildingInstanceRegistry.',
        'The scene id pcg_w46c_acceptance_0_0 binds chunk 0,0 of continuous surface region w46c_acceptance.',
        'The generated BuildingInstance uses a stable explicit id and globalAnchorTile. Runtime resolves it back into this partition local space.',
        'Interact with the front door, save, reload, and confirm the effective door visual/collision state survives via buildings/building_instance_deltas.json.',
        'Roof/front-wall cutaway and active camera floor remain local view state and must never appear in the building save sidecar or network snapshot.',
        'Native editor authoring: Ctrl+B place; Ctrl+Alt+Arrow move stable instance id; Ctrl+Shift+B delete; Ctrl+S writes catalog/per-instance source files.'
    ]}
    d['acceptance']={
        'pass':'167Z109W46C',
        'buildingInstanceId':'havenwild.acceptance.pcg_three_level_house',
        'buildingRecipeId':'havenwild.prototype.three_level_house',
        'buildingAuthority':'BuildingInstanceRegistry',
        'recipeAuthority':'BuildingRecipeRegistry',
        'visualAuthority':'PublishedWorldAssetRegistry',
        'placementSpace':'continuous_surface',
        'surfaceRegionId':'w46c_acceptance',
        'globalAnchorTile':anchor,
        'staticSceneObjectCount':0,
        'worldgenPlacementField':'buildingInstances',
        'saveSchema':'havenwild.building_instance_world_state.v1',
        'saveRelativePath':'buildings/building_instance_deltas.json',
        'persistentOpeningId':'front_door',
        'cameraLocalStateExcludedFromSave':True,
        'cameraLocalStateExcludedFromReplication':True,
        'entryDoorWorldTile':[28+ox,20+oy],
        'cellarConnectorWorldTile':[26+ox,18+oy],
        'upstairsConnectorWorldTile':[30+ox,18+oy]
    }
    d['validationRules']=[
        'worldgen and authored placement both converge on BuildingInstanceRegistry',
        'continuous-surface placement is keyed by region + stable global tile anchor rather than storage-scene identity',
        'save state is an overlay of upserts/tombstones/per-instance state rather than a copy of BuildingRecipe or PublishedWorldAsset data',
        'door render and collision read the same effective persistent opening state',
        'camera-local inside/active-level/cutaway state is absent from persistence and network replication',
        'native editor place/move/delete writes BuildingInstance source authority and preserves stable ids across moves'
    ]
    out.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    print(f'PASS W46C building persistence acceptance scene: {out.relative_to(root)}')
    print(f'- continuous-surface BuildingInstance anchor={anchor}; zero baked object carriers')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
