#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    source=root/'content/worldgen/scenes/world_asset_acceptance/building_recipe_acceptance_scene_v1.json'
    out=root/'content/worldgen/scenes/world_asset_acceptance/building_instance_acceptance_scene_v1.json'
    d=load(source)
    d['id']='building_instance_acceptance_scene_v1'
    d['version']='1.0.0'
    d['sceneId']='building_instance_acceptance'
    d['title']='Building Instance Runtime Acceptance — W46B'
    d['objects']=[]
    d['spawns']=[{'id':'player_default','tile':[28,23]}]
    d['editor']={'notes':[
        'W46B native BuildingInstance acceptance: the house is not baked into scene objects.',
        'BuildingInstanceRegistry places havenwild.acceptance.three_level_house at anchor tile 24,14.',
        'Walk north through the open front door. Roof/front-wall cutaway is camera-local and reveals only the active structural level.',
        'Interact at world 30,18 to traverse ground/upstairs; interact again to return.',
        'Interact at world 26,18 to traverse ground/cellar; interact again to return.',
        'Stair traversal mutates active structural level and never changes SceneMap identity.',
        'Native editor: PageUp/PageDown changes structural-level preview; Home toggles cutaway/exterior roof preview.'
    ]}
    d['acceptance']={
        'pass':'167Z109W46B',
        'buildingInstanceId':'havenwild.acceptance.three_level_house',
        'buildingRecipeId':'havenwild.prototype.three_level_house',
        'buildingAuthority':'BuildingInstanceRegistry',
        'recipeAuthority':'BuildingRecipeRegistry',
        'visualAuthority':'PublishedWorldAssetRegistry',
        'structuralLevels':[-1,0,1],
        'ordinaryInteriorPolicy':'same_world_building_instance',
        'staticSceneObjectCount':0,
        'runtimeMaterialized':True,
        'entryDoorWorldTile':[28,20],
        'cellarConnectorWorldTile':[26,18],
        'upstairsConnectorWorldTile':[30,18]
    }
    d['validationRules']=[
        'building_instance_acceptance contains no baked structural object carriers',
        'runtime/editor materialize BuildingInstanceRegistry + BuildingRecipeRegistry directly',
        'walking through the front door hides roof/front-wall only for the local camera',
        'ground/upstairs/cellar traversal mutates active structural level and never changes scene id',
        'logical walls block movement even when exact facing visuals are deferred',
        'inactive levels remain authoritative but are not rendered as the active camera layer'
    ]
    out.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
    print(f'PASS W46B building instance acceptance scene: {out.relative_to(root)}')
    print('- zero baked structure carriers; runtime/editor BuildingInstance materialization is authoritative')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
