# B05B — Cliff source-backed projection authority (2026-09-17)

## Source of truth

The canonical structural mask remains `TavernMap.structural_levels`; its
renderer uses `haven_render::structural_cliff_visual` and the exact certified
ElizaWy/LPC `Terrain/cliff_summer.png` cell/assembly roles. The raw source
remains read-only. The V7 `terrain-map-v7.png` owns underlying surface
materials. `assets/generated/worldgen_v0_1/terrain/elizawy_cliff_runtime_overlay_summer.png`
is an **output/cache derived from those sources**, not independent artwork.

The active W109G projection JSON locks the raw source, V7 image, derivative
SHA-256, dimensions and builder. This pass connects that contract to build
and test intake: after existing LPC restoration the gate validates both
sources and the output. If the output is absent it invokes the existing
builder **to a temporary file**, verifies exact contract hash and dimensions,
and publishes atomically only if they match. A wrong existing output is
preserved, never silently replaced. The known older builder may not
reproduce the active W109G hash: in that event the build fails visibly;
correct the builder against the source/acceptance evidence, not by relaxing
SHA-256 or drawing proxy cliffs. No copyrighted assets are included in patch.

## What this does not claim

This is asset supply/contract enforcement, **not** a claim that every cliff
is present in the source scene structural levels, that all cliff contour
recipes have passed visual review, or that editor/client water is optimized.
The previous screenshots show both missing coverage and water seams; those
need structural-host diagnostics and neighbor-aware water/render caching as
separate verified changes. PIE remains pending.

## Gate and manual acceptance

1. Apply patch on top of B05A, run PCC Full Quality Gate.
2. Look for `Pinned ElizaWy cliff source VERIFIED`, `Pinned V7 terrain source
   VERIFIED`, and `Derived cliff projection VERIFIED` in the build log.
3. If the build fails with `builder are out of sync`, share the new debug
   bundle. Do not manually copy a different cliff sheet into the derived path.
4. After GREEN, capture whether `CLIFF ART MISSING` appears and check the
   specific location for a structural edge in editor **and** external client.
5. Measure water frame time separately; this source-asset pass cannot
   certify improved water FPS or cross-partition seams.
