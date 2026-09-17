# B05A — World Canvas render-hotpath and cliff readiness

This is a targeted source-level optimization and diagnostic pass against the September 17 B04R2 baseline. **It is not complete visual parity, seamless partition rendering, or PIE.**

- `haven_assets::lpc_mapped_terrain`: remove per-cell `Vec` allocation in both ordinary and animated-water tuple selection. Retain the same indexed candidate order, exact corner filter, variant count, variant index, and selected source rectangle. Existing terrain-map tests (including authored shoreline and world-edge sampler cases) must pass in the Windows Full Gate.
- Native World Canvas: avoid hashing/rebuilding a structural cache for a partition when its structural layer is hidden or the required cliff source texture is absent. No cliff geometry or pixels are fabricated as a fallback.
- The canvas now explicitly identifies missing cliff source artwork when that layer is enabled, and identifies neighbor-aware partition resolution as unfinished rather than declaring world artwork complete.

## Known blockers documented by source and screenshots

1. Rendering replays textured terrain and tuple lookups for each visible tile every frame. Allocation removal reduces hotpath cost but cannot alone certify acceptable FPS. The next performance pass needs frame timings (world draw CPU time, visible cell counts, terrain/tuple submissions, cliff cache updates) and a dirty-aware visible-partition artwork cache / submission budget that never changes semantic terrain or breaks live editing.
2. Local V7 tuple lookup samples only within `TavernMap`; current world composition renders each `SceneMap` independently. The existing sampler API already supports cross-partition lookups, but the World Canvas does not yet feed it adjacent materialized partitions. Build a neighbor-aware halo/tuple adapter from the existing continuous-surface manifest, add side-by-side chunk edge tests, and compare shoreline/water seams in editor and client. Do not overpaint seams with generic pixels.
3. Cliff rendering returns without drawing if `ELIZAWY_SUMMER_CLIFF_SOURCE_PATH` fails to load. Check the actual Windows texture readiness, generated source provenance, and structural host levels. A loaded terrain atlas does not prove cliff texture readiness. When artwork loads, certify cliff/connector recipes against the runtime at the exact same coordinates including chunk borders.
4. B04 only paints already-materialized scene rectangles; unmaterialized terrain is schematic and cannot be called finished visual world authoring.

## Checkpoint

Run PCC Full Quality Gate. Open the same materialized region from the B04 screenshot, note responsiveness versus B04R2 and whether `CLIFF ART MISSING` appears. This patch is not expected to remove water seams or fill unmaterialized world by itself. Do not mark those items fixed without a focused parity fixture and runtime evidence. No Windows build or frame-profile measurement was available when creating this transport.
