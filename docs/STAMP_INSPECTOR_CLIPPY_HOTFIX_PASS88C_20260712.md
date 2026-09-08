# Havenwild Pass 88C — Stamp Inspector Clippy Hotfix

## Failure corrected

The Windows `tools/build/Build.cmd all` run passed formatting and `cargo check --workspace --all-targets`, then stopped during strict Clippy in:

- `crates/haven_editor/src/stamp_inspector.rs`
- `clippy::too_many_arguments`
- `update_scene_stamp` had 8 parameters while the project uses `-D warnings`

## Implementation

Pass 88C replaces the eight-parameter command function with a typed request object:

- Added `StampUpdateRequest`.
- Added `StampUpdateRequest::new(...)` for conversion of scene ID and action text.
- Reduced `update_scene_stamp(...)` to four parameters.
- Updated the native stamp inspector call site.
- Re-exported the request type from `haven_editor`.
- Did not add a Clippy suppression.

The transaction, validation, undo, placement-collision, identity, minimum-size, and editor-status behavior is unchanged.

## Validation

Completed in the packaging environment:

- Architecture validation: passed, 179 Rust files.
- Content validation: passed, 217 JSON files.
- Open-world preset validation: passed.
- Editor validators V54–V90: passed. The aggregate command timed out after V69, so V70–V90 were run directly and all passed.
- Pass 87 expandable pond validator: passed, 14 mapped families.
- Pass 88 scene migration validators: passed.
- New V90 stamp-inspector Clippy regression validator: passed.
- ZIP integrity: passed.

Rust, Cargo, and Clippy are unavailable in the packaging environment. Final verification must run on Windows.

## Windows verification

From the source root:

```bat
tools/build/Build.cmd all
```

The build should now pass the reported `update_scene_stamp` Clippy failure and continue to the next gate. Preserve the next complete log if another strict warning appears.
