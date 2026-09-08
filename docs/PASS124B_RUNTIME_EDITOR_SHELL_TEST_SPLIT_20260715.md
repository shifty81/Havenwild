# Pass 124B — Runtime Editor Shell Test Split

Date: 2026-07-15

## Purpose

Fix the final architecture validation failure from Pass 124A without changing terrain behavior.

The Windows build reached `cargo check`, `cargo clippy`, `cargo test`, and `cargo build`, then failed because `crates/haven_game/src/runtime_editor_shell.rs` exceeded the architecture line limit.

## Change

- Moved shore/water normalization unit tests into `crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs`.
- Left the production shore/water normalization implementation in `runtime_editor_shell.rs`.
- Updated V114, V127, and V128 validators so production guards still inspect `runtime_editor_shell.rs`, while test-name guards inspect the new sibling test module.

## Behavior

No gameplay or editor behavior changed in this pass.

The guarded behavior remains:

- Sand touching cardinal water normalizes to wet sand.
- Wet sand away from cardinal water normalizes back to sand.
- Deep water touching land or shore through the eight-neighbor shore buffer normalizes to shallow water.
- Pure water/deep-water fills can animate through authored variants.
- Mixed shore/depth edges stay stable instead of cycling frames.

## Local validation

Validated in the scratch workspace:

- `tools/automation/validation/checks/misc/Validate-LpcPaintTopologyStabilityV114.py`
- `tools/automation/validation/checks/terrain/Validate-ShoreWaterNormalizationV127.py`
- `tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
- `tools/automation/validation/validate_architecture.py`
- `bash -n tools/build/Build.sh`

`runtime_editor_shell.rs` is now 710 lines, under the 750-line architecture limit.
