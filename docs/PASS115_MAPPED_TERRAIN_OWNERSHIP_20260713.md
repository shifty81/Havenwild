# Pass115 Mapped Terrain Ownership

## Root Cause

Pass114 let `lpc_mapped_terrain_transition_covers_map_cell` report that a cell was covered by the Tiled terrain renderer whenever it touched a different mapped material.

That was broader than the actual draw rule. `lpc_mapped_terrain_entry_for_map` only draws on the owning side of a boundary, but the coverage check also suppressed legacy transition rendering on non-owner cells. The result was visible seep-through and missing/competing material at terrain boundaries.

Water was also promoted into live Tiled replacement before its Tiled water tuples were visually safe. The screenshot symptoms were grid/checker artifacts and shallow/deep water cells pulling unrelated detailed land pixels into a painted water region.

## Pass115 Contract

- A mapped terrain cell suppresses legacy transitions only if that same cell has an actual mapped replacement entry.
- Non-owner cells keep the stable base/autotile/transition renderer.
- Grass, dirt, and sand remain live Tiled-backed mapped terrain aliases.
- Wet sand and all water tile kinds remain cataloged but are deferred from live Tiled replacement.
- The full Tiled terrain catalog remains exported for future promotion.
- The placeable-object catalog split from Pass114B is included so the source remains under architecture limits.

## Validation

Validated locally:

- `Build-LpcMappedTerrainV7.py`
- `Validate-LpcMappedTerrainReplacementV122.py`
- `Validate-GenericTiledTerrainCatalogV123.py`
- `Validate-LpcPlaceableObjectPromotionV119.py`
- `Validate-LpcPaintTopologyStabilityV114.py`
- `Validate-HavenwildAssetUtilizationAuditV115.py`
- `Validate-LpcMixedCornerTopologyV116.py`
- `Validate-LpcClosedSandGrassCornerTopologyV121.py`
- `tools/automation/validation/validate_architecture.py`
- Python compile checks
- `bash -n tools/build/Build.sh`

Cargo is not available in the scratch environment; `tools/build/Build.cmd all` on the Windows workstation remains the Rust format/check/clippy/test authority.
