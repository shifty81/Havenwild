# Worldgen Runtime Loader Contract v0.4

This pass turns the generated art/data pack into something the editor and runtime can consume deterministically.

## Load order

Use `content/worldgen/worldgen_runtime_load_order_v0_4.json` as the authoritative order:

1. Probe schemas.
2. Load the master asset manifest.
3. Load atlas JSON files and their PNGs.
4. Load `TileKind` runtime bindings.
5. Load the generated asset lookup and object footprint registry.
6. Load worldgen rules: placement, autotile, scene-edge, editor layer registry.
7. Load biome palette and world-surface scene map.
8. Load scenes.
9. Load transition/navigation graph.
10. Load editor overlays and previews.

## Runtime resolution rules

- `TileKind` resolves through `runtimeTileKindLookup` first.
- Scene object `assetId` resolves through `objectAssetLookup`.
- If an object is scene-only, it is allowed as a placeholder but should show a missing-production-art warning in the editor.
- Scene border policy resolves through `world_edge_border_resolution_v0_3.json`, then `borderLookup`.
- Collision and interaction rectangles are authoritative over visual rectangles.

## Editor panels this enables

- Tile/Autotile Palette
- Object Footprint Inspector
- Collision/Interaction Overlay
- World Graph
- Scene Edge Resolver
- Validation Console

## No Rust source changes in v0.4

This overlay intentionally avoids Rust source edits. The next risky step is a source-level loader that reads `worldgen_home_island_v0_4.json` and creates runtime `SceneMap` objects from JSON.
