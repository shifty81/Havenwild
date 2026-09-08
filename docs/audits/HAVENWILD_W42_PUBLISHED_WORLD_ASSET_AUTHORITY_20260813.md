# Havenwild W42 — Published World Asset Authority

## Scope

W42 converts the W41A inventory into one runtime/editor/persistence identity path without creating a second asset registry. The existing registry implementation is evolved in place and old placeable type names remain compatibility aliases only.

## Implemented

- retired `content/asset_packs/havenwild_objects/placeables_v1.json`;
- added `published_world_assets_v1.json` (`havenwild.published_world_asset_catalog.v1`);
- 35 published records / 30 aliases;
- published all 29 W41A LPC-backed authored-scene candidates with exact source provenance and runtime cache regions;
- preserved authored scene `assetId` through `StablePlaceableAssetRef::from_scene_asset_alias`;
- canonicalized aliases at game startup, runtime worldgen reload and native-editor startup;
- exporter preserves unresolved aliases or canonical stable IDs;
- explicit primary legacy adapters prevent variant ambiguity;
- retained `ObjectKind` only as gameplay/save/fallback compatibility;
- updated older placeable validators and behavior tests to the published catalog/current serialization ownership;
- added `published-assets` build command, root menu command 34 and registered W42 source/full validator.

## Intentionally unresolved

The 12 W41A authored-scene blockers are not published aliases yet: `aging_barrel_row`, `bar_counter_stage_01`, `cave_mouth_entrance`, `greenhouse_stub`, `guest_bed`, `home_birch_tree_mature`, `home_tavern_mountain_entrance`, `large_table_six_seat`, `old_growth_landmark_tree`, `ore_node_copper`, `stone_signpost`, `stove_oven_2x3`. They require real source art or structural/building recipes.

## Validation

`Validate-PublishedWorldAssetAuthorityV1.py` requires 35 unique records, exact LPC provenance/runtime geometry for all 29 migrated scene candidates, 11 primary legacy adapters, zero premature blocker aliases, scene alias preservation/canonicalization, and retirement of the old catalog. The registered `source` profile passes.

## Next

W43 creates the placeable/world-asset acceptance scene and performs visual/anchor/footprint/collision/interaction/sort/occlusion certification before blockers are promoted.
