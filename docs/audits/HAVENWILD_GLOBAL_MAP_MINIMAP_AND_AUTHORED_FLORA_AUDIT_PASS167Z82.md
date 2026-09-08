# Havenwild Pass167Z82 Audit — Global Map, Minimap, and Authored Flora

## Findings

### Minimap

The pre-pass minimap rasterized `world.active().map` into the HUD panel and placed the player marker with active-scene-local coordinates. This made every PCG storage partition look like an independent map.

The replacement minimap resolves the player's global tile, builds the active PCG-region surface manifest, samples the correct owning partition for each displayed cell, and keeps the marker fixed at the center.

### Full map

Each selected world already stores its seeded archipelago rectangle manifest and generated scene tiles. The pass loads that save-specific layout and adds a runtime map state and screen rather than introducing a second world representation. The checked-in manifest is only a compatibility fallback.

### Flora

The authored object atlas already exposes multiple trees, bushes, mushrooms, herbs, wildflowers, and reeds. PCG client generation explicitly set vegetation density to zero. The pass removes that suppression and adds deterministic placement plus existing-save migration.

### Surface actors

Terrain had global cross-partition rendering, while objects and stamps were still drawn only from the active scene. The pass adds globally offset surface object/stamp commands and retains the local path for interiors.

## Risks reviewed

- PCG islands reuse local chunk coordinates. The minimap and exterior actor path intentionally use `ContinuousSurfaceManifest::for_world`, which filters to the active PCG region before indexing by chunk coordinate.
- The full world map uses landmass region identity plus rectangle coordinates, allowing different islands to reuse local chunk coordinates without collisions.
- Natural-object placement uses existing collision and footprint checks and cannot overwrite player-authored objects.
- Existing save migration is versioned and deterministic.
- The pass does not claim waypoint persistence or fog-of-war completion.

## Locked decisions

- Pass167Z80 remains the checkpoint.
- Exterior minimap coordinates are global and player-centered.
- Interiors remain local scene maps.
- `M` is the runtime world-map toggle.
- Flora remains object-based and sourced from existing authored assets.
- No placeholder or generated artwork is permitted.
