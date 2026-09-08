# Pass 125: Water Animation Ownership

Date: 2026-07-15

## Purpose

Terrain-v7 is now the canonical renderer for mapped natural terrain, including
coastline and water-depth cells. Legacy transition overlays must not draw on top
of cells that terrain-v7 already owns.

## Changes

- Added `lpc_mapped_terrain_owns_map_cell`.
  - Returns true when the target map cell participates in any terrain-v7 mapped
    render tile, not only when a mixed tuple is present.
  - The runtime transition pass now suppresses legacy transition overlays for
    these owned cells.
- Kept mixed coastline and water-depth tuples stable.
  - Mixed shore/depth shapes remain authored static terrain geometry.
  - This avoids full-tile blinking/crawling on coast edges.
- Expanded pure water animation coverage.
  - `Water`
  - `Water_Deep`
  - `Water_Shallows_Sand`
  - `Water_Shallows_Dirt`
- Added per-tile animation phase/hold offsets.
  - Water tiles no longer advance in a fully synchronized sheet-wide pulse.
  - The policy still uses authored pure-fill variants only.

## Intentionally deferred

- Animated coastline shimmer/crawl overlays.
  - The current pass prevents stale legacy art from bleeding into the shore.
  - A later pass should add a small overlay layer for foam/crawl effects rather
    than swapping the whole mixed coastline tile.
- New water biomes such as lava, ice, purple water, green swamp water.
  - The same pure-fill animation policy can be extended once those semantic
    materials are promoted into the editor.

## Validation

- `tools/automation/validation/checks/characters/Validate-LpcWaterAnimationOwnershipV129.py`
- Updated V122/V128 contracts so stale mixed-only overlay ownership is no longer
  treated as required behavior.
