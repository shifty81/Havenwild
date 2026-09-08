# Havenwild Pass 111 - LPC Terrain Map V7 Replacement Pilot

## Source Added

`lpc-terrains(1).zip` has been imported into:

`content/assets/lpc/source/lpc-terrains-v7/`

The source includes the original credits, `terrain-map-v7.png`,
`terrain-map-v7.tsx`, `terrain-v7.png`, `terrain-v7.tsx`, and the preview TMX.

## Why This Replaces the Overlay Guesswork

The Tiled `.tsx` file already maps terrain corner tuples. For covered pairs,
the runtime can pick one complete 32x32 replacement tile from the mapped source
instead of drawing a base tile plus edge and corner overlays.

That avoids the Pass110 failure mode where pure 2x2 corner art was layered over
ordinary edge runs and created repeated scalloped bites along sand, wet-sand,
and water borders.

## Runtime Pilot

The generated runtime output is:

- `assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.png`
- `assets/generated/worldgen_v0_1/terrain/lpc_mapped_terrain_v7_32.json`
- `docs/assets/previews/havenwild_lpc_mapped_terrain_v7_pass111.png`

The runtime draws a mapped complete tile only when the local four-corner tuple
exists in this manifest. If no exact tuple exists, it falls back to the existing
base/transition path.

## Current Mapped Runtime Families

- grass
- dirt
- sand
- shallow water
- water
- deep water
- river/ocean water aliases

`WetSand` is intentionally deferred. The source pack has sand/water-shallows
terrain, but not a true dry wet-sand land material. Routing `WetSand` to shallow
water would reproduce the kind of regression seen in the latest screenshots.

## Validation

`Validate-LpcMappedTerrainReplacementV122.py` verifies:

- source files and credits are present;
- generated atlas and manifest exist;
- mapped tuple coverage is substantial;
- wet sand remains deferred;
- the renderer uses complete mapped replacement tiles before falling back to
  old overlays;
- `tools/build/Build.sh all` regenerates and validates the mapped atlas before Cargo.
