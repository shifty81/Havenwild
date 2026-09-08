# Havenwild Pass114B Architecture Split

Purpose:

- Fix the final build failure from `validate_architecture.py`.
- Preserve the existing Pass114 terrain/catalog generation work.

Change:

- Split object definitions and footprints out of `crates/haven_core/src/foundation/tile_object_catalog.rs`.
- Added `crates/haven_core/src/foundation/placeable_object_catalog.rs`.
- Re-exported the new module from `crates/haven_core/src/foundation.rs`, preserving existing public imports such as `haven_core::ObjectKind` and `haven_core::ObjectFootprint`.

Validation performed in the scratch workspace:

- `python3 tools/automation/validation/validate_architecture.py`
- `python3 tools/automation/validation/checks/assets/Validate-HavenwildAssetUtilizationAuditV115.py`
- `bash -n tools/build/Build.sh`

Notes:

- This is an overlay hotfix, not a complete source rollup. Apply it over the Pass114 source tree that produced the July 13 20:19 build log.
- Full Rust verification still needs to be run on the Windows repo with `tools/build/Build.cmd all`.
