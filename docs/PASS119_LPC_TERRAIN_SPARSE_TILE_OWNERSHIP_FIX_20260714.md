# Pass 119: LPC Terrain Sparse Tile Ownership Fix

## Goal

Fix the `LPC Terrain` editor lane where sparse land placements such as `grass / sand / grass` or a one-cell sand/dirt edit caused neighboring grass cells to draw oversized sand/dirt transition art.

## Root Cause

The normal LPC terrain transition resolver let grass own sand/dirt boundary art. That works for larger blobs, but for sparse one-cell edits it made the visual result expand into surrounding grass cells. In alternating layouts, grass cells between two sparse sand/dirt cells could also draw two opposing transition edges, making the placed tile look like it was targeting the edge of the cell instead of the cell itself.

## Fix

- Added sparse grass-land ownership suppression in `transition_resolver.rs`.
- Grass no longer draws sand/dirt/farm transition overlays unless the neighboring land material has same-family side support.
- Pure diagonal grass-to-sand/dirt inner-corner art is suppressed for sparse land edits.
- Contiguous sand/dirt patches still receive supported edge transitions.
- Updated atlas request tests so a single sand cell no longer requests an expanding eight-neighbor grass ring.

## Validation

- `tools/automation/validation/checks/terrain/Validate-LpcSparseLandTileOwnershipV126.py`
- `tools/automation/validation/checks/terrain/Validate-LpcSeasonalTerrainTopologyV106.py`
- `tools/automation/validation/checks/editor/Validate-LpcClientEditorStabilityV102.py`
- `tools/automation/validation/checks/misc/Validate-LpcPaintTopologyStabilityV114.py`
- `tools/automation/validation/checks/misc/Validate-LpcMixedCornerTopologyV116.py`
- `tools/automation/validation/checks/terrain/Validate-LpcClosedSandGrassCornerTopologyV121.py`
- `tools/automation/validation/checks/terrain/Validate-NativeAutotileBoundaryFallbackV124.py`

This pass is for the `LPC Terrain` panel/editor lane, not the separate `Blend` material-paint path.

## Direction

Promote the LPC terrain lane as the main terrain authoring path:

- Treat reviewed LPC 32x32 tile/role mappings as canonical runtime terrain.
- Keep sparse editor edits tile-owned; one click should not silently expand into neighbor cells.
- Bring similar compatible 32x32 tilesets through the same role/topology catalog pipeline so they become drop-in alternatives once mapped.
- Keep experimental blend/material-paint work out of the main terrain authoring loop until the LPC path is stable.
