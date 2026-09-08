# Scene Identity Migration Pass 45

This pass starts the real prerequisite for Create Scene / Delete Scene workflows.

The current runtime still uses a legacy `SceneId` enum. That is safe for a prototype, but it prevents honest user-created scenes because every scene must be known at compile time. This pass adds a project-owned `ProjectSceneId` bridge in `haven_core` and a migration contract under `content/editor/scene_identity/`.

## Added

- `crates/haven_core/src/scene_identity.rs`
- `ProjectSceneId`
- `SceneSurfaceRole`
- `SceneCanvasPlacement`
- `SceneIdentityRecord`
- `SceneIdentityMigrationPlan`
- default migration records for the existing seed scenes

## Rules

- Exterior scenes live on the overworld canvas.
- Interiors, caves, dungeons, and special scenes live in a scene bank.
- Bank scenes connect through transitions and do not occupy overworld terrain.
- Create/Delete scene buttons remain gated until runtime navigation, saves, validation, and transitions use `ProjectSceneId` instead of the enum.

## Next implementation step

Replace transition targets and active scene references with a bridge type that can resolve either a legacy enum scene or a project-owned scene record.
