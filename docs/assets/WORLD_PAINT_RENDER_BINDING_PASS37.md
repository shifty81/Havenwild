# World Paint Render Binding Pass 37

This pass binds the world-paint material-state pipeline to the generated strict `32x32` world environment atlas.

Pipeline:

```text
paint delta
-> material state
-> adjacency report
-> transition tile resolver
-> render binding cache
-> runtime atlas draw
```

## Ownership boundary

- `haven_world` owns deterministic material, adjacency, and tile-resolution logic.
- `haven_game` owns runtime texture loading and preview draw calls.
- Paint deltas and material state remain authoritative data.
- Render bindings are derived client/editor preview data and should not become multiplayer authority.

## Runtime behavior

The game attempts to load:

```text
assets/generated/world_tiles/havenwild_world_environment_test_v0_1/havenwild_world_environment_test_v0_1.png
```

The active scene gets a render-binding cache on startup, scene switches, paint strokes, replay, save/load lifecycle hooks, and the manual Paint-tab `Bind` button / `B` hotkey.

If a cell has no render binding, the older prototype TileKind/procedural rendering path remains in use.

## Current capability

The strict 32x32 generated atlas can now appear in the runtime preview for painted cells that have material-state records and transition tile resolutions. This is still an editor/dev-preview binding; the next production step is a persistent render cache document and layer-aware composition for overlays such as foam/debris.
