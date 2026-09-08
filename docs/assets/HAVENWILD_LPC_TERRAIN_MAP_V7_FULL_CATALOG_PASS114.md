# Havenwild LPC Terrain Map V7 Full Catalog - Pass114

This report is generated from `content/assets/lpc/source/lpc-terrains-v7/terrain-map-v7.tsx`.
The generator now catalogs the full Tiled terrain tuple set, including terrain types that do not yet have Havenwild editor brush IDs.

- Terrain types: 34
- Unique cataloged corner tuples: 15562
- Pure fill tuples present: 34

## Runtime Intake Policy

- The Tiled terrain catalog is now the primary LPC runtime terrain source for mapped families.
- Havenwild still stores `TileKind` cells, and the runtime resolver derives Tiled corner tuples from neighboring cells.
- Older neighboring transition overlays are suppressed where a mapped LPC terrain cell owns the visible boundary.
- Single-cell shapes that cannot be expressed by four-corner tuples remain native fallback masks.

## Current Havenwild TileKind Aliases

| Tile/editor material | Tiled terrain |
|---|---|
| `grass` | `Grass` |
| `dirt` | `Dirt_Brown` |
| `sand` | `Sand` |
| `shallow_water` | `Water_Shallows_Sand` |
| `deep_water` | `Water_Deep` |
| `water` | `Water` |
| `river_water` | `Water` |
| `ocean_shallow` | `Water_Shallows_Sand` |
| `ocean_deep` | `Water_Deep` |

## Full Tiled Terrain Types

| # | Terrain | Catalog tuples using it | Pure fill exported | Status |
|---:|---|---:|---|---|
| 0 | `Dirt_Brown` | 3039 | yes | promoted runtime TileKind terrain |
| 1 | `Dirt_Dark` | 1219 | yes | cataloged, pending Havenwild material |
| 2 | `Dirt_Roots` | 4325 | yes | cataloged, pending Havenwild material |
| 3 | `Dirt_Tan` | 5121 | yes | cataloged, pending Havenwild material |
| 4 | `Earth_Cracked` | 175 | yes | cataloged, pending Havenwild material |
| 5 | `Grass` | 3423 | yes | promoted runtime TileKind terrain |
| 6 | `Grass_Dark` | 4353 | yes | cataloged, pending Havenwild material |
| 7 | `Grass_Dead` | 369 | yes | cataloged, pending Havenwild material |
| 8 | `Grass_Light` | 1 | yes | cataloged, pending Havenwild material |
| 9 | `Gravel_1` | 1473 | yes | cataloged, pending Havenwild material |
| 10 | `Hole_Black` | 57 | yes | cataloged, pending Havenwild material |
| 11 | `Hole_Brown` | 43 | yes | cataloged, pending Havenwild material |
| 12 | `Ice` | 369 | yes | cataloged, pending Havenwild material |
| 13 | `Ice_Melting` | 15 | yes | cataloged, pending Havenwild material |
| 14 | `Lava` | 369 | yes | cataloged, pending Havenwild material |
| 15 | `Mud_Brown` | 4325 | yes | cataloged, pending Havenwild material |
| 16 | `Mudstone_Brown` | 3395 | yes | cataloged, pending Havenwild material |
| 17 | `Mudstone_Gray` | 3395 | yes | cataloged, pending Havenwild material |
| 18 | `Rock_Black` | 687 | yes | cataloged, pending Havenwild material |
| 19 | `Rock_Dark` | 1777 | yes | cataloged, pending Havenwild material |
| 20 | `Rock_Gray` | 1777 | yes | cataloged, pending Havenwild material |
| 21 | `Rock_White` | 1105 | yes | cataloged, pending Havenwild material |
| 22 | `Sand` | 1075 | yes | promoted runtime TileKind terrain |
| 23 | `Snow_1` | 383 | yes | cataloged, pending Havenwild material |
| 24 | `Snow_2` | 369 | yes | cataloged, pending Havenwild material |
| 25 | `Soil` | 65 | yes | cataloged, pending Havenwild material |
| 26 | `Stone_Tan` | 2625 | yes | cataloged, pending Havenwild material |
| 27 | `Stone_White` | 2465 | yes | cataloged, pending Havenwild material |
| 28 | `Water` | 1695 | yes | promoted runtime TileKind terrain |
| 29 | `Water_Deep` | 175 | yes | promoted runtime TileKind terrain |
| 30 | `Water_Green` | 65 | yes | cataloged, pending Havenwild material |
| 31 | `Water_Purple` | 65 | yes | cataloged, pending Havenwild material |
| 32 | `Water_Shallows_Dirt` | 671 | yes | cataloged, pending Havenwild material |
| 33 | `Water_Shallows_Sand` | 65 | yes | promoted runtime TileKind terrain |

## Native Editor Material Catalog

`content\assets\lpc\lpc_tiled_terrain_material_catalog_v0_1.json` contains one generic terrain material record for every Tiled terrain type.
`paintableNow: true` records are backed by Havenwild TileKind terrain storage and the runtime LPC mapped atlas.
