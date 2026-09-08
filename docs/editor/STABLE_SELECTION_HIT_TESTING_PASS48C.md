# Stable Selection and Shared Hit Testing — Pass 48C

## Purpose

Pass 48C removes unstable vector indexes from authored-object, transition, and region-node selection before marquee selection, drag movement, duplication, clipboard operations, and typed undo are introduced. It also establishes one headless hit-test result shared by the native editor and future authoring surfaces.

## Stable authored identities

The core model now owns serializable identifiers for:

- `ObjectId` — every placed map object;
- `TransitionId` — every scene transition rectangle;
- `ZoneId` — the stable key for the current cell-backed zone model;
- `RegionNodeId` — region graph nodes;
- `ProjectSceneId` — the scene scope containing the selected item.

Newly authored objects and transitions receive IDs through their owning map or scene. Worldgen imports derive deterministic IDs from source object/transition keys. Existing line saves remain readable: legacy object and transition records receive IDs during import, while new saves persist those IDs explicitly.

`PlacedObject` and `Transition` were extracted to `foundation/authored_entities.rs`, reducing the remaining `foundation.rs` aggregate and preventing the identity work from increasing the legacy monolith.

## Canonical selection model

`haven_authoring::EditorSelection` is the presentation-neutral selection state. Its primary values are `SelectionItem` variants keyed by stable IDs rather than positions in `Vec` storage:

- tile grid cell;
- object ID;
- zone ID plus grid cell;
- transition ID;
- scene ID;
- region-node ID.

The selection also stores the owning scene and optional `GridRect` bounds. The native editor now uses this state for object highlighting, transition highlighting, region-node highlighting, inspector targeting, duplication, movement, resize operations, and selection repair after undo/load.

The old `selected_scene_object: Option<usize>` and region-node index selection state are removed. Ordered indexes remain only as transient list-navigation cursors where needed; they are resolved back to stable IDs before authoring state is stored.

## Shared canvas hit testing

`haven_authoring::hit_test_scene_cell` is the canonical headless scene-cell hit test. It accepts a `SceneMap`, snapped `GridPos`, and `SceneAuthoringLayer`, then returns a `CanvasHit` containing:

- owning `ProjectSceneId`;
- snapped cell;
- stable `SelectionItem`;
- selection bounds.

The module has no Macroquad or windowing dependency. Screen-to-world and world-to-grid conversion remain owned by the native canvas camera; all layer-specific authored-content resolution now goes through the shared authoring contract.

## Typed transaction groundwork

`EditTransaction` and `EditOperation` define the next undo architecture using stable IDs. Pass 48C does not replace snapshot undo yet. Pass 48D should add apply/revert execution, begin/update/commit gesture handling, operation coalescing, and one undo record per brush stroke or drag.

## Compatibility and remaining work

The runtime developer overlay still contains some local index-based UI cursors. Those are not used by the normalized native editor selection contract and should be migrated when the runtime authoring surface adopts the shared controller.

Pass 48D should implement typed transactional undo/redo. The following feature pass can then safely add marquee selection, move handles, rectangle paint, flood fill, replace, clipboard, and multi-item operations.
