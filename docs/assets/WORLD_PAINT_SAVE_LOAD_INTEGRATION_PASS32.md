# World Paint Save/Load Integration Pass 32

Pass 32 connects the world paint delta replay system to normal runtime lifecycle points.

## Goals

- Keep the simulation on the canonical 32x32 world grid.
- Preserve 16x16 / 8x8 / 4x4 subcell-mask intent through delta metadata.
- Replay persisted paint deltas after startup, manual world load, and worldgen pack load.
- Replay deltas before save so the saved world snapshot contains the latest reconstructed terrain state.
- Restore the next paint edit sequence from the persisted delta document.
- Guard Paint-tab hotkeys so mirror and subcell controls do not also trigger global overlays or transition-target controls.

## Runtime lifecycle

```text
startup/load source world
  -> replay WORKSPACE/generated/world_paint/world_paint_deltas_v0_1.json
  -> restore max paint sequence
  -> first frame

manual F9 load
  -> load workspace/saves/world.tworld
  -> replay paint deltas
  -> refresh inspector/status

F5 save
  -> replay paint deltas
  -> save workspace/saves/world.tworld
```

## Ownership boundary

- `haven_world::world_paint_replay` remains deterministic replay logic.
- `haven_game::world_paint_lifecycle` owns runtime lifecycle wiring only.
- `runtime_persistence` calls lifecycle helpers rather than duplicating replay logic.
- UI panels remain in `world_paint_editor_panel`.

## Multiplayer note

This remains host/server safe because the authoritative record is a compact operation log. Clients should derive final visuals from the same tile/material/autotile manifests rather than synchronizing raw shoreline or foam pixels.
