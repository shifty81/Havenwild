# Scene Reference Runtime Bridge Pass 46

This pass moves the two highest-risk runtime references off direct enum storage without pretending arbitrary scene creation is finished.

## Implemented

- Added serializable `SceneReference`, backed by normalized `ProjectSceneId` strings.
- Migrated `GameWorld.active_scene` from `SceneId` to `SceneReference`.
- Migrated `Transition.target` from `SceneId` to `SceneReference`.
- Added legacy resolution helpers for the existing nine seed scenes.
- Added identity-record alias resolution for staged migrations where a project scene ID maps to a legacy seed scene.
- Updated line-save serialization, line-save loading, worldgen JSON import/export, world-paint delta replay, simulation, validation, graph rendering, transition editing, and runtime scene navigation.
- Worldgen imports now retain unknown project scene targets instead of discarding them.
- Runtime navigation blocks unresolved targets with a status/log message instead of changing to an invalid active scene and panicking.

## Compatibility boundary

`SceneMap.id` remains `SceneId` in this pass. That keeps the current map generator, fixed scene list, editor tools, and save format operational while references become project-owned. Active scene references must therefore resolve to a loaded legacy-backed scene for now.

Create Scene and Delete Scene remain gated.

## Next implementation step

Move `SceneMap.id` and editor scene selection to `ProjectSceneId`, add a scene registry owned by `GameWorld`, then update map lookup and save loading so newly created scene records can be loaded without a legacy enum value.

## Validation performed

- Scene identity migration validator passed.
- First-island, asset, and GUI contract validator passed.
- Scene reference bridge validator passed.
- Open-world preset validator passed.
- All project JSON files parsed successfully.
- All Rust source files passed structural syntax parsing.
- Web editor JavaScript passed Node syntax checks.

A full `cargo check --workspace` and test run is still required in the normal Rust development environment; the packaging environment did not include the Rust/Cargo toolchain.
