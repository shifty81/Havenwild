# Pass116 Tiled Terrain Runtime Deferred

Pass115 fixed mapped-terrain ownership, but screenshots still showed square holes, grid/checker artifacts, and material bleed when painting grass, sand, dirt, and water near each other.

Root cause: `terrain-map-v7.tsx` is a Tiled corner/vertex terrain tileset. Havenwild's live map currently stores one `TileKind` per cell and renders cell-based base/transition passes. Directly drawing Tiled corner tuples as complete cell replacements mixes two ownership models:

- Tiled terrain owns tile corners/vertices.
- Havenwild runtime terrain owns whole cells.

That mismatch makes some cells draw Tiled replacement art while neighboring cells still draw native transition art, producing the visible square holes and seep-through.

Pass116 keeps the full Tiled terrain catalog and generated preview outputs, but defers live runtime replacement:

- `tileKindTerrainMap` is empty.
- editor catalog materials are `paintableNow: false`.
- the mapped terrain atlas path returns a runtime-deferred error.
- runtime no longer falls back to loading the mapped atlas after that error.
- `mapped_terrain_name` returns `None` for all `TileKind` values.

The correct future promotion path is one of:

1. Bake Tiled corner tuples into Havenwild's native cell-mask transition atlases.
2. Add a real corner/vertex terrain layer to the engine.

Until then, grass, dirt, sand, wet sand, and water painting should use the stable Havenwild cell/autotile renderer rather than the Tiled replacement renderer.

## Why TSX Still Matters

The TSX file is useful as source metadata. It tells us which image tile represents each four-corner terrain tuple, for example `grass,grass,sand,sand`. That is enough to build a correct importer.

The problem is drawing those tuples directly in Havenwild's current renderer. A Tiled terrain tuple describes four tile corners, while Havenwild currently stores one center-owned `TileKind` per map cell. The correct path is to convert the TSX tuple set into one of Havenwild's native runtime forms:

- a baked cell-mask atlas for each promoted material relationship; or
- a new corner/vertex terrain layer that stores Tiled-style ownership directly.

Until one of those exists, the TSX catalog remains planning/import data and should not suppress or replace the native cell renderer.
