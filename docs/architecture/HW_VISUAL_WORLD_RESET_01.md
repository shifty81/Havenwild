# HW-VISUAL-WORLD-RESET-01

Baseline: `f8b47a750d11ea894995854ded03d70b0885fd0a`

This reset deliberately removes presentation-driven world mutation before any
further atlas/editor compatibility work.

## Authority rule

World generation, explicit editor authoring, and gameplay state own semantic
terrain and hydrology. Rendering consumes those semantics.

Rendering limitations are never permission to:

- convert grass/dirt into sand merely because water is adjacent;
- create a fixed-width beach band;
- erase isolated water or thin land features;
- rewrite diagonal/checkerboard terrain contacts;
- convert shallow/deep water to make a transition atlas easier to draw.

Unsupported authored combinations must become presentation diagnostics or an
approved non-semantic owner-fill fallback.

## Runtime change

The legacy shoreline cleanup/lifecycle entry points remain callable for API
compatibility, but are semantics-preserving no-ops.

The per-water-tile animated glint/caustic overlay is disabled. The span material
remains active. Future water animation must be batched/retained rather than
issuing decorative draw calls per visible water tile.

## Test change

Old tests that protected beach-band, speckle-removal, land-erosion, depth rewrite,
and atlas-driven topology mutation are replaced with semantic-preservation tests.

## Next reset block

HW-VISUAL-WORLD-RESET-02 should address:

1. editor Assets: normal Library shows semantic assemblies/slices; complete
   atlas sheets stay in Sources/provenance only;
2. building composition: wall/roof/door/window sockets and collision from one
   authored recipe; no repeated full-sheet/facade slabs;
3. structural cliff visual/collision/attachment authority;
4. held-tool per-action/per-frame hand sockets;
5. validator matrix: KEEP / REWRITE / DELETE / HISTORICAL-ONLY for every
   visual/world-generation validator and acceptance test.
