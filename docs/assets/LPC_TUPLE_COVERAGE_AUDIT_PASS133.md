# LPC Tuple Coverage Audit - Pass 133

This audit enumerates 16 binary 4-corner tuple patterns for every current terrain material pair.

- Exact tuples: 753
- Terrain-v7 fallback tuples: 689
- Missing tuples: 94

Fallback is acceptable as a temporary safety net because it keeps rendering inside terrain-v7 and suppresses stale legacy atlas draw. Production polish still means converting high-frequency fallback pairs into exact authored tuple art.

## Highest Fallback Pairs

| Pair | Fallback Patterns |
|---|---:|
| `Sand__Water_Deep` | 14 |
| `Grass__Water_Deep` | 14 |
| `Water_Deep__Water_Shallows_Sand` | 14 |
| `Sand__Dirt_Roots` | 14 |
| `Dirt_Brown__Stone_Tan` | 14 |
| `Water__Mudstone_Brown` | 14 |
| `Grass__Water_Shallows_Sand` | 14 |
| `Grass_Dark__Water_Shallows_Sand` | 14 |
| `Grass_Dark__Water_Deep` | 14 |
| `Grass_Dark__Water` | 14 |
| `Grass_Dark__Water_Shallows_Dirt` | 14 |
| `Dirt_Brown__Mudstone_Brown` | 14 |

## Outputs

- JSON: `content\assets\lpc\lpc_tuple_coverage_audit_v0_1.json`
- Preview: `docs\assets\previews\havenwild_lpc_tuple_coverage_pass133.png`
