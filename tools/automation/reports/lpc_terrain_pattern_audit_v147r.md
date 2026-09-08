# LPC Terrain Pattern Audit — Pass 147R

- mapped entries: **5127**
- unique corner signatures: **213**
- live autotile groups: **road, wood_floor, stone_floor, water, wall, cliff, cave_wall**

## Identity collisions

- StonePath collapses into PebblePath
- MountainPath and Bridge collapse into Road

## Missing distinct path groups

- stone_path
- mountain_path
- bridge

## Topology inventory

- `diagonal_split`: 116
- `edge`: 232
- `fill`: 55
- `inner_corner`: 348
- `junction_3_material`: 2700
- `junction_4_material`: 1560
- `outer_corner`: 116
