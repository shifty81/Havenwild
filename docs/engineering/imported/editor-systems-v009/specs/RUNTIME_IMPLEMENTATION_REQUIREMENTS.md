# Runtime Implementation Requirements

## Runtime must support

```text
semantic terrain maps
V005 compositor output
V006 object/fringe/overhead layers
V008 scene rectangles
scene streaming
in-game editor overlay
runtime command application
dirty-cell recomposition
collision rebuild
save/load
```

## Runtime layers

```text
00 deep water
01 mid water
02 shallow water
03 water animation / foam
04 wet shore band
05 dry bank / terrain material
06 base ground
07 terrain overlays
08 roads / paths
09 detail decals
10 cliff/ledge shadows
11 floor objects
12 fringe objects, Y-sorted
13 characters/NPCs, Y-sorted
14 overhead/roof/canopy
15 occlusion/fade masks
16 editor overlays
```

## Runtime systems

```text
SceneStreamingSystem
TerrainCompositorSystem
DirtyTileRebuildSystem
ObjectPlacementSystem
CollisionRebuildSystem
YSortSystem
OcclusionFadeSystem
InteractionProbeSystem
BuildValidationSystem
SaveLoadSystem
RuntimeEditorBridge
```

## Dirty rebuild rule

When terrain or objects change:

```text
mark affected cells dirty
expand dirty area by one tile for masks
recompute terrain masks
recompose visual tiles
rebuild collision/interaction
refresh pathfinding if needed
refresh water/fishing regions if needed
save dirty scene state
```

## Performance rule

Large scenes should not recompose all terrain every edit.

Use:

```text
dirty rects
chunk cache
per-layer invalidation
lazy rebuild
background bake where safe
```
