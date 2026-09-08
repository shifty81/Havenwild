# Pass 124A — Water Animation Clippy Hotfix

Date: 2026-07-15

## Purpose

Pass 124 passed the terrain validators and `cargo check`, but failed strict
Clippy with:

- an unused `lpc_mapped_terrain_entry_for_map` import in `haven_game`;
- `draw_tile_base` exceeding the project argument-count limit after adding the
  water animation frame.

## Fix

- Removed the stale `lpc_mapped_terrain_entry_for_map` import from
  `crates/haven_game/src/main.rs`.
- Collapsed `draw_tile_base` screen coordinates into one `Vec2` argument so the
  water animation frame can remain explicit without tripping
  `clippy::too_many_arguments`.
- Strengthened V128 to guard both the animated-water behavior and this Clippy
  shape.

## Behavior

No terrain behavior changes beyond Pass 124:

- pure water/deep-water fills animate through authored variants;
- mixed shore/depth edge geometry remains stable;
- deep water keeps a shallow buffer around shore/land.
