# World Paint Transition Tile Resolver Pass 36

This pass connects persisted paint material state and adjacency reports to actual strict-32x32 tile records from `havenwild_world_environment_test_v0_1.json`.

## Ownership boundary

- `haven_world/src/world_paint_transition_tile_resolver.rs` resolves material-state adjacency into tile record IDs and atlas rectangles.
- `haven_game/src/world_paint_editor_panel.rs` only hosts Paint-tab buttons/hotkeys and calls the deterministic backend.
- `haven_game/src/world_paint_editor_draw.rs` only displays the selected tile resolution status.

## Editor controls

- `Tile` button or `O` hotkey: resolve selected-cell transition tile.
- `SceneTile` button or `L` hotkey: summarize active-scene transition tile resolution.

## Runtime rule

The authoritative state remains paint/material data. Transition tile IDs, shoreline visuals, cave edges, brick trims, and wood trim choices are derived from shared manifests and deterministic neighbor masks.
