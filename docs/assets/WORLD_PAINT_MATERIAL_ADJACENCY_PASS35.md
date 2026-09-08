# World Paint Material-State Adjacency Resolver Pass 35

This pass adds a deterministic adjacency resolver on top of the persisted world-paint material-state layer.

## Goals

- Keep the gameplay grid canonical at 32x32 pixels.
- Resolve material adjacency from saved material cells, not from rendered pixels.
- Detect shoreline candidates between sand and water.
- Detect cave edge/cliff-face candidates when cave cells touch other material families.
- Detect grey paved-brick edge/corner readiness.
- Detect wood-floor trim/edge readiness.
- Provide selected-cell and active-scene summaries in the Paint tab.
- Preserve multiplayer safety by deriving visuals client-side from deterministic state.

## Runtime/UI

Paint tab additions:

- `Adj` button / `Y` hotkey: resolve selected-cell adjacency.
- `SceneAdj` button / `U` hotkey: summarize active-scene material adjacency.

## Module Ownership

- `haven_world::world_paint_material_adjacency` owns deterministic resolver logic.
- `haven_game::world_paint_editor_panel` only hosts buttons, hotkeys, and display text.
- No raw visual shoreline/foam/debris state is made authoritative.

## Next Step

Use these adjacency reports to select prototype transition tile records from the strict 32x32 world tile atlas.
