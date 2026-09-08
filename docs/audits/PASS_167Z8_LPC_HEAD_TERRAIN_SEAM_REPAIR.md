# Pass 167Z8 Audit — LPC Head and Terrain Seam Repair

## Screenshot diagnosis

### Missing heads

Universal LPC body sheets are intentionally neck-down anatomy. Pass 167Z7 generated `body_male` and `body_female` caches from `body/bodies/*` only and never composed:

- `head/heads/human/heads_human_male.json`
- `head/heads/human/heads_human_female.json`

Hair and clothing therefore rendered around an absent head layer.

### Hard road, field, and land seams

`LiveAutotileCache::resolve_autotile_cell` returns a resolved record only for tiles with a `TileAutoGroup`. Grass, dirt, sand, farm soil, and mud-bank tiles do not all have such a group. The base terrain cache previously copied transitions only from an existing resolved autotile record, so land-owned boundaries were dropped before rendering.

This is why road and cultivated-soil edges remained square even though the ordered LPC transition registry contained the correct grass-over-dirt rule.

### Pond-bank checker artifacts

`MudBank` used terrain-v7 source tile 124, a visibly sprouted mud/farm texture. Around natural ponds it appeared as scattered planted rectangles. `MudBank` now uses the LPC summer dirt fill; the adjacent water cell continues to own and draw the exact LPC dirt-bank transition family.

## Character correction

The Universal LPC cache generator now composes:

1. neck-down body sheet;
2. matching human head definition;
3. eyes, clothing, hair, and equipment remain separate runtime layers.

The generator revision is:

`167Z8-universal-lpc-head-terrain-seam-repair-v1`

The included generated body sheets were verified at 576×384 with nontransparent head pixels in all four facing rows.

## Terrain correction

`BaseTerrainChunkCache` now resolves terrain transitions directly when a cell has no same-family autotile record. Transition work remains retained and only occurs during cache synchronization/rebuild, not every frame.

The direct LPC water fill coordinates were intentionally left unchanged after checking the reviewed source-sheet grid. This pass does not replace correct LPC water cells with guessed coordinates.

## Validation completed in the packaging environment

- Universal LPC runtime-cache generator executed successfully.
- 119 component groups generated from 177 exact source sheets.
- Corrected male and female body/head sheets visually inspected.
- Content-integrity validator passed all 17 active checks.
- Production LPC runtime-binding validator passed.
- Python compilation passed.
- `tools/build/Build.sh` shell syntax passed.
- JSON output parsing passed.
- Patch checksums and ZIP integrity passed.

Cargo, Clippy, Rust unit tests, Windows build, live visuals, and FPS require local `tools/build/Build.cmd all` because Rust tooling is unavailable in the packaging environment.
