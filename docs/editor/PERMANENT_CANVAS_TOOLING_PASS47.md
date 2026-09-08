# Permanent Canvas Tooling — Pass 47

## Problem closed

The prior native editor treated zoom as a raw multiplier applied directly to scene rectangles. At high zoom, rectangle fills and thumbnails were drawn outside the intended world area and over the docked editor UI. The scene-map rail also exposed layers and content brushes without a clearly separated tool-selection stage, which made object placement appear to require the undocumented `2` shortcut.

## New canvas contract

Scene Map and Scene Rectangles now use persistent per-workspace `CanvasCameraState` values:

- zoom is canvas-local;
- pan is canvas-local;
- zoom is centered on the mouse pointer;
- camera rendering is clipped through Macroquad's `Camera2D.viewport`;
- docked UI is always rendered in default screen space;
- switching editor workspaces does not discard each canvas view;
- `F` frames the active canvas;
- middle-drag and `Space` + left-drag provide temporary pan.

The Pass 47 camera and canvas implementations were moved without behavior changes in Pass 48A. They now live in `apps/haven_editor_native/src/app/canvas_camera.rs` and `apps/haven_editor_native/src/app/canvas_view.rs`, while headless editing services remain in `crates/haven_editor`.

## Explicit Scene Map tools

The Scene Map tool rail now has a dedicated first stage:

1. Select
2. Paint
3. Place
4. Erase
5. Pan

Layer and content selection are separate stages. Terrain and zone brushes activate Paint automatically. Object and transition brushes activate Place automatically. Selecting `Table` and clicking the map therefore places a table immediately; pressing `2` is no longer required.

Keyboard compatibility remains:

- `1` Select
- `2` layer-appropriate Paint or Place
- `3` Erase
- `4` Pan
- `F1`–`F4` layer selection
- `Q` / `E` brush cycling
- `Enter` apply
- `Ctrl+Z` undo

`Space` is reserved for temporary canvas pan and no longer doubles as Apply.

## Grid and infinite-canvas behavior

Scene Map:

- visible 1x1 cell grid over the actual map;
- major guide every 8 cells;
- painting and object placement use camera-derived world coordinates and floor to the canonical tile cell;
- Paint and Erase support drag authoring without reapplying repeatedly to the same cell.

Scene Rectangles:

- every exterior scene renders as one uniform 96x96 editor cell;
- landmass groups retain their authored relative placement but are normalized to the common editor grid;
- scene selection uses the same world-space grid geometry used for rendering;
- Select and Pan are explicit canvas tools;
- the off-world scene bank is a fixed dock and never scales with the canvas.

## Validation and incidental repair

`Validate-PermanentCanvasToolingV57` locks the camera, clipping, explicit tools, automatic Paint/Place activation, grid normalization, and fixed scene-bank contracts. The pass also repairs the malformed newline literal in `tools/automation/worldgen/Generate-HomeIslandScenes.py`, allowing the repository Python scripts to pass syntax compilation again.

## Follow-on work

This pass intentionally establishes the viewport and input contract before arbitrary scene creation and drag-repositioning. The next scene-registry pass can add create/delete/duplicate scene commands and snapped scene-cell dragging without rebuilding camera, clipping, hit-testing, or tool-selection behavior again.
