# Worldgen v0.1 Apply Notes

Copy this overlay into the project root.

No Rust files are replaced by this pack. It is intentionally safe as an asset-contract layer first.

## What this accomplishes

1. Generates the asset contract.
2. Generates common base terrain, water, and autotile placeholder sheets.
3. Generates one complete home-island biome set.
4. Adds a JSON smoke-test scene and preview for editor/worldgen validation.
5. Leaves expansion to the other 9 islands for the next pass after loader validation.

## Immediate next code task

Implemented: editor/runtime `GeneratedAssetRegistry` now reads:

`assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`

and binds current `TileKind` variants to atlas entries in:

`assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json`

## Known limitation

The generated art is placeholder-grade and programmatic. It is designed to lock the pipeline and manifest contract, not final production art.
