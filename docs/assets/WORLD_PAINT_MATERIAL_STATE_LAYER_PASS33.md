# Havenwild — World Paint Material-State Layer Pass 33

## Purpose

Pass 33 adds a lightweight scene-side material-state layer for world painting.
The paint delta log remains the replayable operation history. The material-state document is the current resolved authoring/runtime state keyed by scene, tile coordinate, and paint layer.

This prevents the paint system from being only a `TileKind` rewrite path. The engine can now retain:

- material family
- target layer
- subcell mode
- subcell grid
- per-subcell weights
- resolved prototype tile kind
- last edit sequence

## Runtime document

```text
WORKSPACE/generated/world_paint/world_paint_material_state_v0_1.json
```

## Canonical grid

```text
world tile = 32x32
subcell modes = 32x32, 16x16, 8x8, 4x4
```

The smaller grids are masks inside a 32x32 tile. They are not standalone gameplay tiles.

## Authority boundary

Authoritative/edit state:

- scene id
- x/y tile coordinate
- layer
- material family
- subcell weights
- edit sequence
- resolved tile kind for prototype compatibility

Client-derived visual state:

- shoreline overlays
- foam overlays
- debris visuals
- atlas variation choice
- transition atlas cell choice

## Anti-monolith ownership

- `haven_world/src/world_paint_material_state.rs` owns deterministic material-state document logic.
- `haven_game/src/world_paint_editor_panel.rs` only calls the backend after a paint stroke.
- `runtime_config.rs` owns the path constant.
- No pixel editor or UI painting logic is added to `main.rs`.

## Next pass

World Paint Material-State Replay/Inspector Pass 34 should expose material-state counts and selected-cell material details in the Paint tab, then use material-state documents as the source for future adjacency/brush previews.
