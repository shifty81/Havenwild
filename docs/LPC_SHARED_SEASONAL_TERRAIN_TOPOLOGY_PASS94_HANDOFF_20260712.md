# Havenwild Pass 94 — Shared LPC Seasonal Terrain Topology

## Why the single sand cell was broken

Pass 92 suppressed diagonal-only grass-to-sand inner corners. That removed the
four authored 2x2 concave roles needed around an isolated sand cell, leaving a
plus-shaped grass fringe with square missing corners.

## Runtime correction

- Restored authored grass-to-sand inner-corner requests.
- Removed the pair-specific exception from the shared inner-corner resolver.
- Kept owner-side cardinal edge masks and authored outer-corner masks.
- Added a map-level test proving one sand cell produces four cardinal edge roles
  and four diagonal inner-corner roles.
- The same resolver now applies to every mapped LPC topology family.

## Whole-sheet seasonal contract

`lpc_seasonal_terrain_topology_v0_1.json` is generated from the complete summer
cell ledger. It records 20 authored 3x3 topology families, 19 authored 2x2
inner-corner families, and identical coordinate bindings for summer, spring,
autumn, winter, and winter-ice.

Summer remains the canonical semantic role map. Seasonal sheets swap source
art only; they do not define separate topology logic.

## Architecture cleanup

The player HUD/minimap rendering was moved from `runtime_draw.rs` into
`runtime_hud.rs`, returning the runtime draw aggregate below its locked file-size
limit.

## Commands

```bat
tools/build/Build.cmd lpc-seasonal-topology
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

## Visual acceptance

- One sand cell in grass forms one complete rounded LPC hole with no missing corners.
- 2x2, L-shaped, strip, cove, island, and hole shapes have no internal seams.
- Grass/dirt, grass/sand, banks, depth rings, and future promoted summer families
  all use the same eight-neighbor role contract.
- Seasonal mirrors preserve topology and change only their source sheet.
