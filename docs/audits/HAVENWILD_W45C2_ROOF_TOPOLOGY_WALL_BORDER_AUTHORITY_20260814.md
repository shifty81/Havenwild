# Havenwild W45C2 — Roof Topology + Exact Wall-Border Authority

W45C2 keeps roof implementation on the normalized PublishedWorldAsset/BuildingRecipe path without guessing atlas cells. The pinned LPC roofing sheets are complex multi-cell source grammars, so this pass establishes topology authority first and publishes only the exact wall-border region that has been reviewed.

## Roof authority

`content/buildings/roof_topology_contract_v1.json` defines the roof as a BuildingInstance shell assembly rather than a monolithic placeable. Required vocabulary includes field, eaves, rakes, horizontal/vertical ridges, gables, hips, valleys, inner/outer corners, and trim. Generated runtime atlases remain cache-only.

Normal roofs stay attached to the same multi-level `BuildingInstance` as ground floors, upstairs and basements. Roof visibility/cutaway is camera-local and may never mutate shared world state, collision, persistence or multiplayer authority.

## Exact Wall Border candidate

`wall_border_formal_crown_repeat` is promoted through `PublishedWorldAssetRegistry` from:

- source: `Structure/Wall Borders/Formal Crown Molding.png`
- exact source rect: `[0,64,32,32]`
- runtime cache rect: `[0,0,32,32]`
- topology: repeat segment on X
- certification: CANDIDATE

The first four bottom-row 32x32 cells are pixel-identical, so one exact cell is the repeat authority. `structure_roof_trim_acceptance` lays five copies side-by-side for seam inspection.

## Deferred intentionally

All seven roofing source sheets remain unreviewed at exact-component level. W45C2 does not publish a roof merely because a cell is non-empty. W45C3 will use the local coordinate review boards to select exact field/edge/ridge/gable/hip/valley/trim regions.

## Validation

- W45A structure source inventory: 98/98 sheets, 11 reviewed exact-source sheets after W45C2
- W45C1 surface/building visibility authority: PASS
- W45C2 roof topology + exact wall-border authority: PASS
- `tools/build/Build.sh structure-roof-trim`: PASS
- Windows Rust compile: pending local toolchain gate
