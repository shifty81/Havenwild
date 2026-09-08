# Havenwild Exact World Tile Spec v0.1

## Core Tile Standard

| Rule | Value |
|---|---|
| Base tile size | 32x32 pixels |
| Atlas coordinate unit | 32 pixels |
| Scene prototype size | 48x32 tiles for compact playable scenes, not whole-island maps |
| World structure | scene-based maps connected by transition rectangles |
| Interior structure | separate expandable scenes with dark/black void boundary |
| Recommended atlas grid | fixed columns + rows, never one-row atlas with mismatched manifest columns |
| Art direction | warm earth tones, readable cozy terrain, brighter color reserved for items/icons/highlights |

## Scene Scale Contract

The current 48x32 grid is a prototype/playable scene slice. It must not be treated as a full island satellite map.

Rules:

- A tavern, farm patch, road, cave mouth, dock, or greenhouse is a local feature inside a scene, not a scaled overlay over an island map.
- The starter tavern footprint should stay in the range of roughly 10-18 tiles wide and 7-12 tiles deep in a 48x32 prototype scene.
- A starter crop patch should occupy a small-to-medium local field area, not more than about 20% of the scene.
- Roads should be narrow path networks that connect transitions and buildings. They should not divide the map into huge bands unless the scene is explicitly a road connector.
- Island-scale shape belongs to the world graph or region map. It should be represented as multiple connected scenes, not squeezed into one 48x32 scene.
- Debug previews must label their source: imported concept, generated height/layer preview, active SceneMap render, or full region/world graph preview.

If a preview makes the tavern footprint look nearly the same size as the island, the preview is invalid for gameplay scale.

## Required Runtime Layers

Do not store everything as one tile enum. The world should be layered.

| Layer | Purpose | Example data |
|---|---|---|
| Height field | reusable generation source | 0-100 elevation values |
| Base terrain | visible ground/water/floor/wall tile | grass, sand, water, cliff |
| Autotile mask | resolves edge/corner variant | road/water/cliff/floor/wall masks |
| Overlay/stamp layer | small variation without changing base tile | flowers, pebbles, reeds, leaves |
| State layer | gameplay state | watered, fertilized, dirty, construction, snow |
| Object layer | placed objects | tree, door, bridge prop, ore node |
| Zone layer | gameplay zoning | tavern, kitchen, field, cave, staff-only |
| Transition layer | scene travel | target scene + spawn tile |

## Exact Height Bands

Use water level and mountain level as scene settings, then classify height values.

Default prototype values:

```txt
height: 0..100
water_level: 34
mountain_level: 72
```

| Height rule | Default tile | Notes |
|---|---|---|
| `height <= water_level - 10` | deep_water | deep sea/lake, boat/fishing depth |
| `height <= water_level - 3` | water | normal fishable water |
| `height <= water_level` | shallow_water | visible edge water, near shore |
| `height <= water_level + 4` | wet_sand / mud / pebble_shore | biome-specific waterline |
| `height <= water_level + 10` | sand / dirt / pebble_shore | beach/shore band |
| `height < mountain_level` | grass/dirt/tall_grass | land body |
| `height >= mountain_level` | cliff | steep transition |
| `height >= mountain_level + 10` | mountain_rock | hard blocker |

Biome overrides:

| Biome | Waterline | Shore | Upland | Mountain |
|---|---|---|---|---|
| Temperate | mud/dirt | grass/dirt | grass/tall_grass | cliff/mountain_rock |
| Coastal | wet_sand | sand/pebble_shore | grass/tall_grass | cliff |
| Highlands | pebble_shore | mountain_path/pebbles | tall_grass/mountain_path | mountain_rock |
| Cave | cave_water | cave_floor | cave_floor/ore_floor | cave_wall |
| Farm | mud | dirt/rich_soil | grass/tilled_soil | usually none |

## Exact Code-Compatible Tile List

The replacement `prototype_terrain_tiles.png/json` has 25 tiles in the current clean source `TileKind::ALL` order.

| Index | ID | Category | Walkable | Buildable | Fertile | Liquid | Fishable | Autotile Group | Height Band |
|---:|---|---|---:|---:|---:|---:|---:|---|---|
| 0 | grass | terrain | yes | yes | no | no | no | grass | land |
| 1 | tall_grass | terrain | yes | yes | no | no | no | grass | land |
| 2 | sand | terrain | yes | yes | no | no | no | shore | beach |
| 3 | wet_sand | terrain | yes | no | no | no | no | shore | waterline |
| 4 | pebble_shore | terrain | yes | yes | no | no | no | shore | shore |
| 5 | road | terrain | yes | yes | no | no | no | road | land |
| 6 | stone_path | terrain | yes | yes | no | no | no | road | land |
| 7 | mountain_path | terrain | yes | yes | no | no | no | road | slope |
| 8 | wood_floor | interior_floor | yes | yes | no | no | no | wood_floor | interior |
| 9 | plank_floor | interior_floor | yes | yes | no | no | no | wood_floor | interior |
| 10 | stone_floor | interior_floor | yes | yes | no | no | no | stone_floor | interior |
| 11 | brick_floor | interior_floor | yes | yes | no | no | no | stone_floor | interior |
| 12 | wall | wall | no | no | no | no | no | wall | blocked |
| 13 | cliff | wall | no | no | no | no | no | cliff | cliff |
| 14 | mountain_rock | wall | no | no | no | no | no | cliff | mountain |
| 15 | dirt | terrain | yes | yes | yes | no | no | dirt | land |
| 16 | bridge | terrain | yes | yes | no | no | no | road | over_water |
| 17 | cave_floor | cave | yes | yes | no | no | no | cave_floor | cave_floor |
| 18 | cave_wall | cave | no | no | no | no | no | cave_wall | cave_wall |
| 19 | tilled_soil | farm | yes | no | yes | no | no | farm_soil | field |
| 20 | crop | farm | yes | no | yes | no | no | crop | field |
| 21 | greenhouse_zone | farm | yes | no | yes | no | no | greenhouse | field |
| 22 | water | water | no | no | no | yes | yes | water | water |
| 23 | shallow_water | water | no | no | no | yes | yes | water | shallow_water |
| 24 | deep_water | water | no | no | no | yes | yes | water | deep_water |

## Required Tile Families For Real World Generation

### Land

- grass
- grass variants
- tall grass
- flowers/clover/herb overlays
- autumn/snow variants or seasonal overlay

### Soil/Farm

- dirt
- tilled soil
- watered soil state overlay
- rich/composted soil state overlay
- crop stage overlay
- mud/rain state overlay

### Coast/Water

- deep water
- water
- shallow water
- river water
- river foam/current overlay
- wet sand
- sand
- pebble shore
- reed bank overlay

### Roads/Paths

- dirt road
- stone path
- cobble path
- mountain path
- bridge
- snow/mud path overlays

### Cliffs/Mountains

- cliff face
- cliff top
- mountain rock
- mountain path
- cave entrance frame object/stamp

### Caves

- cave floor
- cave wall
- cave water
- ore floor overlay/stamp
- lava crack late-game/hazard placeholder

### Interiors

- wood floor
- plank floor
- stone floor
- brick/kitchen floor
- cellar floor
- wall
- interior void/dark boundary

## Exact Autotile Groups

| Group | Members | Needs variants |
|---|---|---|
| water | shallow_water, water, deep_water, river_water, cave_water | edge, corner, inner corner, isolated, full |
| shore | wet_sand, sand, pebble_shore, mud | edge blends against water/grass |
| road | road, dirt_road, stone_path, cobble_path, mountain_path, bridge | line, corner, T, cross, endcap |
| grass | grass, tall_grass, meadow_grass | soft variation only; no hard edges needed early |
| farm_soil | tilled_soil, tilled_soil_watered, rich_soil | field joins and furrow direction |
| cliff | cliff, mountain_rock, cliff_top | face, top, corner, blocker edge |
| cave_wall | cave_wall | cave room boundaries |
| wood_floor | wood_floor, plank_floor | room flooring edges |
| stone_floor | stone_floor, brick_floor, cellar_floor | room/cellar flooring edges |
| wall | wall | interior room boundary |

## Exact State Layers To Add Next

These should be saved per tile, but not necessarily as base tiles.

| State | Type | Purpose |
|---|---|---|
| watered_today | bool | crop growth |
| soil_quality | 0-100 | yield/quality |
| fertilized | enum/level | crop output modifier |
| crop_id | optional string | crop identity |
| crop_growth_stage | integer | growth sprite overlay |
| seasonal_variant | enum | spring/summer/autumn/winter presentation |
| snow_depth | 0-3 | winter overlay |
| cleanliness | 0-100 | tavern/interior dirt |
| construction_state | enum | planned/taped/active/complete |
| room_id | optional id | room simulation hooks |
| fish_habitat | enum | river/coast/lake/deep/cave |
| current_direction | enum | river visual and fishing behavior |

## Replacement Files In This Pack

| File | Purpose |
|---|---|
| `assets/generated/prototype_terrain_tiles.png` | Drop-in code-compatible 25-tile replacement atlas |
| `assets/generated/prototype_terrain_tiles.json` | Exact metadata for current code-compatible tiles |
| `assets/generated/havenwild_world_tiles_expanded_v1.png` | Forward-looking 48-tile worldgen atlas |
| `assets/generated/havenwild_world_tiles_expanded_v1.json` | Expanded metadata for future data-driven tile pipeline |
| `content/worldgen/biome_presets.json` | Biome/worldgen presets for starter island, harbor, caves, farms, interiors |
| `content/worldgen/tile_transition_rules.json` | Height bands, autotile mask, transitions, state-layer rules |
| `tools/automation/worldgen/Generate-HavenwildWorldTiles.py` | Reproducible generator for the replacement placeholder tiles |

## Direct Integration Rule

For now, replace only the generated prototype atlas/manifest and add the new worldgen metadata files. Do not immediately explode `TileKind` to 48+ variants. Load metadata first, then add state layers and autotile variant resolution.
