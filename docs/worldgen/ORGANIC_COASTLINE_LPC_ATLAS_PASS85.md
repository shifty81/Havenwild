# Havenwild Organic Coastline + LPC Atlas Pass 85

Date: 2026-07-11

## Result

Pass 85 replaces the old rounded structural-island fill with one continuous,
seeded coastline raster generated across the complete scene-cell assembly. It
also corrects the reviewed LPC summer-terrain coordinates and enables real
LPC-authored coastline contours in the runtime transition-atlas path.

The generated world is no longer a single radial circle split across scenes.
Coast, beach, and shallow-water bands are derived from the same global land
mask, so they remain continuous at scene boundaries and around missing scene
cells.

## Root causes closed

1. The former island field was effectively radial at scene scale, producing a
   large rounded blob.
2. Several promoted LPC base coordinates selected transition cells, transparent
   cells, or the wrong material family. That produced checkerboard terrain and
   black/empty-looking cells.
3. The transition manifest still identified the generated sheet as a
   placeholder, so the renderer used procedural fallback bands instead of the
   atlas.
4. Missing neighboring scene cells did not exert a strong enough ocean-edge
   constraint, allowing land to touch empty assembly slots.

## World-generation changes

- Added `crates/haven_world/src/island_coastline.rs`.
- Generates one global raster for every landmass assembly, then slices that
  raster into editable scenes.
- Combines five overlapping superellipse lobes instead of one circle.
- Applies broad, medium, and fine seeded domain warping.
- Cuts authored-style bays/coves into the silhouette.
- Smooths the binary land mask twice before material classification.
- Uses distance fields to create ordered bands:
  - interior grass
  - sand
  - wet sand at the land edge
  - shallow water
  - deep water
- Treats missing or exterior scene neighbors as open ocean and guarantees a
  water margin before the coastline tapers inward.
- Preserves scene IDs, scene transitions, harbor routing, and save-compatible
  semantic `TileKind` values.

Approval preview:

`docs/assets/previews/havenwild_organic_coastline_pass85.png`

## LPC terrain corrections

Reviewed mapping contract:

`content/assets/intake/lpc_terrain_promotion_v0_2.json`

Corrected families include grass, tall grass, dirt, road, sand, wet sand,
shallow water, deep water, ocean water, river water, shore foam, mud bank, and
stone-path families. Critical repeatable base cells are validated as fully
opaque.

Transition contour blocks:

- `grass_to_dirt`: zero-based block `[6, 0, 3, 3]`
- `sand_to_ocean`: zero-based block `[3, 20, 3, 3]`
- `riverbank_mud`: zero-based block `[6, 10, 3, 3]`

The baker composes the existing N/E/S/W mask layout from the reviewed LPC 3x3
blocks, extracts the authored boundary contour, and stores it as a transparent
overlay. Runtime tint supplies the requested semantic material while the
corrected base texture remains visible beneath it.

Attribution remains OGA-BY 3.0 for Lanea Zimmerman (Sharm) and Eliza Wyatt
(DeathsDarling).

## Regenerate on Windows

From the repository root:

```bat
tools/build/Build.cmd tiles
tools/build/Build.cmd apps
```

Then launch `HavenwildEditor.exe`.

To replace the current rounded generated island:

1. Open the World Canvas.
2. Right-click a scene cell on the target island.
3. Choose **Generate this island**.
4. Or choose **Generate all islands** to rebuild the entire archipelago.
5. Use **Save All** to persist the regenerated scenes and layout.

`File > Regenerate Current Seed` rebuilds the current structural layout and all
islands. `File > Reroll` uses the next shareable seed.

Generation replaces generated scene contents for the selected island. Save a
backup slot first when an island contains hand-authored changes that must be
kept.

## Build integration

The `tiles` command now runs in this order:

1. production terrain Pass 59
2. production environment Pass 60
3. corrected LPC terrain/coastline promotion Pass 85
4. multi-tile stamp preview Pass 61

Pass 85 deliberately runs after Pass 60 because Pass 60 recreates the base
terrain atlas. The existing user-import proof atlas was also rebaked once so its
checked-in PNG/JSON match the deterministic Pass 66 baker; this is a generated
output normalization only and does not change the intake workflow.

## Validation completed here

Passed:

- Python syntax checks for every changed validator and baker
- shell syntax check for `tools/build/Build.sh`
- JSON parsing for all changed/generated manifests
- web JavaScript syntax checks
- architecture validation
- content validation
- world preset validation
- project validators through V72 before the aggregate runner reached its time
  limit
- validators V73 through V84 individually
- terrain transition atlas V13
- terrain atlas manifest V14
- deterministic asset-intake atlas V66
- `git diff --check`

Rust compilation, `cargo fmt`, Clippy, and Rust unit tests could not be executed
inside this environment because no Rust toolchain is installed. The changed
Rust files were manually checked for balanced syntax and kept within the
project's module-size limits. Run `tools/build/Build.cmd all` on the Windows development
machine before promoting the pass.
