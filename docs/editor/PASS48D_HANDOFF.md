# Havenwild Pass 48D — Transactional Undo and Gesture Coalescing

## Purpose

Pass 48D replaces full-world serialized snapshots as the native editor's primary undo/redo implementation. It preserves snapshot history only as a compatibility path for the in-game developer overlay while later runtime-editor migration remains pending.

## Implemented

- Added executable, reversible `EditTransaction` and `EditOperation` history in `haven_authoring`.
- Added typed operations for tile, zone, object, and transition authoring.
- Object and transition insert/remove history stores the complete authored entity and its stable ID.
- Undo reverts operations in reverse order; redo applies them in forward order.
- Strict expected-state checks reject replay against unexpectedly modified data.
- Failed transaction replay restores the pre-replay world clone atomically.
- Added mixed history support for typed transactions and legacy snapshots.
- Added `begin_gesture`, `record_transaction`, `commit_gesture`, and `cancel_gesture` lifecycle APIs.
- Repeated tile, zone, object-move, and transition-resize changes coalesce within a gesture.
- Native Scene Map paint and erase drags now create one undo entry per pointer gesture.
- `Escape` reverts an uncommitted paint/erase gesture.
- `Ctrl+Z` uses transaction-aware undo.
- `Ctrl+Y` and `Ctrl+Shift+Z` use transaction-aware redo.
- Tool, layer, scene, and workspace changes safely commit any open gesture.
- Removed per-edit `GameWorld::serialize_lines()` calls from `haven_editor::scene_edit`.
- Added editor history status for total undo, typed undo, redo, and active gesture operation counts.

## Compatibility boundary

The in-game developer overlay still records serialized snapshots through `capture_undo_snapshot`. The native editor uses `undo_world` and `redo_world`, which can replay both history formats. A later pass can migrate runtime overlay commands and then remove the snapshot-only API.

## Main files

```text
crates/haven_authoring/src/transactions.rs
crates/haven_authoring/src/command_bus.rs
crates/haven_editor/src/scene_edit.rs
crates/haven_editor/src/scene_edit_tests.rs
apps/haven_editor_native/src/app/input.rs
apps/haven_editor_native/src/app/scene_authoring.rs
content/editor/transactions/transactional_undo_contract_v0_1.json
docs/editor/TRANSACTIONAL_UNDO_PASS48D.md
tools/automation/validation/checks/misc/Validate-TransactionalUndoV61.py
```

## Validation performed in this environment

- Full Havenwild validation registry: passed.
- Architecture scan: 104 Rust files.
- Content validation: 170 canonical JSON files.
- Tree-sitter Rust syntax parse: 104 files.
- Python syntax: 72 scripts.
- JSON parse: 177 files.
- TOML parse: 13 files.
- Web editor JavaScript syntax: passed.
- ZIP integrity: checked after packaging.

Cargo, Rustc, and Rustfmt are not installed in this execution environment. Run the following on the Windows development machine before merging:

```powershell
.\tools/build/Build.cmd check
.\tools/build/Build.cmd test
.\tools/build/Build.cmd editor
```

## Expected native editor verification

1. Open the Scene Map workspace.
2. Select Terrain and Paint.
3. Hold the left mouse button and paint across multiple cells.
4. Release the button; the history display should show one typed undo entry.
5. Press `Ctrl+Z`; the entire stroke should revert.
6. Press `Ctrl+Y`; the entire stroke should return.
7. Start another stroke and press `Escape` before releasing; the unfinished stroke should be reverted without adding an undo entry.
8. Repeat with Erase and with an object place/remove operation.

## Next pass

Pass 49 should implement the first complete infinite-canvas authoring toolset on this transaction foundation:

- marquee and additive selection;
- multi-item movement;
- rectangle paint;
- flood fill;
- replace and eyedropper;
- copy, cut, paste, duplicate, and delete;
- a real visibility/lock/opacity layer stack;
- frame selection and persistent per-scene canvas state.
