# Pass 122 - LPC Runtime Terrain Promotion

This pass promotes the generated LPC `terrain-map-v7` atlas from catalog/deferred
data into the live terrain renderer.

## Runtime Policy

- `assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png` is now a
  runtime-loaded terrain atlas.
- `tools/automation/terrain/Build-LpcMappedTerrainV7.py` now emits the promoted
  `tileKindTerrainMap` during normal builds instead of regenerating the older
  deferred manifest shape.
- `TileKind::Grass`, `Dirt`, `Sand`, `ShallowWater`, `Water`, `DeepWater`, and
  their existing close aliases map to the LPC terrain names in
  `lpc_mapped_terrain_v7_32.json`.
- Sand/grass transition ownership is no longer left to the older neighboring
  transition overlay. The sand cell owns the visible shape, and adjacent grass
  cells do not draw competing sand overlays.
- Multi-cell sand/grass corners and edges are handled by the generated LPC
  mapped atlas.
- A small isolated sand-over-grass fallback remains for the single-cell case
  because a four-corner terrain tuple cannot represent "sand center with all
  four corners grass" without erasing the sand cell.

## Validation

- `Validate-LpcMappedTerrainReplacementV122.py` now validates runtime promotion
  instead of enforcing the older deferred policy.
- `Validate-LpcMappedTerrainRuntimePromotionV128.py` locks the atlas files,
  tile mappings, generator output policy, runtime atlas path, and sand/grass
  ownership hooks.

## Notes

- `cargo`, `rustc`, and `rustfmt` were unavailable in the scratch container, so
  Windows build validation remains required.
- `Validate-GenericTiledTerrainCatalogV123.py` still requires an OpenGameArt
  `terrain.png` source file that was not present in the attached source zips.
