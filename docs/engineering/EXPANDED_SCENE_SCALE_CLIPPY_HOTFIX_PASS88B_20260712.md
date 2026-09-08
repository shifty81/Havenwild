# Expanded Scene Scale Clippy Hotfix — Pass 88B

## Failure corrected

The Windows `tools/build/Build.cmd all` run completed `cargo check --workspace --all-targets`, then failed at the strict Clippy gate in `crates/haven_core/src/worldgen_loader.rs`.

Clippy reported `needless_range_loop` for zone migration loops that indexed `zone_rows[y]` and `row[x]`.

## Implementation

The zone parser now uses iterator/enumeration traversal while preserving the existing validation and migration behavior:

- zone row count must equal the source scene height;
- every zone row must equal the source scene width;
- malformed rows and cells retain coordinate-specific errors;
- legacy scene offsets still apply to every migrated zone cell;
- out-of-runtime-bounds cells remain guarded by `TavernMap::idx`;
- no Clippy allow attribute or weakened build gate was added.

## Validation

Added `tools/automation/validation/checks/worldgen/Validate-ExpandedSceneScaleClippyHotfixV89.py` and registered it in the aggregate editor validation lane.

## Windows verification

Run from the repository root:

```bat
tools/build/Build.cmd all
```

Expected progression:

1. formatting passes;
2. workspace check passes;
3. strict Clippy proceeds beyond `haven_core`;
4. tests, project validators, and application builds continue.
