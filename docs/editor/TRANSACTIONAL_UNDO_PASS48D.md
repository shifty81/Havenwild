# Havenwild Pass 48D — Transactional Undo and Gesture Coalescing

Pass 48D replaces full-world serialized snapshots as the native editor's primary undo path.
The editor now records reversible `EditTransaction` values composed of typed `EditOperation`
entries backed by `ProjectSceneId`, `ObjectId`, and `TransitionId`.

## Gesture lifecycle

A paint or erase pointer drag follows one lifecycle:

1. Pointer down opens the gesture.
2. Every changed cell contributes a typed operation.
3. Repeated edits to the same cell coalesce to the original `before` value and final `after` value.
4. Pointer release commits the gesture as one undo entry.
5. Escape reverts the uncommitted gesture.

This means a 200-cell brush stroke is one history entry rather than 200 serialized copies of the world.

## Typed operations

The initial transaction executor supports:

- tile and zone changes;
- object insertion, removal, and movement;
- transition insertion, removal, and resizing.

Object and transition operations preserve exact stable identities. Undo executes operations in reverse
order. Redo executes them in forward order. The transaction executor clones the world only at undo or
redo time as an atomic recovery guard; it does not serialize or clone the world for every edited cell.

## Compatibility

`EditorCommandBus::capture_undo_snapshot` remains available for the in-game developer overlay while
that surface is migrated. The native editor uses `undo_world` and `redo_world`, which support both typed
and fallback snapshot entries in the same history.

## Native editor controls

- `Ctrl+Z`: undo
- `Ctrl+Y` or `Ctrl+Shift+Z`: redo
- `Escape`: cancel an active paint/erase gesture

The inspector reports total undo entries, typed undo entries, redo entries, and active gesture operation count.

## Next work

Pass 49 can now add marquee selection, multi-item movement, rectangle paint, flood fill, replace, and clipboard
operations without rewriting undo again. Those features should emit one `EditTransaction` per user gesture.
