# Expanded Scene Scale Compile Hotfix — Pass 88A

## Failure reproduced from Windows build log

`cargo check --workspace --all-targets` stopped in `haven_core` because
`foundation/scene_size_migration.rs` attempted to import `ProjectSceneId` from
its parent `foundation` module. `ProjectSceneId` is exported at the crate root,
not from `foundation`.

The same compile attempt also reported an unused parent-module import of
`legacy_scene_offset`. That helper is intentionally private to the migration
module and should not be imported by `foundation.rs`.

## Corrections

- Import `ProjectSceneId` from `crate::ProjectSceneId`.
- Remove the unused `legacy_scene_offset` import from `foundation.rs`.
- Preserve `legacy_scene_offset` as a private helper inside
  `scene_size_migration.rs`.
- Add validator V88 so this module-boundary error cannot silently return.

## Windows verification

Run from the repository root:

```bat
tools/build/Build.cmd all
```

Expected first corrected gate:

```text
OK cargo check --workspace --all-targets
```

The full build should then continue into Clippy, tests, validators, and app
packaging.
