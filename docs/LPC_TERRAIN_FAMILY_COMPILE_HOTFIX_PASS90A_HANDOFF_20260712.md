# Havenwild Pass 90A — LPC Terrain Family Compile Hotfix

## Purpose

Correct the Rust compile error introduced by Pass 90 in `haven_world` and remove the accompanying unused-import warning without suppressing compiler or Clippy diagnostics.

## Corrections

1. Added an explicit lifetime to `builder_for` in:
   - `crates/haven_world/src/autotile/transition_atlas.rs`

   The returned mutable builder is now explicitly tied to the lifetime of the mutable `builders` vector, not the independent static atlas-group string.

2. Removed the production-only unused import of `default_atlas_group_for_material` from:
   - `crates/haven_world/src/autotile/transition_rule_draft.rs`

3. Imported `default_atlas_group_for_material` directly inside the test module that uses it:
   - `crates/haven_world/src/autotile/transition_rule_draft/tests.rs`

## Behavior impact

None. This is a compile-safety correction only. Pass 90 terrain-family selection, atlas baking, pond mappings, save compatibility, and runtime behavior are unchanged.

## Windows verification

Run from the repository root:

```bat
tools/build/Build.cmd all
```

Expected next gate sequence:

1. `cargo fmt --all`
2. `cargo fmt --all -- --check`
3. `cargo check --workspace --all-targets`
4. `cargo clippy --workspace --all-targets -- -D warnings`
5. tests, validators, and release application builds

The correction was prepared in an environment without a Rust toolchain, so Windows remains the authoritative compile and Clippy verification environment.
