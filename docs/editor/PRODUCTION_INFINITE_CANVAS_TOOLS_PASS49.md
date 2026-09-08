# Havenwild Pass 49 — Production Infinite-Canvas Tools

Pass 49 turns the permanent Scene Map viewport into a practical GameMaker/Tiled-style authoring surface. It builds on stable entity IDs and typed transactions from Passes 48C–48D.

## Tool set

The tool rail exposes nine explicit tools in a fixed 3×3 grid:

1. Select
2. Paint
3. Rectangle
4. Fill
5. Replace
6. Pick/Eyedropper
7. Place
8. Erase
9. Pan

Keyboard shortcuts `1` through `9` select the matching tool. `F1` through `F4` select Terrain, Objects, Zones, and Transitions.

## Selection and movement

- Select-click resolves through the shared layer-aware canvas hit-test contract.
- Dragging empty canvas creates a snapped marquee.
- Holding Shift adds or toggles selection.
- Dragging selected content moves it as one typed transaction.
- Object and transition selection uses stable IDs, not vector indexes.
- Terrain and zone selections retain exact selected cells.
- `Shift+F` frames the current selection.

## Bulk tools

- Rectangle paints terrain or zones inside a snapped rectangle.
- Fill performs a four-neighbor flood fill.
- Replace changes every matching terrain/zone value sampled under the pointer.
- Eyedropper samples terrain, zone, object, or transition content.
- All bulk operations generate one reversible typed transaction.

## Clipboard

- `Ctrl+C`: copy selection
- `Ctrl+X`: cut selection
- `Ctrl+V`: paste at the current cursor cell
- `Ctrl+D`: duplicate one cell down/right
- `Delete` or `Backspace`: delete the current selection

Clipboard coordinates are relative to the selection bounds. Pasted objects and transitions receive new stable IDs. Invalid or out-of-bounds pastes restore the world atomically.

## Layers

Terrain, Objects, Zones, and Transitions each expose:

- active-layer selection;
- visibility toggle;
- edit lock;
- opacity adjustment.

Hidden layers do not render. Locked layers reject authoring operations while remaining inspectable.

## Canvas behavior

- The map remains inside its clipped permanent viewport.
- Wheel zoom is cursor-centered.
- Middle-drag, Space+drag, and the Pan tool move the camera.
- Camera position and zoom are remembered independently for each scene during the editor session.
- `F` frames the scene and `Shift+F` frames selection.
- The 1×1 minor grid and 8×8 major guides use the same transform as rendering, selection, and placement.

## Architecture

Headless authoring behavior lives in:

- `crates/haven_editor/src/bulk_edit.rs`
- `crates/haven_editor/src/scene_clipboard.rs`

Native input and visualization live in:

- `apps/haven_editor_native/src/app/production_tools.rs`
- `apps/haven_editor_native/src/app/canvas_tool_rack.rs`
- `apps/haven_editor_native/src/app/render_helpers.rs`

This keeps bulk edits reusable by the future developer overlay and automation layer without depending on Macroquad.
