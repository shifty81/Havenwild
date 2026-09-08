# Pass 139 — Wrapped World Coordinate Foundation

Pass 139 establishes the coordinate and persistence contract for Havenwild's finite globe-like exterior world.

## Locked behavior

- The overworld is finite, not endless.
- East/west traversal wraps continuously across one canonical seam.
- North/south remains bounded.
- Canonical persistence always stores coordinates inside the finite surface.
- Rendering and editor navigation may use the nearest unwrapped copy to avoid camera jumps at the seam.
- Chunk keys normalize before save, delta lookup, or host/server synchronization.
- Interiors, caves, ruins, dungeons, and other entered spaces remain scene-transition spaces.

## Implementation

`haven_world::world_topology` now owns:

- tile and chunk canonicalization;
- seam-aware cardinal neighbors;
- shortest wrapped horizontal distance;
- nearest-copy rendering/editor coordinates;
- canonical chunk persistence keys;
- topology schema and validation.

Client save metadata generation version is now 4 and records world dimensions, chunk size, and east/west wrapping. Each slot owns `worldgen/world_topology.json`.

## Next pass

Pass 140 should build the archipelago world skeleton on this contract: mainland, ten major biome islands, optional minor islands, ocean depth bands, and authored anchor reservations.
