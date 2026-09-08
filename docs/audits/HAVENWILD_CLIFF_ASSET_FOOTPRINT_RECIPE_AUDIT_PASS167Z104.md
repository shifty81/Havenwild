# Havenwild Cliff Asset Footprint & Recipe Audit — Pass167Z104

## Result

The cliff source libraries use a **32×32 source grid**, but that grid is only an addressing system. It is not a declaration that every occupied cell is an independently placeable 1×1 world asset.

Havenwild now records three separate concepts:

1. `sourceGridSpan` / `sourceRectPx` — where the authored pixels live in the source sheet.
2. `worldVisualFootprintTiles` — how much of the game-world grid a normalized recipe visually occupies.
3. `structuralHostMask`, collision edges, and traversal edges — which structural Level boundary or connector the recipe actually represents.

The latter two remain unset until a complete recipe is certified. This prevents image dimensions from becoming accidental gameplay collision or navigation authority.

## OGA LPC grass-top cliff pack

Source: `content/assets/oga_lpc/source/terrain/cliffs_grass_top/LPC_cliffs_grass.png`

- Canvas: **384×288 px**.
- Source grid: **12×9** at 32×32.
- Runtime status: **quarantined**.
- Classification: specialist connected-art construction/stamp kit, not a complete arbitrary cliff autotile family.

Audited aligned source envelopes:

| Source assembly | Grid span | Aligned px | Tight visible px | Z104 classification |
| --- | ---: | ---: | ---: | --- |
| Bare pillar/ring | 3×5 | 96×160 | 65×125 | specialist stamp, semantics pending |
| Bare diagonal split | 2×5 | 64×160 | 64×160 | specialist stamp, semantics pending |
| Grass pillar | 3×5 | 96×160 | 75×130 | complete pillar stamp/reference |
| Grass crossing/T-ramp | 3×4 | 96×128 | 86×128 | crossing/ramp assembly |
| Grass side face | 1×4 | 32×128 | 21×107 | specialist side component |
| Cave host | 3×3 | 96×96 | 96×75 | complete cave-host assembly |
| Ramp/crossing | 6×4 | 192×128 | 174×109 | complete multi-cell specialist assembly |
| Ladder | 1×3 | 32×96 | 26×83 | traversal attachment |
| Rope/suspension attachment | 2×3 | 64×96 | 48×83 | traversal attachment |
| Bottom decorative source | 3×1 | 96×32 | 96×32 | excluded from structural cliffs |

The previous renderer failure came from treating cells inside the 3×5 grass pillar as generic repeatable cliff rows. Z104 makes that interpretation invalid by contract.

The dark-dirt, sand, and snow images share the same 384×288 layout family. They remain reference variants; each material variant still needs recipe-level visual certification rather than inheriting runtime approval from the grass sheet.

## ElizaWy seasonal cliff family

Pinned commit: `f07f7f5892e67c932c68f70bb04472f2c64e46bc`

Sources:

- `Terrain/cliff_spring.png`
- `Terrain/cliff_summer.png`
- `Terrain/cliff_autumn.png`
- `Terrain/cliff_winter.png`
- `Terrain/cliff_winter_ice.png`

Every sheet is **512×448 px**, or **16×14 source cells**, and the existing audit confirms identical alpha geometry across seasons. This is the preferred Havenwild structural cliff art family once recipes are certified.

Important multi-cell source windows include:

| Source window | Source span | Meaning at Z104 |
| --- | ---: | --- |
| Bare rounded plateau construction | 5×5 | construction/reference template |
| Bare square plateau construction | 3×5 | construction/reference template |
| Grass rounded plateau construction | 5×4 | construction/reference template |
| Grass square plateau construction | 3×4 | construction/reference template |
| Water-facing valley A/B | 3×3 each | water/cliff recipe candidates |
| Water/bridge bay A/B | 2×4 each | bridge/water/cliff recipe candidates |
| Right-side terminal | 1×5 | source construction window; not automatically a 1×5 world stamp |
| Narrow cave host | 1×3 | cave recipe candidate |
| Wide cave host | 3×3 | cave recipe candidate |
| Ladder columns | 1×3 each | traversal connector candidates |
| Face columns | 1×3 each | repeatability still requires seam certification |
| Vine/climbable windows | multi-cell | climbable-face recipe candidates |

The old `diagonal_faces_and_ramps` and other broad regions remain useful only as inspection windows. They are explicitly **not runtime recipes**.

## `Rocks, Cliffs.png`

Pinned source: `Terrain/Rocks, Cliffs.png`

- Canvas: **192×128 px**.
- Classification: loose boulders, rock clusters, small rocks, and cliff debris.
- Structural cliff provider: **false**.

Connected artwork spans multiple source cells in several places, including large 2×3 and 2×2 boulders. These should be promoted as natural-object components with explicit object collision footprints. They must never resolve a Level 0→1 or Level 1→2 structural boundary.

Pass167Z104 removes this file from the structural cliff provider and cliff-recipe brush list while keeping it in the rock-object family.

## `Waterfall.png`

Pinned source: `Terrain/Waterfall.png`

- Canvas: **512×608 px**.
- Source grid: **16×19**.
- Classification: animated multi-cell structural water connector.

The audited frame envelopes include:

- Four south-facing frames, each **3×5 source cells**.
- Four west-facing frames, each **2×7 source cells**.
- Four east-facing frames, each **2×7 source cells**.
- A **3×7** auxiliary tiling/cap-parts window requiring final semantic decomposition.

A waterfall therefore cannot be promoted as a 1×1 terrain cell. Its final recipe also needs the cliff host, top-water socket, bottom-water socket, animation timing, collision boundary, occlusion, splash/contact region, and sound anchor.

## In-world composition target

The upstream demonstration scenes show large walkable plateaus and mountain/highland regions whose **perimeters** are assembled from cliff art. Havenwild should follow that visual logic:

- Platform interiors remain ordinary ground material.
- Structural Level data describes discrete platform regions.
- Cliff recipes render only where neighboring structural levels differ.
- Large mountains/highlands may span many world cells; their size is not determined by a source stamp's image dimensions.
- Complete multi-cell cave, ladder, bridge, ramp, and waterfall assemblies attach to compatible perimeter locations.
- Missing topology remains an editor diagnostic; it does not invent pixels or invisible collision.

## Pixel Studio normalization workflow

1. Open the third-party source atlas read-only on the exact 32×32 game grid.
2. Select one or more complete source cells/regions; Ctrl+click supports multi-selection.
3. Load the selected source region into the separate Havenwild working/assembly canvas at the same world-grid scale.
4. Never modify the source layer.
5. Record source span independently from world visual footprint.
6. Author structural host mask, collision edges, traversal edges, anchor, draw order, and occlusion independently.
7. Test the recipe on a large Level-based acceptance formation, not an isolated 3×3 tile sample.
8. Publish the recipe, runtime atlas entry, thumbnail, acceptance fixture, source hash, license, and attribution atomically.

## Runtime decision

Cliff rendering and procedural cliff collision remain disabled after this pass. Z104 normalizes the source truth; it does **not** prematurely reactivate rendering.

The next cliff implementation pass should extract and certify the minimum ElizaWy straight/corner/base/cave/ladder recipe set and build a large acceptance scene before PCG mountain rendering is restored.
