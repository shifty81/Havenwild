# Worldgen Runtime Integration v0.2

Date: 2026-05-25

## Purpose

`worldgen_v0_1` generated real PNG atlases and JSON manifests for the common terrain set, water families, home-island trees, clutter, structures, borders, and a smoke-test scene. This v0.2 pass defines how those files should be validated and wired into the editor/worldgen runtime.

## Current source reality

The Rust source already has a game/editor split:

```text
crates/haven_core   shared world, scenes, tiles, objects, serialization
crates/haven_editor editor palette, validators, inspector reports
crates/haven_game   macroquad game/editor overlay runtime
```

The current `TileKind` enum is already close to the generated common terrain atlas. The main mismatch is that the generated asset pack contains richer art ids than the runtime enum currently exposes. That is intentional for now: runtime tile behavior should stay stable while atlas art can be expanded independently.

## Integration target

Add a runtime asset layer that maps existing `TileKind` behavior to atlas rectangles:

```text
TileKind::Grass        -> common_base_terrain_32.tiles[grass]
TileKind::TallGrass    -> common_base_terrain_32.tiles[tall_grass]
TileKind::Water        -> water_families_animated_32.tiles[freshwater or ocean by scene/water family]
ObjectKind::Tree       -> home_island_trees_32 object selected by biome/season/growth stage
ObjectKind::Bar        -> home_island_structures_32 object when exterior/outside bar is needed
Scene edge decorators  -> scene_edge_borders_32 by adjacent scene kind
```

Do **not** add a new Rust enum for every art variant yet. Use data-driven ids in JSON and keep Rust gameplay enums small until the render path is stable.

## Recommended module additions

```text
crates/haven_core/src/asset_manifest.rs
  AssetAtlasManifest
  AtlasTileRect
  AtlasObjectRect
  WorldgenAssetPack
  TileKindAtlasBinding

crates/haven_game/src/asset_runtime.rs
  LoadedAtlasTexture
  RuntimeAtlasCatalog
  draw_tile_from_catalog(...)
  draw_object_from_catalog(...)

crates/haven_editor/src/worldgen_asset_validation.rs
  editor-facing validation summaries
  missing atlas/image warnings
  invalid object footprint warnings
```

For the first compile-safe pass, these can be simple structs and manual JSON readers, or they can use `serde` if the workspace adds the dependency intentionally.

## Renderer binding order

1. Load `content/packs/worldgen_home_island_v0_1.json` at startup or editor command.
2. Follow the `masterManifest` path to `assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`.
3. Load all atlas JSON files listed by the master manifest.
4. Load each PNG referenced by convention from the JSON filename.
5. Resolve `runtime_bindings/rust_tilekind_mapping_v0_1.json`.
6. Render the current scene using tile/object bindings.
7. Keep the existing colored-rect fallback if any atlas fails.

## Editor workflow needed next

Add an editor tab or panel group named **Worldgen Assets**:

```text
Worldgen Assets
  Asset Pack: Home Island v0.1
  Validate Pack
  Reload Atlases
  Show Tile Bindings
  Show Missing Runtime Bindings
  Open Smoke Test Scene
  Save Smoke Test As World
```

The editor should show validation problems as warnings, not hard failures, unless image files are missing or JSON is invalid.

## Smoke-test scene usage

The smoke-test scene is located at:

```text
assets/generated/worldgen_v0_1/home_island/home_island_worldgen_smoke_test_v0_1.json
```

It is intentionally not written in the current `.tworld` save format. It is a neutral worldgen test format designed to test atlas ids, terrain layout, objects, borders, and placement metadata before runtime save serialization is finalized.

## Collision and footprint rules

Visual footprint and collision footprint must remain separate:

```text
visualFootprint: how many tiles the sprite occupies on screen
collisionFootprint: how many map cells block movement
origin: anchor tile used for sorting, placement, and object selection
```

Examples:

```text
normal mature tree: visual 3x3, collision 1x1
special landmark tree: visual 5x5, collision 2x2
mountain tavern entrance: visual 6x5, collision 6x1
clutter flowers: visual 1x1, collision 0x0
```

## Important rule

The asset generator creates placeholder production-shape assets. The next milestone is not more art. The next milestone is proving the editor can load, validate, preview, and place these assets using the metadata correctly.
