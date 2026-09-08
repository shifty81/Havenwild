# Worldgen v0.6 Multi-Tile Footprint Runtime Patch

## Purpose

Worldgen v0.5 loaded scene objects as single anchor tiles. v0.6 upgrades the runtime/editor bridge so generated scene objects can carry separate visual, collision, and interaction rectangles. This is required for large tables, outside bars, cave entrances, tavern facades, greenhouse markers, trees, beds, barrel rows, and future multi-tile build-mode objects.

## Runtime model

`PlacedObject` now stores an `ObjectFootprint` alongside `ObjectKind`, `x`, and `y`.

The footprint contains:

- visual offset and size
- collision offset and size
- interaction offset and size
- movement blocking flag
- player occlusion/fade flags

The loader parses `visualRect`, `collisionRect`, and the first `interactions[].rect` from generated scene JSON. The object anchor is the collision rectangle origin when present. Visual and interaction offsets are stored relative to that anchor.

## Editor behavior

The inspector now reports the object footprint at the selected tile, including visual, collision, and interaction rectangles. Validation now checks spawn/transition walkability against blocking object footprints, not only terrain tiles.

## Gameplay behavior

Player movement now uses `SceneMap::is_cell_walkable`, which checks both terrain walkability and blocking object collision. Object drawing uses visual rectangle size, while render sorting uses the bottom of the collision footprint.

## Save compatibility

Old object save lines with `object kind x y` still load. New saves write the extended object footprint fields so custom worldgen footprints are preserved.

## Remaining work

The next patch should add visual overlay toggles for collision/interaction rectangles in the editor and proper object placement previews before commit.
