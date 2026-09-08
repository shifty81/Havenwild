# Pass 120 - LPC Grass/Sand Boundary Fix

## Goal

Stabilize the LPC Terrain panel for grass and sand before moving on to other materials.

## Fix

- A single sand tile painted into grass now keeps the full authored LPC grass-over-sand boundary:
  cardinal grass neighbors request edge roles, and diagonal grass neighbors request inner-corner roles.
- The thin alternating `sand / grass / sand` case is still guarded so the center grass tile does not turn into a visual bridge.
- The previous broad inner-corner suppression was removed because it also blocked legitimate sand patch corners.
- The sparse ownership validator now locks the grass/sand behavior directly instead of defending the over-suppressed one-cell ring.

## Validation

- `Validate-LpcSparseLandTileOwnershipV126.py`
- `Validate-LpcMixedCornerTopologyV116.py`
- `Validate-LpcClosedSandGrassCornerTopologyV121.py`
- `Validate-LpcClientEditorStabilityV102.py`
- `Validate-NativeAutotileBoundaryFallbackV124.py`

Local container note: `cargo` is not installed in the scratch runtime, so Rust unit tests must be run by the normal Windows build.
