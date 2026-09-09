# HW-CLIFF-SOURCE-02 — Evidence Gate

This pass does not modify cliff runtime rendering.

## What SOURCE-02 proves

SOURCE-02 reverse-maps source-native ElizaWy 32×32 cliff cells into the official
ElizaWy Summer demo and Test Landscape using the opaque pixels of the original
pinned sheet as evidence. Matches may occur at any pixel offset; the tool does
not assume the demonstration image starts on a 32px grid.

The generated authority records:

- high-confidence source-cell occurrences;
- ambiguous occurrences separately;
- demonstrated N/E/S/W neighbors;
- connected demonstrated components containing c8/c15 cells;
- 5×5 visual context crops for human review.

## What SOURCE-02 does NOT prove

A matching cell is not automatically an independently placeable world tile.
A demonstrated component is not automatically a procedural recipe.

No runtime recipe is certified in this pass.

In particular, SOURCE-02 does not:

- resurrect `LPC_cliffs_grass.png`;
- certify the old 3×4 directional ramp;
- certify the historical six-cell ramp corridor;
- crop c8 into an invented standalone ramp;
- delete `oga_cliff_source`;
- alter structural collision or traversal;
- alter CliffShape15.

## SOURCE-03 entry requirement

SOURCE-03 may promote a source-native assembly only when its exact demonstrated
neighbors, footprint, anchor and source lineage are unambiguous enough to
describe without screenshot-driven synthesis.

If the official scenes leave an assembly ambiguous, it stays unresolved.
