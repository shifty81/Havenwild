# LPC Tuple Promotion Plan - Pass 134

This plan ranks terrain-v7 fallback tuples that should be converted into exact authored tuple art.

| Category | Fallback Patterns |
|---|---:|
| `advanced_water_shore` | 322 |
| `advanced_land_edge` | 171 |
| `production_water_shore` | 84 |
| `advanced_water_land` | 56 |
| `water_depth` | 28 |
| `production_land_edge` | 28 |

## Top Promotion Rows

| Priority | Pair | Category | Exact | Fallback | Fallback Materials |
|---:|---|---|---:|---:|---|
| 1310 | `Sand__Water_Deep` | `production_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 1270 | `Grass__Water_Deep` | `production_water_shore` | 2 | 14 | `Water` |
| 1270 | `Water_Deep__Water_Shallows_Sand` | `production_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 1270 | `Water_Shallows_Sand__Water_Deep` | `production_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 1220 | `Water__Mudstone_Brown` | `production_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 1220 | `Mudstone_Brown__Water` | `production_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 1120 | `Water_Deep__Water_Shallows_Dirt` | `water_depth` | 2 | 14 | `Water_Shallows_Dirt` |
| 1070 | `Water_Shallows_Sand__Water_Shallows_Dirt` | `water_depth` | 2 | 14 | `Water_Shallows_Sand` |
| 960 | `Sand__Dirt_Roots` | `production_land_edge` | 2 | 14 | `Dirt_Roots, Sand` |
| 920 | `Dirt_Brown__Stone_Tan` | `production_land_edge` | 2 | 14 | `Dirt_Brown, Stone_Tan` |
| 770 | `Stone_Tan__Water_Deep` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 770 | `Dirt_Roots__Water_Deep` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 770 | `Mudstone_Brown__Water_Deep` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 770 | `Mud_Brown__Water_Deep` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 760 | `Sand__Water_Shallows_Dirt` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 720 | `Grass__Water_Shallows_Sand` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 720 | `Grass_Dark__Water_Shallows_Sand` | `advanced_water_shore` | 1 | 14 | `Water_Shallows_Sand` |
| 720 | `Grass_Dark__Water_Shallows_Dirt` | `advanced_water_shore` | 1 | 14 | `Water_Shallows_Dirt` |
| 720 | `Dirt_Brown__Water_Shallows_Sand` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 720 | `Stone_Tan__Water_Shallows_Sand` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 720 | `Stone_Tan__Water` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 720 | `Stone_Tan__Water_Shallows_Dirt` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Dirt` |
| 720 | `Dirt_Tan__Water_Shallows_Sand` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Sand` |
| 720 | `Dirt_Roots__Water_Shallows_Sand` | `advanced_water_shore` | 2 | 14 | `Water_Shallows_Sand` |

## Outputs

- JSON: `content\assets\lpc\lpc_tuple_promotion_plan_v0_1.json`
- Preview: `docs\assets\previews\havenwild_lpc_tuple_promotion_plan_pass134.png`
