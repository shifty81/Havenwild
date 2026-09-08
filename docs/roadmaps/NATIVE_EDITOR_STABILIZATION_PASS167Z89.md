# Havenwild Native Editor Stabilization — Pass167Z89

## Purpose

Pass167Z89 makes the native editor a stable application shell before the next world-authoring features are added. It does not replace existing World Surface, Scene Bank, Scene Editor, Pixel Studio, Animation Studio, or Character Studio implementations. It places them inside one persistent workspace contract.

## Shell layout

The editor now uses two fixed top rows: a menu row and a document row. The left Project/Assets panel, center authoring canvas, right Inspector, bottom status bar, and optional bottom dock use one shared layout calculation.

The bottom dock overlays the lower portion of the authoring canvas. Opening Validation or Console therefore does not change the camera viewport dimensions or cause the canvas to jump. The user can hide Project or Inspector panels independently to maximize the canvas. Project, Inspector, and bottom-dock splitters can also be dragged; normalized dimensions are written to the same machine-local layout file.

Machine-local layout state is saved to:

```text
WORKSPACE/editor/native_workspace_layout_v0_1.json
```

This file stores UI preferences only. It is not game content, world-save authority, or multiplayer state.

## Bottom panels

- **Console:** recent native-editor command history.
- **Validation:** the active shared editor validation report.
- **Imports:** asset-browser, promotion palette, and intake status.
- **Build:** current editor validation state and the authoritative Windows Build All path.
- **Tasks:** the active native-editor production lane.

## Status authority

The fixed status bar shows the current operation message, validation state, saved/modified state, undo/redo depth, and a bottom-panel toggle. Pixel and animation document dirty flags remain authoritative for their documents. World-authoring dirty state is measured against the command-history depth recorded by the last successful Save All or Reload Saved action.

## Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+J | Toggle bottom panels |
| Ctrl+Shift+L | Toggle Project panel |
| Ctrl+Shift+I | Toggle Inspector |
| Ctrl+S or F5 | Save all editor documents |
| Ctrl+Z / Ctrl+Y | Undo / redo |
| Tab | Cycle authoring documents |

## Build repair

The strict-Clippy `items_after_test_module` failure in `runtime_surface_streaming.rs` is repaired by moving `surface_maintenance_tests` after all production `impl Game` items. No lint suppression is added.

## Next passes

1. Promote World Surface into the continuous Alderreach global editing canvas.
2. Unify selection and Inspector behavior across terrain, elevation, roads, structures, objects, zones, and stamps.
3. Complete the semantic asset browser and promotion-review workflow.
4. Add elevation sculpting with live cliff, ramp, ladder, bridge, cave, and waterfall previews.
5. Build PCG Studio preview/diff/commit workflows.
6. Complete Sprite/Pixel and animation publishing.
7. Add Play From Here and local live reload.
