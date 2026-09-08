# Asset Requirements Specification

Date: 2026-05-24

## Goal

Define exact asset families, sizing rules, pivots, metadata, and atlas expectations for the non-isometric 2.5D scene system.

## Core Visual Standard

### Grid Standard

- simulation tile size: **32x32 px**
- optional sub-grid for GUI and fine alignment: **16x16 px**
- object footprints resolve in tile units, not freeform pixels

### Approved Sprite Sizes

| Type | Typical Size | Notes |
| --- | --- | --- |
| Ground tile | 32x32 | base terrain, floors, paths |
| Detail decal | 32x32 or 32x16 | overlays, edge wear, puddles, clutter |
| Low object | 32x32 to 32x48 | stools, crates, shrubs |
| Medium object | 32x48 to 64x64 | tables, kegs, beds |
| Tall object | 32x64 to 64x96 | trees, tall shelves, cliff fronts |
| Front occluder | width by 32-96 tall | canopy, roof edge, arch, wall front |
| Backdrop slice | variable | mountains, tree lines, skyline silhouettes |

## Terrain Families

### Required Ground Families

1. grass
2. dirt
3. mud
4. stone path
5. plank floor
6. brick/stone floor
7. sand
8. wet sand
9. pebble shore
10. shallow water
11. deep water
12. mountain path
13. mountain rock
14. cliff top
15. cave floor
16. tilled soil

### Variant Minimums

- minimum 3 visual variants per commonly repeated terrain tile
- minimum 16 connection states for autotile families
- separate shoreline/cliff edge overlays where full autotile replacement is too rigid

## Object Families

### Tavern / Interior

- counters
- tables
- chairs/benches
- shelves
- taps
- kegs
- barrels
- crates
- fireplace/stove
- beds
- wardrobes
- rugs
- lamps/candles

### Exterior / World

- trees
- stumps
- bushes
- rocks
- ore nodes
- fences
- gates
- signs
- wells
- bridges

### Marker / Editor-Only

- zone stamps
- transition arrows
- spawn markers
- validation markers
- spawner/event markers

## Depth / Pivot Rules

### Sort Pivot

Every placeable object needs:

- `pivot_x`
- `pivot_y`
- `sort_mode`

Default rule:

- sort by feet/base contact point near the bottom-center of the sprite

### Front Occluders

Objects or tiles that can cover the player require:

- `occludes_front = true`
- occluder bounds
- optional fade behavior when player is behind

### Cliff / Height Assets

Each height transition needs:

- top tile
- front face tile
- corner variants
- side continuation variants
- shadow/decal overlays

## Metadata Contract

Every asset definition should expose:

```json
{
  "id": "shore_wet_sand",
  "category": "terrain",
  "family": "shore",
  "biomes": ["coast"],
  "tileSize": [32, 32],
  "footprint": [1, 1],
  "pivot": [16, 28],
  "autotileGroup": "shoreline",
  "heightBands": [0, 1],
  "collision": "walkable",
  "frontOccluder": false,
  "shadowProfile": "low",
  "variants": 4
}
```

## Atlas Rules

- atlas grouping should follow logical families:
  - terrain
  - interiors
  - nature
  - cave/mountain
  - characters
  - UI
- keep metadata separate from image filenames
- generated atlases must preserve stable ids across rebuilds

## Exact 2.5D Asset Additions Needed

### Coast

- sand flats
- wet shoreline transition
- pebble shore
- shallow-water edge
- foam/detail decals

### Mountain

- highland grass/dirt variants
- mountain path
- mountain rock
- cliff front faces
- cliff shadow overlays
- distant mountain backdrops

### Water

- shallow water
- deep water
- shoreline edge masks
- river bend and inlet-friendly variants
- bridge-ready water states

### Cave / Dungeon

- cave floor
- damp floor
- cave wall autotiles
- support beams
- rubble decals
- ore node families
- doorway/threshold pieces

## GUI / Overlay Asset Rules

- UI uses grid-snapped frame parts that scale cleanly by 16px increments
- panels need skins for:
  - normal
  - active
  - warning
  - minimized
- icon families should cover:
  - build
  - decor
  - zone
  - validation
  - graph
  - save/load
  - heightmap tools

## Delivery Standard For Generated Assets

Every generated asset batch must include:

1. source prompt or source script id
2. atlas or file output list
3. metadata manifest
4. license/ownership note
5. intended replacement tier:
   - placeholder
   - prototype
   - near-final
