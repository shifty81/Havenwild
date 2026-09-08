# Worldgen Runtime Loader Patch v0.5

This patch is the first source-level bridge between the generated worldgen JSON data and the Rust runtime/editor structures.

## What changed

- Added `crates/haven_core/src/worldgen_loader.rs`.
- Added `load_worldgen_pack_from_path(...)`.
- Added startup fallback order:
  1. load `workspace/saves/world.tworld`,
  2. load `content/packs/worldgen_home_island_v0_4.json`,
  3. fall back to `GameWorld::starter()`.
- Added dev-mode `F10` reload for the generated worldgen pack.
- Added support for generated zones: `public_path`, `tavern_exterior`, and `bar`.
- Added editor palette entries for those zones.
- Added a cleanup script for the stale `crates/crates` duplicate folder that appeared in earlier applied-source zips.

## Current loader scope

The loader imports:

- scene id
- scene kind
- biome
- 48x32 terrain layer
- 48x32 zone layer
- object anchors from collision rectangles
- transitions
- default player spawn
- default tile heights derived from tile type

## Known limitation

The runtime still stores `PlacedObject` as a single tile anchor. The generated manifests already know full visual and collision rectangles, but the runtime collision system needs a v0.6 patch before those multi-tile footprints affect movement and object picking.

## Validation

Run these after applying:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools/automation/Repair-WorldgenV05Layout.ps1
powershell -ExecutionPolicy Bypass -File .\tools/automation/validation\checks\worldgen\Validate-WorldgenAssets.ps1
powershell -ExecutionPolicy Bypass -File .\tools/automation/validation\checks\worldgen\Validate-WorldgenRuntimeIndex.ps1
powershell -ExecutionPolicy Bypass -File .\tools/automation/validation\checks\worldgen\Validate-WorldgenLoaderV05.ps1
cargo check --workspace
```

`cargo check` must be run on your machine because this container does not have Rust/Cargo installed.
