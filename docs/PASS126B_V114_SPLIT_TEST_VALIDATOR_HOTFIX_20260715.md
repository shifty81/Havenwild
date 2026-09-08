# Pass 126B: V114 Split-Test Validator Hotfix

Date: 2026-07-15

## Purpose

After `runtime_editor_shell.rs` was split to satisfy the architecture line-count
limit, V114 still expected the shore/water test name to remain in the main
runtime editor shell source file.

## Change

- Keep V114 runtime logic checks pointed at `runtime_editor_shell.rs`.
- Point the shore/water test-name check at
  `runtime_editor_shell/shore_water_tests.rs`.

## Behavior

No runtime behavior changes.
