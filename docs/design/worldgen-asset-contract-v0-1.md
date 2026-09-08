# Worldgen Asset Contract v0.1

Date: 2026-05-25  
Project: Havenwild / Havenwild source

## Locked base assumptions

- Base tile size: **32x32 px**.
- Generated placeholder assets live under `assets/generated/worldgen_v0_1/`.
- Runtime world scenes currently use **48x32 tiles**.
- Asset sheets use **2 px atlas padding** with **1 px extruded edge padding**.
- Art direction: original cozy fixed-orthographic pixel art, not copied from Travellers Rest or Stardew Valley.
- Every atlas must have a sibling JSON manifest.
- Visual footprint, collision footprint, interaction points, occlusion, and fade behavior are manifest-driven.

## Required runtime/editor metadata

Each tile or object entry should declare:

```json
{
  "id": "home_oak_mature_summer",
  "kind": "object",
  "tileSize": [32, 32],
  "visualFootprint": [3, 3],
  "collisionFootprint": [1, 1],
  "origin": [1, 2],
  "layer": "foliage_tall",
  "occludesPlayer": true,
  "fadeWhenPlayerBehind": true,
  "biomeTags": ["home_island", "temperate"],
  "worldgenTags": ["tree", "wood_source"]
}
```

## Layer contract

1. `terrain_ground`: grass, dirt, sand, soil, floors.
2. `terrain_overlay`: foam, puddles, grass tufts, edge transitions.
3. `low_object`: clutter, flowers, rocks, shells, crops.
4. `object`: furniture, crates, barrels, counters, workstations.
5. `tall_object`: trees, walls, buildings, cliffs, cave fronts.
6. `roof_canopy`: tree crowns, roof overhangs, foreground masks.
7. `fade_overlay`: walls/trees that should fade around the player.
8. `collision`: separate non-rendered collision grid.
9. `interaction`: separate use/click/seat/harvest/service points.

## Autotile contract

- Primary terrain transitions target a **47-tile blob autotile**.
- Roads, paths, walls, cave edges, and simple trims may use a 16-tile directional subset.
- Water is split into ocean, freshwater, river, and river-mouth transition families.
- Ocean wave/foam tiles are separate animated overlays instead of being baked permanently into sand.

## Home island asset scope v0.1

The first complete biome set is the home island:

- Temperate wooded coastal island.
- Central mountain base tavern exterior.
- East/west and north/south road intersection.
- About 20-tile path from main road up to the tavern entrance.
- Beach/ocean edge, river/freshwater edge, cave entrance, east woods, south field.
- Native wood trees: oak and birch.
- Fruit tree placeholders to be added next: apple and pear.

## Tree footprint contract

| Stage | Visual footprint | Collision footprint | Notes |
|---|---:|---:|---|
| Sapling | 1x1 | 1x1 | Low object/tall object threshold depends on art height. |
| Young | 2x2 | 1x1 | Can occlude slightly. |
| Mature | 3x3 | 1x1 trunk | Player can walk under/around canopy except trunk tile. |
| Tall mature | 3x5 | 1x1 trunk | Up to 5 tiles high, fades around player. |
| Special landmark | 5x5 | 2x2 base | Rare, not standard tree size. |
| Stump | 1x1 | 1x1 | Harvest/removal target. |
| Fallen | 3x1 | 3x1 | Blocks until cleared unless marked decorative. |

## Scene-edge contract

Every scene must select an edge border set for each side:

- forest
- cliff
- ocean
- mountain
- city
- farm
- cave darkness
- dungeon darkness

This prevents the player-facing camera from showing empty void at scene borders and lets adjacent scenes visually map to the overworld.

## Validation rules

- A PNG atlas without a JSON manifest is invalid.
- Object visual footprint may exceed collision footprint.
- Collision cannot be inferred from sprite size.
- Seat, bar, table, workbench, door, stair, and harvest interactions must be authored as interaction points.
- Excess seating is allowed; tavern level controls active customer occupancy.
- Tall objects must declare whether they fade around the player.
- Water tiles must declare water family: ocean, freshwater, river, or transition.
