# Pass 135B V122 Split-Test Validator Hotfix

Date: 2026-07-15

## Scope

This pass fixes the V122 validator after the mapped terrain tests were extracted from `crates/haven_assets/src/lpc_mapped_terrain.rs` into `crates/haven_assets/src/lpc_mapped_terrain_tests.rs`.

## Change

`tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainReplacementV122.py` now keeps runtime implementation checks in `lpc_mapped_terrain.rs`, while allowing test-only guard names to be found in either the runtime file or the extracted test file.

## Local validation

The following checks pass locally:

- `python3 -m py_compile tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainReplacementV122.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedTerrainReplacementV122.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcTerrainDetailEditorWindowV123.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedEditorTerrainAndWaterPaintV135.py`
- `python3 tools/automation/validation/checks/persistence/Validate-LpcEnvironmentTileMigrationV112.py`
- `python3 tools/automation/validation/validate_architecture.py`
- `bash -n tools/build/Build.sh`

`cargo` is not available in this container; run the full Windows `tools/build/Build.sh all` to confirm the next cargo/clippy phase.
