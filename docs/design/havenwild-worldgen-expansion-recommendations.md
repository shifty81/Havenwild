# Havenwild — World Appearance + Generation Expansion Recommendations

## Current base

The clean source is already pointed in the right direction: it uses 32x32 tiles, scene maps, zone layers, scene transitions, a `TileKind` enum with 25 entries, scene biomes, and per-cell height storage. The current gap is that maps are still mostly hand-shaped rectangles and simple hash scatter. The next upgrade should turn the world into a layered generator.

## Scale correction

Do not present the starter island as one 48x32 scene where the tavern, farm patch, road, and cave overlay the entire island mask. That reads as a board-game token map, not a cozy world.

Use two different preview scales:

| Preview type | Purpose | Scale rule |
|---|---|---|
| Region/world graph preview | Shows island or region shape, coast, towns, cave areas, and scene links | large abstract map; structures are icons or labels |
| SceneMap preview | Shows the playable 48x32 local scene | tavern/farm/road/cave are tile-scale local features |
| Layer debug preview | Shows height, moisture, zones, protection, and generated flags | use false colors, and label as debug data |
| Art/presentation preview | Shows actual terrain/object sprites | generated from the active scene/layer data |

For the starter experience, the island/region should be composed from connected scenes such as Farmstead, SouthField, EastWoods, NorthRoad, CaveMouth, and future harbor/town scenes. The farmstead scene can contain a tavern footprint, starter field, road exits, creek, and cave approach, but it should not try to depict the entire island silhouette.

## Highest-value additions

### 1. Separate visual layers from gameplay tile identity

Do not keep adding one hard tile for every visual variation. Keep the base gameplay tile stable, then render overlays/decor above it.

Recommended layers:

| Layer | Purpose | Examples |
|---|---|---|
| Base tile | gameplay identity | grass, sand, road, water, wood floor |
| Edge/autotile | neighbor-aware borders | shoreline, road edge, wall edge, cliff edge |
| State overlay | temporary condition | wet soil, watered crop, dust, snow, ash |
| Decor overlay | non-blocking visual flavor | flowers, reeds, shells, pebbles, mushrooms |
| Object layer | blocking/interactable entities | tree, keg, table, bed, ore node |
| Lighting/shadow | mood and readability | cave darkness, tree shade, indoor warm light |

This keeps data manageable and makes the world look richer without exploding the `TileKind` enum.

### 2. Add deterministic micro-variation

Every natural tile should pick a visual variant from a deterministic cell hash. For example, `Grass` can draw variant 0-5 while still saving as `grass`.

Use cases:

- grass color/speckle variants
- sand ripple variants
- dirt pebble variants
- wet sand edge variants
- water ripple animation offsets
- cave floor crack variants
- floor plank variants

This is the fastest path to a less flat world.

### 3. Add biome decorator passes

After the base map is generated, run decorator passes that place non-blocking flavor.

| Biome/area | Decor examples |
|---|---|
| coastal | shells, driftwood, sea grass, pebbles, foam |
| riverbanks | reeds, mud patches, flowers, small stones |
| temperate field | flowers, weeds, clover, light grass tufts |
| woods | mushrooms, fallen leaves, roots, saplings |
| highlands | exposed rock, scrub grass, moss, cliff cracks |
| caves | crystals, moss, water drips, ore glints, rubble |
| tavern interior | rugs, footprints, soot, floor wear, warm light pools |

### 4. Make water a system, not just a tile

The project needs all natural water to be fishable, visible rivers to flow, and boats/harbor travel later. Water should carry metadata.

Recommended fields:

```text
water_depth: none / puddle / shallow / deep / ocean
water_flow: none / north / east / south / west
fish_region: river / pond / coast / deep_sea / cave_pool
water_quality: clean / brackish / murky / magical / polluted
```

This lets fishing, visuals, crop watering, and river animation all read the same data.

### 5. Add shore and cliff post-processing

Generate height first, then derive tile identity.

Suggested pass order:

```text
height map -> water mask -> shore band -> cliff band -> biome mask -> paths -> zones -> decorators
```

Rules:

- below waterline = deep water
- just above waterline = wet sand / pebble shore
- higher coastal band = sand / grass
- large height delta between neighbors = cliff
- mountain center = rock/cliff/cave entrance bias
- water next to land = foam/ripple overlay

### 6. Rivers should be flow paths, not random vertical stripes

The current river/creek style is useful for prototyping, but the final system should create a source and carve downhill.

Good first version:

1. pick source near mountain/highlands
2. step toward lower height and nearest coast
3. widen at turns and lowlands
4. mark center as deep/shallow water
5. mark banks as wet sand/reeds/pebbles
6. assign flow direction per river cell

This makes every river useful for fishing, travel readability, and visual motion.

### 7. Add seasonal visual rules early

Seasons are a core gameplay pillar, so the renderer should accept a season now even before full crop calendars exist.

Season effects:

| Season | Visual changes |
|---|---|
| Spring | flowers, bright grass, rainy mud/wet soil |
| Summer | saturated grass, dry path dust, stronger water highlights |
| Autumn | leaf litter, golden grass, mushroom boost |
| Winter | snow overlay, frozen edges, muted grass, heated interior contrast |

Avoid duplicating every tile. Use palette/tint and overlays where possible.

### 8. Add region identity per island

Each island has unique crops, fish, cuisine, and visual identity. Give every scene/world region a `region_id` and `island_id` as soon as possible.

Use this to drive:

- crop availability
- fruit/vegetable spawns
- fish tables
- cuisine unlocks
- NPC/patron preferences
- import/export prices
- foliage colors
- shoreline style

### 9. Use preview/debug maps in the editor

Worldgen needs visible debug overlays:

- height
- moisture
- fertility
- biome
- fish region
- pathability
- zone type
- spawn density
- transition links
- dirty/generated/protected cells

This will prevent mystery bugs when generation starts getting more layered.

## Recommended worldgen pass stack

```text
1. Choose region/world graph node
2. Choose scene profile
3. Height field for the playable scene slice
4. Moisture field
5. Temperature/season field
6. Waterline and coastline within the scene, if the scene touches water
7. River/stream carve
8. Cliff/rock pass
9. Biome tile classification
10. Road/path carve toward transition rectangles
11. Tavern/farm/city reserved footprints at local scene scale
12. Soil/fertility pass
13. Decor spawn pass
14. Object/resource spawn pass
15. Transition placement
16. Validation
17. Save generated result or save only player edits
```

## What should be generated vs saved

| Data | Save? | Reason |
|---|---:|---|
| Seed/profile | yes | reproduces base world |
| Player edits | yes | construction/farming/mining changes |
| Placed objects | yes | persistence |
| Crops/soil/watered state | yes | gameplay state |
| Pure visual grass variants | no | derive from hash |
| Seasonal tint | no | derive from time/season |
| Static generated trees | optional | save if interactable/cuttable |
| Resource nodes | yes once discovered/mined | gameplay persistence |

Best practice: generate the base scene deterministically, then save only edits and persistent state deltas.
