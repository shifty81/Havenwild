# Havenwild Native Terrain Transaction Clippy Audit — Pass167Z72

## Finding

The Windows Z71 build passed project validation, formatting, and Cargo check. Strict Clippy stopped in `crates/haven_editor/src/scene_edit.rs` because the new multi-cell terrain transaction diff used `for index in 0..scene.map.tiles.len()` to index both `before_tiles` and the current scene buffer.

## Resolution

The diff now uses:

```rust
for (index, (&before, &after)) in before_tiles
    .iter()
    .zip(scene.map.tiles.iter())
    .enumerate()
```

This is behavior-equivalent because the before snapshot and active scene tile buffer have the same map dimensions. The iterator remains row-major and continues deriving `x` and `y` from the enumerated index.

## Non-goals

No terrain rendering, water tier, style-lane, editor brush, migration, or asset behavior changed.
