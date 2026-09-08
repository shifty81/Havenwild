# Havenwild W46A — Building Recipe Authority

Date: 2026-08-14  
Pass: `167Z109W46A`

## Purpose

W46A establishes the first canonical `BuildingRecipeRegistry` and `BuildingRecipeDefinition` without creating a second visual-asset authority. `BuildingRecipe` owns structural assembly and `PublishedWorldAssetRegistry` continues to own exact component identity, provenance, source rectangles, topology metadata and certification state.

## Locked building model

Ordinary buildings are one same-world `BuildingInstance` with discrete structural levels. The diagnostic authority recipe exercises:

- level `-1`: cellar/basement;
- level `0`: ground floor;
- level `+1`: upstairs;
- explicit stair connectors between `-1↔0` and `0↔+1`;
- one roof assembly attached to the same building instance.

Ordinary upstairs, basements and interiors do not imply scene transitions. Separate scenes remain exceptions for genuinely streamed/instanced spaces such as deep cave networks, large dungeons or spatially nonlocal interiors.

## Authority separation

`BuildingRecipeRegistry` owns:

- footprint and structural levels;
- logical wall runs and collision;
- floor fills;
- openings;
- room/zone rectangles;
- structural connectors;
- roof assembly topology;
- cutaway groups;
- same-world persistence policy.

`PublishedWorldAssetRegistry` owns:

- exact visual component identity;
- exact source path/rectangle and provenance;
- structure topology metadata;
- certification state.

Generated atlases remain rendering caches only.

## Fail-closed facing policy

The currently published `wall_drywall_simple` is exact south-facing wall art. W46A therefore does **not** rotate/substitute it for north/east/west runs. Those logical walls remain authoritative for geometry/collision while their visual state is explicitly `deferred_exact_facing` and emits no visual until exact facing-specific art is reviewed.

This is intentional and prevents a repeat of earlier terrain/cliff substitution errors.

## Initial recipe

`content/buildings/recipes/three_level_house_prototype_v1.json`

The 9×7 diagnostic recipe includes:

- dark wood cellar floor;
- light wood ground/upstairs floors;
- exact south wall faces;
- exact front door;
- exact ornamental windows;
- exact short stair-run connectors;
- exact gray Flat Shingle nine-slice roof;
- room zones reserved for W47 interior grammar;
- camera-local roof/wall cutaway groups.

It is `diagnosticOnly=true` and is not the production Estate house.

## Deterministic materialization

`BuildingRecipeDefinition::materialize_structural_pieces()` expands currently resolved visual pieces into floor, wall, opening, connector and roof references. It never copies source rectangles; every visual piece remains a `PublishedWorldAsset` reference.

Door/archway openings replace the wall visual at their tile. Windows overlay the wall. Deferred-facing walls emit no wrong visual.

## Acceptance fixture

`building_recipe_acceptance` presents an exploded diagnostic view of cellar, ground, upstairs and roof. The exploded layout is presentation-only; the recipe itself remains one `BuildingInstance`.

199 current visual pieces are emitted from exact/candidate published structural assets.

## Validation

In the packaging environment:

- development layout: PASS;
- architecture: PASS (`415` Rust source files checked);
- project content: PASS (repository-owned JSON authority checked; external/transient state skipped);
- content integrity: `18/18 PASS`;
- W45D2 exact structural publication: PASS;
- W46A BuildingRecipe authority: PASS;
- `Build.sh building-recipes`: PASS.

Windows/Cargo compile remains a user-local gate for the new Rust module.

## Next

W46B should connect `BuildingRecipeRegistry` and deterministic materialization to the native editor/client runtime path so the same recipe can be instantiated as a native `BuildingInstance`, with active structural level and camera-local cutaway state rather than diagnostic scene carriers.
