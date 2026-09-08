# Havenwild — 2.5D Non-Isometric Grid Implementation Spec v0.1

## Decision
Use an **orthogonal 32×32 tile grid** with **2.5D sprite presentation**.

This means the gameplay grid is not isometric. The player, build mode, planting, digging, hoeing, watering, room placement, and object placement all target integer 32×32 tiles. Depth comes from taller sprites, bottom-foot anchors, Y-sorted render order, shadows, wall cutaways, object overhangs, and layered overlays.

## Why this fits the project
Havenwild needs a Stardew-like farm grid and a Travelers Rest-like tavern interior/business grid. The correct blend is:

- Stardew-style exact ground targeting for hoeing, watering, planting, digging, pathing, and crops.
- Tavern-life room/build placement with rectangular footprints and clear valid/blocked previews.
- Taller 2.5D objects for cozy visual depth: trees, counters, kegs, beds, fireplaces, doors, stage props, lamps, construction scaffolds.
- Scene-based interiors with void/backdrop support.
- No diagonal/isometric coordinate math.

## Rendering stack
1. Void/background
2. Base ground tile layer
3. Terrain variant overlay
4. Seasonal overlay
5. Soil/crop state overlay
6. Water animation overlay
7. Floor wear/decor overlay
8. Back object layer
9. Y-sorted actors and props
10. Front object/overhang layer
11. Roof/cutaway layer
12. Tool preview/build grid layer
13. UI

## Sort rule
Every tall object has a foot anchor. The foot anchor snaps to the center/bottom of a 32×32 tile. The renderer sorts Y-sorted sprites by:

```txt
layer_order, foot_anchor_screen_y, foot_anchor_screen_x, stable_id
```

Do not sort by sprite image top-left. A 32×64 tree should sort by the trunk/base tile, not by its leaf canopy.

## Grid action rules
All tool actions use grid footprints:

| Action | Grid Rule |
|---|---|
| Hoe | single tile early; upgraded line/area later |
| Water | single tile early; upgraded line/area later |
| Dig | single tile or small area |
| Plant | prepared soil tile only |
| Build | rectangular footprint with collision/path validation |
| Place furniture/object | footprint tiles + Y-sort anchor |

## Non-isometric camera
Use a normal orthographic top-down camera. The art can show object fronts and vertical faces, but the map remains orthogonal.

```txt
screen_x = tile_x * 32 - camera_x
screen_y = tile_y * 32 - camera_y
```

## Build mode snap
Build mode should never allow sub-tile placement for core gameplay objects. Decorative objects can later support half-tile offsets, but only if their collision footprint still resolves to tile cells.

## Required metadata for every object sprite
```json
{
  "name": "bar_counter",
  "sprite_cell": "32x64",
  "foot_anchor_px": { "x": 16, "y": 56 },
  "sort_origin_px": { "x": 16, "y": 56 },
  "footprint_tiles": { "w": 2, "h": 1 },
  "snap": "bottom_center_to_tile_center"
}
```

## Worldgen rules for this style
Worldgen should emit base tile identity plus side layers:

- height
- moisture
- fertility
- water flow
- decor overlay
- seasonal overlay
- crop/soil state
- object placement
- zones
- transitions

Avoid exploding the base tile enum into every visual variant. Example: use `grass + flower_overlay + spring_season`, not `spring_flowered_grass_tile_12`.

## Implementation path
1. Add `grid_2p5d.rs` module.
2. Add the render contract JSON.
3. Add overlay/tool preview atlas.
4. Add object metadata for anchor/footprint sorting.
5. Update editor/build mode to draw valid/blocked tile previews.
6. Update renderer sorting for actors/props.
7. Add soil/crop state layer separate from base tile enum.
8. Add water-flow metadata for rivers/fishing.
