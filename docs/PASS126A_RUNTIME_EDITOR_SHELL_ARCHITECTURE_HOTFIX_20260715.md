# Pass 126A: Runtime Editor Shell Architecture Hotfix

Date: 2026-07-15

## Purpose

The Pass126 runtime and validation changes passed fmt, check, clippy, tests, and
workspace build. The remaining failure was the architecture line-count guard:

- `crates/haven_game/src/runtime_editor_shell.rs` exceeded the 750-line limit.

## Change

- Keep shore/water normalization tests in
  `crates/haven_game/src/runtime_editor_shell/shore_water_tests.rs`.
- Leave `runtime_editor_shell.rs` with only `#[cfg(test)] mod shore_water_tests;`.

## Behavior

No runtime behavior changes.

## Validation

- `tools/automation/validation/validate_architecture.py`
- `tools/automation/validation/checks/misc/Validate-LpcPaintTopologyStabilityV114.py`
- `tools/automation/validation/checks/terrain/Validate-ShoreWaterNormalizationV127.py`
- `tools/automation/validation/checks/characters/Validate-LpcWaterAnimationAndShoreDepthV128.py`
