# Scene Registry and Foundation Normalization — Pass 48B

## Purpose

Pass 48B completes the world-model side of the scene identity migration before advanced infinite-canvas editing is added. Runtime scenes are no longer stored as a raw vector keyed by the fixed legacy `SceneId` enum.

## Canonical scene model

- `SceneMap.id` is a project-owned `ProjectSceneId`.
- `GameWorld.scenes` is a `SceneRegistry`.
- `SceneReference` remains the serialized transition and active-scene reference.
- `SceneId` remains only as the nine starter-template identifiers and a compatibility adapter for old content and UI that has not yet migrated.

`SceneRegistry` preserves insertion order for editor presentation while maintaining an ID index for direct lookup. Duplicate normalized IDs are rejected.

## Scene lifecycle APIs

`GameWorld` now exposes guarded operations for:

- inserting a project scene;
- duplicating a scene under a new project ID;
- renaming a scene while repairing active-scene and transition references;
- removing a scene only when it is neither active nor referenced by inbound transitions;
- activating a scene only when its reference resolves in the registry.

The backing APIs exist now, but Create Scene and Delete Scene UI remain intentionally gated until stable selection IDs, reference-repair presentation, and typed undo transactions are implemented.

## Compatibility

The line-save format remains version 1 and continues to load the existing nine seed scene codes. It now also round-trips arbitrary normalized project scene IDs. Worldgen JSON loading no longer requires `sceneId` values to map to `SceneId`; transition targets are retained as project references and validated after the full registry is assembled.

## Foundation decomposition

The former `foundation.rs` aggregate was reduced by extracting:

- `scene_types.rs` — legacy seed scene enums and common scene/zone classifications;
- `foundation/scene_world.rs` — `SceneMap`, `GameWorld`, serialization, and scene lifecycle services;
- `foundation/ui_layout.rs` — runtime/editor panel layout contracts;
- `scene_registry.rs` — ordered indexed scene storage.

The remaining `foundation.rs` debt is locked against growth and should later be split into tile, object, map, interaction, and build-tool modules.

## Deferred work

Pass 48B does not expose arbitrary scene lifecycle buttons and does not migrate the legacy region graph to project scene IDs. The region graph currently ignores non-seed project scenes instead of assigning an invalid legacy enum value.

The next normalization pass should add stable authored entity IDs, one canonical editor selection model, and shared canvas hit-test results before marquee, move, clipboard, and typed transactional undo are implemented.
