# HW-ASSET-UNDERSTANDING-02

This pass turns the existing Assets Studio into the first certification workbench
instead of another source-sheet browser.

## Important distinction

Havenwild already has broad mechanical 32x32 source indexing. That is useful for
addressing source pixels, but it does not prove that a cell is an independent
gameplay asset.

The editor now distinguishes:

- **Sources**: immutable source sheets/documents.
- **Review**: sliced or semantically mapped candidates that still need work.
- **Library**: runtime-certified published assets only.

## Lifecycle

`SOURCE ONLY -> SLICED -> SEMANTICALLY MAPPED -> RUNTIME CERTIFIED`

Examples:

- a complete roof spanning 5x3 cells remains one coherent component;
- a 3x4 tree remains one placeable object with a bottom anchor and trunk
  collision footprint;
- a cliff family becomes a topology/stamp family rather than anonymous cells;
- a character sheet becomes animation/frame metadata rather than loose tiles.

## Candidate analysis

`content/assets/asset_understanding_profiles_v1.json` defines candidate-analysis
requirements for the first six domains. These profiles are suggestions only.
They cannot certify content automatically.

The first detailed certification work is intentionally limited to:

`terrain -> water -> cliffs`

World generation should remain paused until those families have enough
runtime-certified topology to generate directly from authored vocabulary rather
than repair semantic terrain after generation.
