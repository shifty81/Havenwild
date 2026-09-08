# Pass 140 — Archipelago World Skeleton

Pass 140 establishes the deterministic finite-world landmass skeleton on top of Pass 139 wrapping.

## Contract
- Exactly one mainland.
- At least ten major islands, each with a distinct biome identity slot.
- Configurable smaller buildable islands.
- East/west coordinates use the wrapped topology; north/south remains bounded.
- Four ocean depth bands: shore, shallow, continental shelf, and deep ocean.
- Mainland and every major island reserve authored anchors before detailed PCG.
- Interiors, caves, ruins, and dungeons remain scene-based destinations.

## Implementation
`haven_world::archipelago_skeleton` provides deterministic generation, validation, biome identity, landmass classes, ocean-depth classification, and authored anchor reservations. `content/worldgen/archipelago_world_skeleton_v1.json` is the editor/runtime policy contract.

Detailed coastlines, elevation, roads, settlements, and biome decorators remain later generation stages and must preserve these reservations.
