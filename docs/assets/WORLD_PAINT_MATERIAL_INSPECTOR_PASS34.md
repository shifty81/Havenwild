# World Paint Material-State Inspector Pass 34

This pass adds selected-cell material-state inspection to the World Paint system.

## Goals

- Keep the paint system modular.
- Let the Paint tab inspect the selected tile coordinate.
- Show material family, layer, subcell mode, weight count, last edit sequence, and readiness flags.
- Keep authoritative state as deterministic material-state/delta records, not raw rendered shoreline pixels.

## Runtime behavior

The Paint tab now supports:

- `Inspect` button
- `I` hotkey

The inspector reads:

```text
WORKSPACE/generated/world_paint/world_paint_material_state_v0_1.json
```

It reports all cell/layer records for the selected 32x32 tile coordinate.

## Module ownership

```text
haven_world = material-state query structs/functions
haven_game  = Paint-tab UI button/hotkey/display only
haven_editor = future reusable egui inspector/property binding
haven_assets = manifests/catalogs/contracts
```

## Readiness flags

- `ready_for_adjacency`: true when the selected cell has a base terrain/water/cave record useful for shoreline/cave/transition resolution.
- `ready_for_debris`: true when the selected cell has a ground-like material suitable for future debris overlay rules.

## Future follow-up

The next pass should add material-state adjacency resolution so cells marked ready can drive shoreline/cave edge/paved-edge selection from neighboring material records.
