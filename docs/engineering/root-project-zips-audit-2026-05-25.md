# Root Project Zip Audit - 2026-05-25

## Root Zips Found

Two zip archives were present at the repository root:

```text
havenwild-clean-source-with-worldgen-v0-1.zip
havenwild-worldgen-v0-1-overlay.zip
```

Both were copied into:

```text
WORKSPACE/imports/project-rollups/
```

The root copies and temporary archived copies were later removed after the audit and integration work completed.

## `havenwild-worldgen-v0-1-overlay.zip`

Audit result: imported into active project paths.

Archive contents:

- 22 files
- about 0.29 MB uncompressed
- no Rust source replacements
- generated worldgen asset contract, placeholder atlases, atlas manifests, one home-island biome profile, and a smoke-test preview

Imported paths:

```text
assets/generated/worldgen_v0_1/
tools/automation/worldgen/Generate-WorldgenAssets.py
docs/design/worldgen-asset-contract-v0-1.md
docs/engineering/worldgen-v0-1-apply-notes.md
```

Important imported files:

- `assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json`
- `assets/generated/worldgen_v0_1/terrain/common_base_terrain_32.json`
- `assets/generated/worldgen_v0_1/terrain/terrain_autotile_47_32.json`
- `assets/generated/worldgen_v0_1/water/water_families_animated_32.json`
- `assets/generated/worldgen_v0_1/home_island/home_island_worldgen_smoke_test_v0_1.json`

Next code task from this overlay:

```text
Add a Rust GeneratedAssetRegistry that reads
assets/generated/worldgen_v0_1/worldgen_asset_manifest_v0_1.json
and maps current TileKind values to atlas entries.
```

## `havenwild-clean-source-with-worldgen-v0-1.zip`

Audit result: archived as a source snapshot; not overlaid onto active source.

Reason:

- It is a full project snapshot, not a narrow patch.
- It contains older versions of active Rust files compared with the current working tree.
- It includes duplicated nested crate paths such as `crates/crates/...`.
- It includes website `.git` material and legacy/mod documentation that should not be blindly merged into the active runtime/editor tree.

Targeted comparison showed the active tree is newer or more complete for:

- `crates/haven_core/src/lib.rs`
- `crates/haven_editor/src/lib.rs`
- `crates/haven_game/src/main.rs`
- `README.md`
- `content/packs/starter_pack.json`
- `assets/generated/prototype_terrain_tiles.json`

Useful if needed later:

- archived snapshot/reference material
- older website/docs/sdk material
- legacy/module examples that can be audited separately before import

## Current Integration Status

- Worldgen v0.1 generated assets: staged in active project.
- Worldgen v0.1 manifest contract: staged in active project.
- Runtime/editor loader: wired through `haven_core::asset_registry::GeneratedAssetRegistry`.
- Clean-source snapshot: archived only.
