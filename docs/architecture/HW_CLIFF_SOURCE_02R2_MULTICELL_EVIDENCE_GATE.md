# HW-CLIFF-SOURCE-02R2 — Multi-Cell Evidence Gate

SOURCE-02 correctly refused to certify c8/c15, but its single-cell matcher was
too under-constrained to discover the source grammar. In the supplied audit:

- `DemoGame - 2 - Summer.png` matched only 6 source-cell identities, resolved
  only 1 scene position, and retained 29 ambiguous positions.
- `Test Landscape.png` matched only 2 source-cell identities and retained 20
  ambiguous positions.
- c8 observations: none.
- c15 observations: none.

Many ambiguous candidates occurred at x=0 and shared near-identical scores,
which indicates repeated terrain-color evidence rather than useful cliff
assembly evidence.

R2 therefore changes the evidence unit, not the confidence standard.

## R2 method

- enumerate source-native rectangles containing c8/c15;
- test 1×N, N×1, 2×2, 2×3, 3×2, 3×3 and larger nearby source rectangles;
- exact translation only;
- compare only opaque original-source pixels;
- require evidence distributed across at least two source cells;
- retain partial/strong classifications as evidence only;
- export exact source-stamp and official-scene crop pairs;
- write a CSV candidate index for review.

No source transform, rotation, mirroring, stretching, or foreign cliff-family
substitution is allowed.

## Runtime gate

This pass does not certify any runtime recipe.

If SOURCE-02R2 finds strong c8/c15 multi-cell candidates, SOURCE-03 reviews the
exact crop pairs and may promote only a demonstrated assembly.

If R2 still finds no strong evidence, Havenwild must use additional upstream
evidence such as configured Tiled/TSX relationships rather than inventing a
ramp/terminal grammar.
