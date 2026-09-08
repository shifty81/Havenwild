# Havenwild Game Runtime Refactor Pass 2 — 2026-07-09

## Purpose

Continue reducing `crates/haven_game/src/main.rs` into behavior-preserving runtime/editor modules while keeping the playable Macroquad runtime and in-game editor overlay intact.

This pass focuses on extracting editor/runtime feature groups that were still embedded directly in `main.rs` after Pass 1.

## Source impact

`crates/haven_game/src/main.rs` was reduced from roughly 3,377 lines after Pass 1 to roughly 1,967 lines.

New runtime modules added:

- `crates/haven_game/src/object_edit_runtime.rs`
- `crates/haven_game/src/map_edit_runtime.rs`
- `crates/haven_game/src/world_rules_runtime.rs`
- `crates/haven_game/src/transition_edit_runtime.rs`

The existing Pass 1 modules remain:

- `editor_state.rs`
- `game_log.rs`
- `render_queue.rs`
- `runtime_config.rs`
- `terrain_generation.rs`
- `terrain_render.rs`

## Extracted responsibilities

### `object_edit_runtime.rs`

Owns object/outliner editing behavior and object-footprint drawing helpers:

- object tab clicks
- object selection
- object list offset clamping
- object focus/pick/cycle behavior
- object nudge/delete hotkeys
- object anchor-to-cursor behavior
- footprint rectangle edits
- blocking/occlusion/fade toggles
- default footprint reset
- selected-object validation before apply
- object editor tab drawing
- object footprint preview drawing
- tile-rect overlay drawing helpers

### `map_edit_runtime.rs`

Owns heightmap and map editor behavior:

- map tab clicks
- seed/biome/water/cliff controls
- height brush selection
- active-scene heightmap generation
- bridge placement
- active biome cycling
- map brush application
- terrain rebuild from heightmap
- map editor tab drawing

### `world_rules_runtime.rs`

Owns rule/world editor behavior:

- tile-rule tab clicks
- world tab clicks
- tile rule cycling/reset
- rules editor tab drawing
- world editor tab drawing

### `transition_edit_runtime.rs`

Owns transition-editing behavior:

- selected transition resize/adjust hotkeys
- transition placement/edit command application

## Validator updates

Several validation scripts were updated so they scan modular Rust source files instead of assuming all runtime hooks remain in `crates/haven_game/src/main.rs`:

- `tools/automation/validation/checks/worldgen/Validate-WorldgenEditorOverlayV07.py`
- `tools/automation/validation/checks/worldgen/Validate-WorldgenFootprintsV10.py`
- `tools/automation/validation/checks/worldgen/Validate-WorldgenObjectOutlinerV08.py`
- `tools/automation/validation/checks/worldgen/Validate-WorldgenSceneExportV10.py`

This is important because future refactor passes will continue moving code out of monolith files. Validators should follow behavior/features, not line locations.

## Validation run

Validated with Python scripts available in this sandbox:

- PASS `tools/automation/validation/checks/worldgen/Validate-WorldgenRuntimeIndex.py`
- PASS `tools/automation/validation/checks/worldgen/Validate-WorldgenAssets.py`
- PASS `tools/automation/validation/checks/worldgen/Validate-HavenwildOpenWorldPreset.py`
- PASS `tools/automation/validation/checks/worldgen/Validate-WorldgenEditorOverlayV07.py`
- PASS `tools/automation/validation/checks/worldgen/Validate-WorldgenFootprintsV10.py`
- PASS `tools/automation/validation/checks/worldgen/Validate-WorldgenObjectOutlinerV08.py`
- PASS `tools/automation/validation/checks/worldgen/Validate-WorldgenSceneExportV10.py`

`cargo check` was not run in this sandbox because `cargo`/`rustc` are not installed here.

## Intended behavior

This pass is intended to be behavior-preserving:

- no gameplay loop change
- no map format change
- no content pack change
- no save path change
- no editor hotkey change
- no worldgen pack path change

## Next recommended pass

Continue reducing `crates/haven_game/src/main.rs` by extracting:

- `runtime_input.rs`
- `runtime_scene_navigation.rs`
- `runtime_save_load.rs`
- `runtime_draw.rs`
- `runtime_ui_shell.rs`

Completed by Pass 48A: the standalone editor shell moved from `crates/haven_editor/src/main.rs` into the decomposed `apps/haven_editor_native` application. Continue reducing `haven_game/src/main.rs` independently.
