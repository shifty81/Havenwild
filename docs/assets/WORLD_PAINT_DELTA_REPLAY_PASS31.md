# World Paint Delta Replay Pass 31

Pass 31 adds deterministic replay for persisted world paint delta records.

## Goal

The Paint tab already writes operation records to:

```text
WORKSPACE/generated/world_paint/world_paint_deltas_v0_1.json
```

This pass adds a replay path so those operations can rebuild scene tiles after save/load, be used for migration tests, and later become the same operation stream used by the host/server for multiplayer synchronization.

## Ownership boundary

```text
haven_world/world_paint.rs         deterministic brush application
haven_world/world_paint_delta.rs   operation-log storage and validation
haven_world/world_paint_replay.rs  replay orchestration over maps/worlds
haven_game/world_paint_editor_panel.rs UI buttons/hotkeys only
```

The game-side panel does not own replay logic; it only calls the shared world backend.

## Dev overlay controls

In the Paint tab:

```text
Replay     replay deltas for the active scene
ReplayAll  replay deltas for all scenes
T          replay deltas for the active scene
```

## Multiplayer-safe rule

Replay uses authoritative operation inputs such as scene id, material family, brush radius, subcell mode, mirror flags, and center. It does not store or replay raw shoreline pixels, foam sprites, or decorative overlay pixels as authoritative state. Clients derive those visuals from the same deterministic contracts.
