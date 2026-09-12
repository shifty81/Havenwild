# LPC Terrain Pattern Audit — Pass 147R

- mapped entries: **3453**
- unique corner signatures: **149**
- live autotile groups: **road, wood_floor, stone_floor, water, wall, cliff, cave_wall**

## Identity collisions

- StonePath collapses into PebblePath
- MountainPath and Bridge collapse into Road

## Missing distinct path groups

- stone_path
- mountain_path
- bridge

## Topology inventory

- `diagonal_split`: 96
- `edge`: 192
- `fill`: 57
- `inner_corner`: 288
- `junction_3_material`: 1980
- `junction_4_material`: 744
- `outer_corner`: 96
