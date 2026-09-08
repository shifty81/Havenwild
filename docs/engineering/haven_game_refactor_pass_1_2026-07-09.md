# Havenwild Runtime Refactor Pass 1 — Game Main Surface Reduction

**Date:** 2026-07-09  
**Source input:** `crates.zip` uploaded into the current ChatGPT sandbox  
**Scope:** Safe first pass against `crates/haven_game/src/main.rs` to reduce monolith pressure without changing gameplay behavior.

## Why this pass exists

The current source is already aligned toward the intended modular Havenwild Rust workspace, but the game runtime entry file is still carrying too many unrelated responsibilities. This pass starts separating low-risk runtime concerns out of `main.rs` so the next pass can move larger draw/update/editor-overlay systems without mixing behavior changes with structural cleanup.

## Files added

```text
crates/haven_game/src/editor_state.rs
crates/haven_game/src/game_log.rs
crates/haven_game/src/render_queue.rs
crates/haven_game/src/runtime_config.rs
crates/haven_game/src/terrain_generation.rs
crates/haven_game/src/terrain_render.rs
```

## File changed

```text
crates/haven_game/src/main.rs
```

## What moved out of `main.rs`

### `editor_state.rs`

Owns lightweight runtime/editor overlay state enums:

- `EditorTab`
- `TransitionEdit`
- `MapBrushMode`
- `FootprintEditTarget`
- `LayoutDrag`

### `game_log.rs`

Owns runtime logging:

- `GameLog`
- log directory creation
- append-only `logs/haven_game.log` writes

### `render_queue.rs`

Owns render queue command identity:

- `RenderCommand::Object`
- `RenderCommand::Customer`
- `RenderCommand::Player`

### `runtime_config.rs`

Owns runtime constants and Macroquad window configuration:

- player speed
- save path
- worldgen pack path
- worldgen export path
- UI layout path
- undo limit
- UI grid size
- `window_conf()`

### `terrain_generation.rs`

Owns prototype terrain-generation helpers:

- default tile interaction fallback
- deterministic height hashing
- height classification into `TileKind`

### `terrain_render.rs`

Owns prototype terrain visual helpers:

- fallback tile colors
- zone overlay colors
- tile detail drawing
- tile border drawing
- autotile bevel/inner-corner visual pass
- deterministic visual tile jitter

## Behavior expectation

This is intended to be behavior-preserving. It does not change:

- player movement
- editor tools
- save/load paths
- worldgen pack paths
- object placement rules
- map generation output
- Macroquad window title or size
- dev-mode keybinds
- runtime UI behavior

## Validation performed in this sandbox

The sandbox does not have `cargo` or `rustc`, so a Rust compile check could not be executed here.

Performed checks:

```text
python3 tools/automation/validation/checks/worldgen/Validate-WorldgenRuntimeIndex.py
python3 tools/automation/validation/checks/worldgen/Validate-WorldgenAssets.py
python3 tools/automation/validation/checks/worldgen/Validate-HavenwildOpenWorldPreset.py
```

Results:

- Runtime index validation: pass, 0 errors, 1 warning about 14 placeholder object assets needing production atlas art.
- Worldgen asset validation: pass, 0 errors, 1 warning: validator could not parse `TileKind` enum.
- Open-world preset validation: pass, 1024x1024 tiles, 16x16 chunks, 9 required anchors.

Structural sanity checks:

- All `crates/haven_game/src/*.rs` files have balanced braces, parentheses, and brackets by simple static count.
- `main.rs` reduced from 3,936 lines to 3,378 lines.
- New extracted module total: 601 lines.

## Next safest refactor pass

Next pass should continue reducing `haven_game/src/main.rs` in this order:

1. Move editor overlay draw functions into `editor_overlay_ui.rs`.
2. Move editor overlay input/click handling into `editor_overlay_input.rs`.
3. Move object selection/footprint edit helpers into `object_edit_runtime.rs`.
4. Move transition editing helpers into `transition_edit_runtime.rs`.
5. Move save/load/worldgen pack commands into `runtime_commands.rs`.
6. Only after those compile cleanly, split `haven_editor/src/main.rs` into native editor shell modules.

## Notes for Codex / local follow-up

Run these locally before merging:

```powershell
cargo fmt --workspace
cargo check --workspace
cargo test --workspace
cargo run -p haven_game
```

If `#[macroquad::main(window_conf)]` is sensitive to wrapper placement, keep the wrapper in `main.rs` and leave `runtime_config::window_conf()` as the single owner of the actual configuration.
