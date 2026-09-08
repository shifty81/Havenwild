# Havenwild Terrain Set Schema V2

The V2 schema is additive and reference-only during Pass 147R. Existing runtime rendering remains active until the prototype reaches zero unsupported patterns.

## Core records

- `terrainSetId`: compatibility/matching domain.
- `terrainId`: distinct semantic visual terrain.
- `matchMode`: `corners_and_sides`, `corners_only`, or `sides_only`.
- `placementMode`: default editor intent: `connect`, `path`, or `manual`.
- `waterPlacement`: `forbidden`, `allowed`, or `requires_structure`.
- `atlasCandidates`: stable pattern candidate IDs.

Distinct terrains may share a set without automatically connecting. Compatibility is explicit and asymmetric where necessary.
