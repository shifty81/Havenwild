# Havenwild Pass 90B — Scene Registry Expanded-Spawn Test Hotfix

## Failure addressed

`cargo check` and strict Clippy passed, but `cargo test --workspace` failed in:

`haven_core::scene_registry::tests::registry_preserves_order_and_resolves_project_ids`

The test expected the legacy cellar spawn X value `2`. Pass 88 deliberately centers legacy 48x32 scene coordinates inside the expanded 96x64 scene, so the constructed cellar scene now has an X offset of +24 and reports `26`.

## Correction

The scene-registry test now captures `cellar.spawn_x` from the constructed `SceneMap` before inserting it into `SceneRegistry`, then verifies that lookup preserves that value. This keeps the test focused on registry ordering and identifier resolution instead of duplicating the separate scene-size migration contract.

No runtime, terrain, save, scene-size, or registry behavior changed.

## Regression guard

Added `tools/automation/validation/checks/worldgen/Validate-SceneRegistryExpandedSpawnTestV94.py` and registered it in `tools/automation/validation/validate.py`.

## Windows verification

Run:

```bat
tools/build/Build.cmd all
```

Expected next progression:

1. `cargo check --workspace --all-targets` passes.
2. strict Clippy passes.
3. the previously failing `haven_core` scene-registry test passes.
4. the remaining workspace tests and validators continue.
