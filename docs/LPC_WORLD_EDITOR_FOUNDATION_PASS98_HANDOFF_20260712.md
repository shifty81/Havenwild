# Havenwild Pass 98 — LPC World Editor Foundation

Pass 98 begins the project-wide environment and editor-overlay reset after the
Pass 97 authored replacement-role proof.

## World Editor workflow

The client overlay is now presented as the **Havenwild World Editor**. World
and LPC terrain are the leading workflow modes. Advanced height, blend,
transition-rule, gameplay-rule, and source-library tools remain available
without crowding the primary paint workflow.

The Terrain mode exposes only reviewed LPC semantic brushes:

- Grass
- Dirt
- Sand
- Wet Sand
- Pebble Shore
- Shallow Water
- Deep Water

Each button is marked `[LPC]`. Transition targets, foam, river mouths, ocean
aliases, zones, and other derived implementation details no longer appear as
ordinary terrain choices.

## Complete tile migration inventory

All 32 runtime `TileKind` values are classified as:

- LPC Production;
- LPC Mapping Required;
- Derived/System;
- Object/Overlay.

Legacy visuals remain readable in existing saves and runtime data, but are
hidden from the normal production palette until their LPC mapping passes.

The locked promotion sequence is:

1. paths, roads, mountain paths, and bridges;
2. fresh water, rivers, mouths, foam, and mud banks;
3. tilled/watered soil, crops, and greenhouse behavior;
4. cliffs, mountain rock, cave floors, and cave walls;
5. building floors and walls;
6. vegetation and seasonal overlays.

V112 requires every runtime tile to have exactly one migration status and
prevents unfinished or derived tiles from returning to the default palette.

## Universal autotiling contract

All 32 runtime tiles now declare one adjacency behavior. Semantic ground and
water materials resolve eight-neighbor boundaries. Roads, paths, bridges,
cliffs, cave floors/walls, interior floors/walls, farm ground, and modular
building pieces use same-family assembly roles: fills, edges, outer/inner
corners, end caps, straights, and junctions. Foam, river mouths, ocean aliases,
crops, and zones are derived overlays; tall grass remains an object/stamp.

Painting changes a semantic material, never an atlas coordinate. The edited
cell and its eight neighbors are re-resolved. Doors/openings remain explicit
authored stamps but participate in wall adjacency. Roof and trim families are
reserved for a later semantic catalog promotion once their LPC roles are
verified.

V113 locks this policy across exterior terrain, caves, interiors, and modular
building exteriors. Missing authored roles use a clean family fill rather than
synthetic, rotated, or guessed LPC pixels.

## Build

Extract the complete source rollup over the repository and run:

```bat
tools/build/Build.cmd all
```
