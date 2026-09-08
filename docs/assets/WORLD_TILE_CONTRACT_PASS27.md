# World Tile Contract Pass 27

This pass locks the first implementation-facing contract for Havenwild world tiles.

## Canonical tile rule

The game world remains a `32x32` canonical tile grid. Donor/reference packs may use 16, 32, 40, or 48 px grids, but runtime terrain authoring resolves to `32x32` unless an asset is explicitly metadata-marked as an oversized object.

## Nested detail masks

Each `32x32` tile can carry nested masks:

- `2x2` of `16x16` cells for coarse material weight painting.
- `4x4` of `8x8` cells for medium transition detail.
- `8x8` of `4x4` cells for fine shoreline/foam/debris masks.

These masks are not standalone gameplay cells. They are per-tile detail, blend, and paint-weight data used by the editor, renderer, PCG, and autotile resolver.

## First environment families

The first world-environment test families are:

- sand
- water
- cave
- paved_brick
- wood_plank

The generated strict-grid test atlas is intentionally limited to these families so world tile behavior can be stabilized before trees, grass, props, and NPC visuals are layered in.

## Layer contract

World tiles now route through named layer roles, including `ground_base`, `ground_transition_fringe`, `water_base`, `water_surface_fx`, `cave_base`, `cave_wall_face`, `town_surface`, `indoor_floor`, `debris_overlay`, `collision_footprint`, `occlusion_fade_mask`, and `dev_overlay`.

Server-authoritative gameplay state should store material IDs, subcell weight masks when authored, stable object IDs, collision footprints, ownership, and interaction data. Clients derive visual shoreline/variation/debris/occlusion output deterministically from the same manifests.

## Strict test atlas

The generated atlas at:

```text
assets/generated/world_tiles/havenwild_world_environment_test_v0_1/havenwild_world_environment_test_v0_1.png
```

is exactly `512x320`, arranged as `16` columns by `10` rows of `32x32` cells. It is a project-generated draft intended for engine/editor testing, not final art.

Its manifest is:

```text
content/assets/world_tiles/havenwild_world_environment_test_v0_1.json
```

## Next implementation step

The next source pass should wire this manifest into the in-game editor's world paint tools as a material-family brush backend, then expose subcell paint weights in a debug preview before saving them into scene delta data.
