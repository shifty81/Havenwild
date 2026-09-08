# First Island Generation and Larger Scene Plan

This pass adds the first formal generation profile for the main Havenwild island.

## Target

- Canonical tile: 32x32
- Current prototype scene size: 48x32
- Target larger scene size: 96x64
- First island overworld canvas: 384x256 tiles
- Player-facing zoom target: 1.18x

## Direction

The first island should be generated as a whole editable overworld canvas, then split into large exterior scene rectangles. Scene rectangles render their actual `SceneMap` contents on the world canvas. Interiors and caves are not placed directly on the outdoor terrain; they live in the off-world scene bank and connect by transitions.

## Generation passes

1. Height noise
2. Island contour
3. Shoreline bands
4. Mountain core
5. Road skeleton
6. Scene rectangle assignment
7. Transition link seeding
8. Ghost border seeding
9. Validation

## Runtime note

The scene size constants are not changed in this pass because save/load and many editors still assume fixed `MAP_W` and `MAP_H`. The new profile records the target migration so the resize happens intentionally instead of breaking existing saves.
