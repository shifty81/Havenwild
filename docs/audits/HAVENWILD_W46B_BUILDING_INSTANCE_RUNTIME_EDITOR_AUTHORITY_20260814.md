# Havenwild W46B — BuildingInstance Runtime + Editor Authority

Date: 2026-08-14  
Pass: `167Z109W46B`

## Purpose

Replace W46A's exploded scene-carrier-only proof with a native same-world `BuildingInstance` path shared by client and native editor.

## Authority split

- `BuildingInstanceRegistry` owns authored placement and stable instance identity.
- `BuildingRecipeRegistry` owns structural levels, logical walls, rooms, openings, connectors and roof assembly.
- `PublishedWorldAssetRegistry` remains the only exact visual/source identity authority.

No `ObjectKind` or baked acceptance carriers are used to define the W46B house.

## Runtime behavior

`havenwild.acceptance.three_level_house` is placed at tile `[24,14]` in `building_instance_acceptance` and references `havenwild.prototype.three_level_house`.

The client now:

1. materializes visible building pieces directly from the instance + recipe registries;
2. resolves every sprite through `PublishedWorldAssetRegistry`;
3. applies logical wall collision even when a facing-specific wall visual is deferred;
4. respects published per-state door collision;
5. derives camera-local inside/outside cutaway state from active-level room occupancy;
6. hides roof/front-wall groups locally when inside;
7. changes structural level through recipe connectors without changing SceneMap;
8. keeps inactive levels authoritative rather than loading/unloading separate scenes.

Diagnostic connector locations are deliberately distinct:

- cellar ↔ ground: local `[2,4]`;
- ground ↔ upstairs: local `[6,4]`.

The front diagnostic door starts `open_left` so entry traversal is testable without first adding W46C door-state persistence.

## Native editor behavior

The Scene Map canvas resolves the same instance + recipe + PublishedWorldAsset chain.

For scenes containing a BuildingInstance:

- `PageUp` previews the next structural level;
- `PageDown` previews the previous structural level;
- `Home` toggles cutaway/exterior roof presentation.

`building_instance_acceptance` contains zero baked building objects. This is the primary W46B convergence test.

## Deferred to W46C

- permanent/save-backed instance state and per-instance deltas;
- native editor placement/move/delete commands for BuildingInstances;
- PCG/open-world placement through the same instance contract;
- persistent door state mutation for recipe openings;
- multiplayer replication of authoritative building state while preserving camera-local visibility;
- continuous-surface/global-coordinate instance placement beyond the diagnostic authored scene.

## Validation

Packaging-environment checks completed before handoff:

- W46A BuildingRecipe authority PASS;
- W46B BuildingInstance authority PASS;
- architecture line-budget gate PASS after keeping `atlas_render.rs` and native `mod.rs` under declared limits;
- project content/integrity gates reached cleanly in the source-profile architecture run;
- W46B acceptance scene deterministically rebuilds with zero static structure carriers.

Windows Cargo compile/build remains the user-local final gate.
