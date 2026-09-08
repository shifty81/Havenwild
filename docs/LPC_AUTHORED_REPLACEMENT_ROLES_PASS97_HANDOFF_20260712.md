# Havenwild Pass 97 — LPC Authored Replacement Roles

## Visual failure corrected

Painting sand over grass produced long grass teeth, square corner hooks, and
isolated grass fragments. The Pass 90–96 baker was color-classifying complete
LPC composition cells, expanding the selected mask, and treating the result as
an overlay. Ordinary grass texture inside the source tile was consequently
promoted as transition fringe.

Pass 97 stops synthesizing transition pixels from source colors.

## Runtime atlas rule

- north/east/south/west edges use the complete authored LPC source cell;
- the four adjacent outer corners use the complete authored source cell;
- verified 2×2 concave roles use their complete authored source cell;
- T, cross, and opposing-edge masks remain a clean semantic base tile until a
  reviewed authored replacement role exists;
- source pixels are never stretched, recolored, thresholded, or expanded.

Because transition textures draw after the base terrain, an opaque authored
cell naturally replaces the base tile. Source cells containing legitimate
alpha continue to composite over the semantic base.

## Validation closure

The previously missing V55 tile-extraction workbench contract is restored.
V108 now validates replacement-role coverage and rejects fabricated compound
masks. V111 locks the complete-cell model into the build.

## Apply and build

Extract the complete source rollup over the repository and run:

```bat
tools/build/Build.cmd all
```

Then restart the newly packaged client and test a single sand cell, a 2×2
block, an L-shape, a broad painted region, wet-sand boundaries, and shoreline
depth transitions.
