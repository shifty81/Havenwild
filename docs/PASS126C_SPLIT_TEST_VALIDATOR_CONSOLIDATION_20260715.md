# Pass 126C: Split-Test Validator Consolidation

Date: 2026-07-15

## Purpose

The runtime editor shell tests were split out of `runtime_editor_shell.rs` to
satisfy the architecture line-count limit. Several validators still expected
shore/water test names to remain in the main source file.

## Change

- Keep runtime logic checks pointed at `runtime_editor_shell.rs`.
- Keep shore/water test-name checks pointed at
  `runtime_editor_shell/shore_water_tests.rs`.
- Consolidate the split-test aware validators into one patch overlay:
  - V114
  - V127
  - V128

## Behavior

No runtime behavior changes.
