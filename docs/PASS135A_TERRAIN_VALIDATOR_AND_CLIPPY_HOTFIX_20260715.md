# Pass 135A Terrain Validator and Clippy Hotfix

Date: 2026-07-15

## Scope

This pass keeps the Pass 135 terrain-v7 editor/water-paint work intact while fixing the follow-up build failures reported after the full validation run.

## Changes

- Split `crates/haven_assets/src/lpc_mapped_terrain.rs` tests into `crates/haven_assets/src/lpc_mapped_terrain_tests.rs` so the runtime source remains below the architecture line cap.
- Updated terrain validators that previously searched only the runtime source for test-only guard names. They now accept those guards in the extracted test module while still requiring runtime implementation tokens in the production source.
- Rewrote the editor terrain badge match arms in `crates/haven_game/src/runtime_draw.rs` to use direct enum-pattern matching instead of redundant guarded matches.

## Local validation

The following checks pass in this container:

- `python3 -m py_compile` for the updated terrain validators
- `python3 tools/automation/validation/validate_architecture.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcTerrainDetailEditorWindowV123.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `python3 tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedTupleFallbackV131.py`
- `python3 tools/automation/validation/checks/terrain/Validate-LpcMappedEditorTerrainAndWaterPaintV135.py`
- `python3 tools/automation/validation/checks/persistence/Validate-LpcEnvironmentTileMigrationV112.py`
- `bash -n tools/build/Build.sh`

`cargo` is not available in this container, so Windows `cargo clippy --workspace --all-targets -- -D warnings` remains the final confirmation step.
