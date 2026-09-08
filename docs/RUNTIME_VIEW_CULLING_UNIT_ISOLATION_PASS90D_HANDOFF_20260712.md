# Havenwild Pass 90D — Runtime View-Culling Unit Isolation

## Problem

The Pass 90C workspace reached the final `haven_game` test target, where
`runtime_view_culling::tests::bounds_are_clamped_to_expanded_scene` panicked
inside Macroquad because the unit test called `screen_width()` and
`screen_height()` without an initialized Macroquad runtime thread/context.

## Correction

`runtime_view_culling.rs` now separates the runtime wrapper from the pure
calculation:

- `visible_tile_bounds(...)` remains the production entry point and supplies
  the current Macroquad viewport dimensions.
- `visible_tile_bounds_for_viewport(...)` performs the deterministic bounds
  calculation from an explicit `Vec2` viewport size.
- The unit test calls only the pure helper with a 1920x1080 viewport.

No runtime culling math, camera behavior, scene dimensions, or terrain behavior
changed.

## Validation

Added `tools/automation/validation/checks/misc/Validate-RuntimeViewCullingUnitIsolationV96.py` and registered it
in the editor validation domain. The validator prevents tests from directly
calling Macroquad screen-dimension functions.

Run on Windows:

```bat
tools/build/Build.cmd all
```

The expected result is that the previously failing `haven_game` culling test
passes and the build continues into the remaining workspace tests, validators,
and release packaging.
