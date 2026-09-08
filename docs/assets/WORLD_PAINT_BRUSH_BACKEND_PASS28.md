# Havenwild World Paint Brush Backend Pass 28

Pass 28 wires the strict `32x32` world-tile contract into a shared paint backend for both the full editor and the in-game dev overlay.

## Locked rules

- The canonical simulation tile remains `32x32` pixels.
- Nested `16x16`, `8x8`, and `4x4` regions are detail/weight masks inside the 32x32 tile, not separate gameplay tiles by default.
- The first paintable world environment families are:
  - `sand`
  - `water`
  - `cave`
  - `paved_brick`
  - `wood_plank`
- The same backend is used by the standalone editor path and the in-game dev overlay.
- Multiplayer/server state should store material/tile IDs and deterministic edit deltas; clients derive visual shorelines, foam, debris, and transition overlays from shared rules and manifests.

## In-game dev overlay

Open dev/build mode and switch to the `Paint` tab.

Controls:

- Left mouse button paints the selected material family into the world.
- `J` / `K` cycle material family.
- `[` / `]` cycle subcell mask mode.
- `P` cycles target paint layer while on the Paint tab.
- `A` toggles autotile refresh.
- `M` matches the target layer back to the selected family default layer.
- `-` / `+` adjust brush radius.

## Current implementation scope

The current prototype writes the resolved `TileKind` directly into the scene map and reports deterministic subcell coverage. This gives the editor a stable shared call shape now, while leaving room for a later persistent paint-weight/delta layer.

Future persistence should add a scene-side world paint delta file for `subcell_weight_delta`, `material_family`, and `edit_sequence` so multiplayer and save migration can replay edits exactly.
