# Havenwild Terrain Material Render-Mode Registry Audit — Pass 167Z63

## Trigger

The Pass167Z62 Windows build passed source validation, `cargo fmt --check`, `cargo check`, and Clippy, then failed 18 `haven_assets` tests. Every failure reported missing terrain material, missing canonical tuple, or a structure/overlay binding resolving to `None`.

## Root cause

`content/assets/terrain_material_bindings_v0_2.json` correctly declared the structural cliff binding with:

```json
"renderMode": "derived_elevation_structure"
```

The Rust deserializer in `crates/haven_assets/src/terrain_material_bindings.rs` did not define the corresponding `TerrainRenderMode::DerivedElevationStructure` enum variant. Serde therefore rejected the complete binding file. Because the registry is cached as one `Result`, a single unknown mode made all terrain bindings unavailable, including otherwise valid V7 mappings for grass, sand, dirt, roads, water, wet sand, bridge fallback, and authored corner tuples.

This was an authority synchronization defect. It was not missing V7 atlas data and was not a reason to restore cross-family ElizaWy fallback.

## Correction

- Added `TerrainRenderMode::DerivedElevationStructure` using the existing snake-case Serde convention.
- Treated derived elevation structures like other non-ground structural modes when querying tuple fallback material.
- Kept `Cliff` without a tuple fallback so it cannot return to flat ground painting.
- Added a Rust regression test proving that the derived cliff binding loads without disabling the rest of the material registry.
- Extended the terrain style/cliff/F3 validator to require the Rust mode, match arm, and regression test.

## Expected result

The 18 failed tests should recover together because their common registry dependency now loads. The pure V7 atlas remains the tuple source for its style lane, including authored fills, corners, water ownership fills, paths, shore materials, and three-material junctions. ElizaWy assets remain isolated and are not used to patch missing V7 bindings.

## Validation performed in the patch environment

- Parsed all project JSON through the Pass167Z62 owned-content validator.
- Ran the Pass167Z61 terrain style/cliff/F3 validator with the new Rust authority checks.
- Emulated the restored material lookup for all failed material-binding expectations.
- Confirmed required V7 tuple fixtures remain present in the isolated 4,035-entry manifest.
- Confirmed the intentionally unsupported three-material fixture remains absent.
- Python compilation passed for the modified validator.

Rust compilation and the full workspace test run remain for the Windows workstation, where the failure was originally reproduced.
