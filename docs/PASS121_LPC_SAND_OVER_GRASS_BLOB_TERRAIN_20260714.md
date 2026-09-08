# Pass 121 - LPC Sand Over Grass Blob Terrain

## Goal

Finish the first terrain pair before promoting the same neighbor-mask behavior to dirt, wet sand, shorelines, and water depth bands.

## What Changed

- Sand cells now own their visible grass boundary in the LPC Terrain lane.
- A single isolated sand cell no longer renders as a plain interior sand tile.
- Sand cells draw grass-side edge treatment when the cardinal neighbor is grass.
- Sand cells draw inner grass corner cutouts when two adjacent cardinal neighbors are sand but the diagonal is grass.
- Grass cells adjacent to sand skip the older sand transition overlay path so the two systems do not double-paint the same boundary.

## Why

The editor already paints one complete 32x32 sand cell. The remaining defect was visual resolution: the `0000` sand-neighbor case looked like pure sand instead of an isolated sand-over-grass blob. Fixing this on the sand cell itself matches the Tiled/Godot-style mental model and gives worldgen a reusable rule: terrain shape comes from the painted cell plus its 8-neighbor context.

## Validation

- `Validate-LpcSandGrassBlobTerrainV127.py`
- `Validate-LpcSparseLandTileOwnershipV126.py`
- `Validate-LpcMixedCornerTopologyV116.py`
- `Validate-LpcClosedSandGrassCornerTopologyV121.py`
- `Validate-LpcClientEditorStabilityV102.py`
- `Validate-NativeAutotileBoundaryFallbackV124.py`
- `Validate-TransitionAtlasGroupRustSyntaxV109.py`

Local container note: `cargo` and `rustfmt` are unavailable in scratch, so the Windows build remains the compile and visual confirmation step.
