#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "content/worldgen/scenes/world_asset_acceptance/tavern_building_acceptance_scene_v1.json"
W, H = 96, 64

def main() -> int:
    terrain = [["grass" for _ in range(W)] for _ in range(H)]
    scene = {
        "id": "tavern_building_acceptance_scene_v1",
        "version": "1.1.0-w52",
        "kind": "worldgen_scene",
        "sceneId": "tavern_building_acceptance",
        "title": "W52 Production Tavern Visual-Closure Acceptance",
        "sceneKind": "exterior",
        "biome": "temperate",
        "role": "diagnostic_only",
        "sceneSize": [W, H],
        "tileSize": 32,
        "edgePolicy": "bounded",
        "layers": {"terrain": terrain},
        "objects": [],
        "transitions": [],
        "spawns": [{"id": "player_default", "tile": [37, 31]}],
        "editor": {"notes": [
            "W52 production-shaped Tavern acceptance uses one scene-local BuildingInstance and zero baked structural/furniture SceneMap objects.",
            "Enter through the south/front door at world tile 37,28 to trigger Sims-style local roof/front-wall cutaway.",
            "Ground level contains taproom tables/chairs, kitchen prep furniture, service storage, exact INN/PUB plaques, an exact four-tile wood service counter and an exact cast-iron hearth.",
            "Interact at world 42,26 for ground↔guest-floor stairs and at world 32,26 for ground↔cellar stairs.",
            "PageUp/PageDown/Home in the native editor previews all structural levels and cutaway state without scene transitions.",
            "Cellar kegs now use exact singular cask sprites; the Tavern contains no deferred furnishing visuals."
        ]},
        "acceptance": {
            "pass": "167Z109W52",
            "buildingInstanceId": "havenwild.acceptance.standard_tavern",
            "buildingRecipeId": "havenwild.tavern.standard_three_level",
            "buildingAuthority": "BuildingInstanceRegistry",
            "recipeAuthority": "BuildingRecipeRegistry",
            "visualAuthority": "PublishedWorldAssetRegistry",
            "structuralLevels": [-1, 0, 1],
            "ordinaryInteriorPolicy": "same_world_building_instance",
            "staticSceneObjectCount": 0,
            "runtimeMaterialized": True,
            "furnishingPlacementCount": 23,
            "publishedVisualFurnishingCount": 23,
            "deferredExactSourceCount": 0,
            "entryDoorWorldTile": [37, 28],
            "cellarConnectorWorldTile": [32, 26],
            "guestConnectorWorldTile": [42, 26]
        },
        "validationRules": [
            "tavern_building_acceptance contains no baked structural or furnishing SceneMap object carriers",
            "runtime/editor materialize BuildingInstanceRegistry + BuildingRecipeRegistry + PublishedWorldAssetRegistry directly",
            "furniture collision and interaction use published asset footprint/state metadata",
            "furnishing state deltas save and replicate inside BuildingInstance authority",
            "ground/guest/cellar traversal never changes scene id",
            "Tavern bar/hearth/keg visuals resolve to exact pinned LPC source regions through PublishedWorldAssetRegistry"
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
