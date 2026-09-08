# Pass 126: Sparse Water Animation

Date: 2026-07-15

## Purpose

The full pure-water variant cycling was too visually noisy. Because every water
cell advanced through detailed variants, the screen read as marching pixels
instead of subtle water motion.

## Changes

- Pure water animation is now sparse.
  - About 12 percent of pure water cells receive animated detail.
  - The remaining cells stay on the quiet base fill.
- Animated water detail is slower.
  - Detail cells hold frames for multiple water ticks before advancing.
  - Hold duration is deterministic per tile, so the whole ocean no longer pulses
    in lockstep.
- Terrain-v7 overlay ownership no longer depends on a direct center-cell
  precheck.
  - Ownership is determined by whether terrain-v7 can draw one of the sampled
    render tiles for that position.

## Notes

- Mixed coastline and water-depth tuples remain static. They should not swap
  whole tiles for animation because that causes visible crawling along authored
  shore geometry.
- If the coast still needs motion, the next step should be a separate subtle
  shoreline shimmer/foam overlay using sparse alpha sprites, not full mixed-tile
  replacement.

## Validation

- `tools/automation/validation/checks/characters/Validate-LpcSparseWaterAnimationV130.py`
- Updated `tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
