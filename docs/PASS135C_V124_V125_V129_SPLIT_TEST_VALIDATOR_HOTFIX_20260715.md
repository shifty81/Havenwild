# Pass 135C V124/V125/V129 Split-Test Validator Hotfix

Date: 2026-07-15

## Scope

This pass continues the Pass 135 split-test cleanup. The mapped terrain tests now live in `crates/haven_assets/src/lpc_mapped_terrain_tests.rs`, so validators must not require test-only guard names inside the runtime implementation file.

## Changes

- `tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainRuntimePerformanceV124.py`
  - Keeps runtime lookup/performance checks in `lpc_mapped_terrain.rs`.
  - Allows the test call `entry_for_corners([LpcMappedTerrainMaterial::Grass; 4], 0)` in the extracted test file.
- `tools/automation/validation/checks/terrain/Validate-LpcStructuralRockTerrainDeferralV125.py`
  - Keeps structural-rock runtime mapping checks in `lpc_mapped_terrain.rs`.
  - Allows the structural-rock test guard in the extracted test file.
- `tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
  - Keeps water animation ownership implementation checks in `lpc_mapped_terrain.rs`.
  - Allows water ownership/animation test guards in the extracted test file.

## Local validation

The following checks pass locally:

- `python3 -m py_compile` for V124, V125, and V129
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainReplacementV122.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcTerrainDetailEditorWindowV123.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainRuntimePerformanceV124.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcStructuralRockTerrainDeferralV125.py`
- `python3 tools/automation/validation/checks/terrain/Validate-TerrainMaterialRegistryV126.py`
- `python3 tools/automation/validation/checks/terrain/Validate-ShoreWaterNormalizationV127.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedEditorTerrainAndWaterPaintV135.py`
- `python3 tools/automation/validation/validate_architecture.py`
- `bash -n tools/build/Build.sh`

`cargo` is not available in this container; the Windows full build remains the final confirmation step.
