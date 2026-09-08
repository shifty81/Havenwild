# Pass 118: World Paint Single-Cell Overlay Fix

## Goal

Fix the runtime/editor paint feel where a one-tile brush behaved like it was targeting tile edges or requiring two rows before the visual resolved cleanly.

## Root Cause

- `radius_tiles == 1` expanded through the same circular brush code as larger brushes, so a one-tile paint action could affect the clicked cell plus cardinal neighbors.
- Material-state replay used its own matching radius calculation, so adjacency/render bindings inherited the same oversized footprint.
- Runtime paint atlas bindings skipped the base terrain draw for bound cells, letting a selected atlas tile replace the painted cell center.

## Fix

- Added `world_paint_cells_in_brush`.
- Locked radius `1` to exactly the clicked 32x32 cell.
- Reused the same footprint helper for material-state replay.
- Changed runtime terrain drawing so world-paint atlas bindings overlay the owner base tile instead of suppressing it.

## Validation

- `tools/automation/validation/checks/terrain/Validate-NativeAutotileBoundaryFallbackV124.py`
- `tools/automation/validation/checks/terrain/Validate-WorldPaintSingleCellOverlayV125.py`

`tools/automation/validation/validate.py` still stops later in this source-only rollup because generated asset outputs are not present:

- `assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.json`
- `assets/generated/worldgen_v0_1/terrain/live_autotile_16_32.png`
- `assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`
- `content/editor/assets/asset_palette_atlas_binding_contract_v0_1.json`
