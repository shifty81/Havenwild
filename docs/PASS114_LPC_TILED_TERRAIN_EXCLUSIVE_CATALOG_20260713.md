# Pass114 LPC Tiled Terrain Exclusive Catalog

Pass114 makes `terrain-map-v7.tsx` the complete catalog source for mapped LPC
terrain replacement art.

The prior passes proved that the Tiled terrain-map source contains the prettier
corner cells, but the runtime still let older same-family autotile and transition
overlay paths draw on the same boundary cells. That caused green rings, stacked
shoreline art, and grid-like visual artifacts.

This pass changes the rule:

- `terrain-map-v7.tsx` exports all 34 Tiled terrain types and all 15,562 corner
  tuples into the generated manifest.
- Current Havenwild `TileKind` aliases still decide what is paintable today.
- Lava, snow, ice, holes, alternate water, extra mud, rock, stone, dirt, and
  grass variants are cataloged for promotion, but not exposed as editor brushes
  until matching semantic materials exist.
- A mapped boundary has one owner side based on terrain priority.
- Older live-autotile base art and transition overlays are skipped on mapped
  boundary cells so Tiled replacement art is not stacked with legacy systems.

The planning report is generated at:

`docs/assets/HAVENWILD_LPC_TERRAIN_MAP_V7_FULL_CATALOG_PASS114.md`

