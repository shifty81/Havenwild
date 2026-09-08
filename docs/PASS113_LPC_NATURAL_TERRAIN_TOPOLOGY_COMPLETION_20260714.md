# Pass 113 - LPC Natural Terrain Topology Completion

Pass 113 expands the terrain-map-v7 replacement lane from the six-material
pilot to Havenwild's complete natural-terrain authoring set. The same generated
manifest is consumed by the in-client editor and normal client renderer.

## Promoted semantic terrain

- grass and dark/tall-grass ground
- dirt, sand, pebble shore, road, stone path, and mountain path
- cliff, mountain rock, and cave floor
- tilled soil, watered soil, and mud bank
- water, shallow/deep water, ocean aliases, river water, river mouth, and shore foam

Wet sand intentionally remains on the established coastline fallback because
the LPC source's `Water_Shallows_Sand` pixels contain visible water and are not
a dry wet-sand material. Floors, walls, bridges, crops, and greenhouse overlays
also retain their purpose-built render paths.

## Coverage contract

The generated manifest now records:

- every mapped Havenwild tile kind and distinct LPC source material;
- complete 14-arrangement coverage for each authored two-material pair;
- fill, outer-corner, inner-corner, edge, diagonal-split, three-material
  junction, and four-material junction counts.

This replaces ambiguous progress counts with topology-aware validation. A pair
is only complete when all 14 non-pure two-material corner arrangements exist.

The production editor terrain palette is expanded from seven to sixteen direct
brushes so the newly promoted ground, path, rock, cave-ground, farm-soil, and
water mappings are reachable through the same in-client editor workflow.

This rollup also restores the universal autotile policy JSON required by the
already-registered V113 validator; Pass 112 contained the validator but omitted
its contract file.

The object-footprint implementation was moved into its own focused foundation
module. This keeps behavior unchanged while returning the canonical tile/object
catalog below the project's 750-line architecture limit.

Pass 113A corrects the module split boundary so the `ObjectFootprint` derive
attribute travels with the struct instead of remaining at the end of the tile
catalog.

Pass 113B restores the `Clone`, `Copy`, `Debug`, `PartialEq`, and `Eq` derives
on `TileAuthoringStatus`, allowing the production-brush classification helper
to compile when it compares the returned status with `LpcProduction`.
