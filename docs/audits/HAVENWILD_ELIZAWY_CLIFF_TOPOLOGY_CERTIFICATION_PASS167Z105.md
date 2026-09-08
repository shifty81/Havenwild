# Havenwild Cliff Topology Certification Audit — Pass167Z105

The Z104 audit established that several source sheets mix 1×N and multi-cell features on a 32×32 addressing grid. Z105 scrutinizes the actual `cliff_summer.png` geometry and certifies only envelopes that are visually unambiguous.

## Findings

1. The lower feature strip proves that the narrow cave, ladders and straight face columns are vertically composed **1×3** features. Splitting these into three independent cells would destroy the authored assembly.
2. The wide cave is a **3×3** host and must remain separate from the narrow cave; it may not be stretched.
3. The grass plateau examples are complete **5×4** and **3×4** construction references. Their cells are useful for later topology extraction, but the complete template is not equivalent to twenty or twelve freely placeable assets.
4. The water-facing constructions include at least a **3×3** valley and **2×4** bridge/water bay. These are kept as complete references until water and bridge sockets are explicit.
5. Straight face column A (`c10 r09-r11`) is the first horizontally repeatable candidate. Column B remains a complete 1×3 variant but is not certified for self repetition because its side-edge signature differs materially.
6. Waterfall frame envelopes remain 3×5 south and 2×7 east/west. Z105 now records those dimensions as world visual footprints while leaving structural host and animation sockets pending.

## Comparison target

The pinned ElizaWy demonstration scenes show broad traversable plateaus whose cliff faces form continuous boundaries, with caves, stairs/ladders, bridges and waterfalls embedded into those boundaries. This is the visual acceptance target for Havenwild.
