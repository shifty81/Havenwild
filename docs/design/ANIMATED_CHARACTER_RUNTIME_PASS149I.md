# Pass 149I — Animated Character Runtime Composition

Pass 149I makes the persistent character appearance selected in the creator the first runtime representation used by the world renderer.

## Runtime order

1. Load the selected profile from the account-level character store.
2. Resolve the enabled `body/base`, `clothing/torso`, `clothing/legs`, and `clothing/feet` layers.
3. Select idle or one of eight walk frames from movement state.
4. Resolve north, west, south, or east orientation from the runtime facing vector.
5. Draw the same selected skin and starter garment colors in the world.
6. Fall back to the legacy walk atlas only when the profile cannot be loaded.

## Current production boundary

This pass proves the saved layered appearance is authoritative in runtime and animated. The renderer is still a procedural layer compositor. A later asset-binding pass must replace each procedural layer shape with production-approved LPC-compatible sheets while retaining this exact appearance, animation, persistence, and fallback contract.
