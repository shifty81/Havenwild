# Pass 149J — Production LPC Runtime Binding

Pass 149J replaces the always-procedural runtime character with stable asset-pack layer bindings.

## Runtime order

1. Load the selected persistent character profile.
2. Resolve each enabled appearance layer by `StableAssetRef` through the mounted production asset session.
3. Load and deduplicate source textures through `StableTextureCache`.
4. Sort body, clothing, armor, hair, headwear, tools, and weapons into deterministic draw order.
5. Draw the same 64×96 animation frame from every resolved layer.
6. Use the procedural character only when no production layer texture resolves.

The saved appearance remains the source of truth for tint, variant, and enabled state. Variant IDs are ignored only for locating the common source image; they remain available to the animation/appearance model.

## Current supported sheet baseline

The runtime baseline expects four direction rows in north, west, south, east order. Column zero is idle and columns one through eight are walk frames. Future animation-family metadata can override this without changing character saves.

## Licensing

Only assets mounted through production-enabled packs are eligible. Reference-only LPC sources are not silently promoted into runtime content.
