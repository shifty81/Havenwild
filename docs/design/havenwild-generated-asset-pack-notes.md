# Havenwild — Generated Development Asset Pack

This pack contains original placeholder/development assets for the current Havenwild direction. They are not copies of Stardew Valley, Travelers Rest, or any other game. They are grid-accurate prototype assets designed to support implementation.

## Files

```txt
assets/generated/havenwild_ground_tiles_32_v2.png
assets/generated/havenwild_ground_tiles_32_v2.json
assets/generated/havenwild_grid_action_overlays_32_v1.png
assets/generated/havenwild_grid_action_overlays_32_v1.json
assets/generated/havenwild_2p5d_objects_32x64_v1.png
assets/generated/havenwild_2p5d_objects_32x64_v1.json
assets/generated/havenwild_build_grid_preview.png
```

## Ground tile standard
- 32×32 pixels per tile.
- Tile snapping is exact.
- Base tiles carry gameplay identity.
- Visual variety should come from overlays and decor layers.

## Object standard
- Object sprites are 32×64 cells in this pack.
- The lower 32×32 region represents the ground footprint editor guide.
- Metadata defines the foot anchor and Y-sort origin.
- Larger final sprites can use 64×96 or 96×128 later, as long as they keep anchor metadata.

## Included object categories
- trees and forage
- rocks and ore
- tavern furniture
- kitchen/washing stations
- inn objects
- farm/build objects
- construction objects
- entertainment props

## Grid overlays
These support build mode and tools:
- valid placement
- blocked placement
- hoe preview
- water preview
- plant preview
- build footprint
- room footprint
- single/line/square/cross tool shapes
- construction tape/dust
- fishable water marker
- staff/manager/quest zones
