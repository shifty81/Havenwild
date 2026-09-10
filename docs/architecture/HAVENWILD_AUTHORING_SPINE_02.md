# Havenwild Authoring Spine 02

Pass: `HW-AUTHORING-SPINE-02`

## Purpose

This pass begins the Editor Authoring V2 implementation without changing terrain, cliff, water, world-generation or gameplay visuals. It establishes the shared state/command/transaction vocabulary that later Game Canvas, Asset Catalog V2, LDtk-style world authoring and F3 work will use.

The pass intentionally preserves the current working world/runtime as the visual regression authority.

## Locked workflow

Havenwild uses one creator interaction loop:

`context -> layer -> resource -> compatible tool -> Game Canvas -> Inspector -> save/playtest`

World, Scene, Routes and UI are contextual views/documents hosted by the Game Canvas. They are not separate competing world editors.

Spawn is **not** a separate studio, window or universal tool. Player Start, NPCs, animals, spawners, encounter anchors and similar authored points are entity definitions/resources. The ordinary `Place` workflow will place them when the Entities/Gameplay context supplies those resources.

`Play From Here` is deliberately different from Player Start. It is an ephemeral developer launch action and must never silently rewrite the persistent scene Player Start.

## Canonical context

`haven_authoring::AuthoringContext` now carries the frontend, workspace, Game Canvas context, edit scope, active scene/layer/tool, selected resource, selection class, cursor and runtime state.

The shared resource vocabulary is:

`SourceSheet -> TileSet -> Material / Asset / EntityDefinition / Prefab -> Instance`

`Brush` is reusable authoring convenience and `Rule` is automatic resolution/generation logic.

The frontend contract now distinguishes:

- `DeveloperOverlay`: lightweight F3 inspection/diagnostics.
- `RuntimeDeveloperEditor`: explicit in-game world authoring entered deliberately from the developer experience.

This prevents the old behavior where F3 conceptually meant both diagnostics and full editing at once.

## Canonical command vocabulary

The existing `EditorCommandKind` remains the compatibility command type while gaining stable IDs for V2 routing. New vocabulary reserves normal world-authoring operations for entities, prefabs, brushes and raw tile overrides, and separates persistent `world.player_start.set` from ephemeral `runtime.play_from_here`.

Stable command IDs are independent from user-facing labels so future Forge/Cortex/automation bridges can target commands without depending on UI wording.

## Canonical transaction execution

`EditorCommandBus::execute_transaction` is the preferred mutation entry point for migrated typed operations:

1. frontend creates command intent;
2. domain layer creates reversible `EditTransaction`;
3. command bus applies it atomically;
4. the same bus records undo/redo history;
5. frontend handles presentation/status only.

Legacy snapshot history remains valid during migration. The transaction-aware `undo_world`/`redo_world` path can replay both typed transactions and old snapshots.

## First migrated mutation: Player Start

The former F3 `P` shortcut directly changed `SceneMap.spawn_x` and `spawn_y` after capturing a whole-world snapshot.

It now uses `EditTransaction::set_scene_spawn`, which:

- validates scene bounds;
- records expected-before and after coordinates;
- rejects stale replay state;
- supports typed undo/redo;
- executes through the canonical command bus;
- replicates the same editor command envelope as the existing developer workflow.

This is deliberately the first small end-to-end migration because it proves the spine without changing rendering or content resolution.

## What this pass does not do

It does not add a Spawn UI. It does not alter Game Canvas appearance. It does not change terrain rules. It does not change cliffs, ramps, caves, water, assets or worldgen output. It does not delete the legacy F3 editor yet.

Those changes follow after the shared mutation path is stable and green.

## Next pass

`HW-LAYER-CONTEXT-03` should adapt the native Game Canvas onto this context vocabulary and collapse the duplicated Scene/World creator-facing layer/tool state into one contextual layer model while preserving existing stored world data.
