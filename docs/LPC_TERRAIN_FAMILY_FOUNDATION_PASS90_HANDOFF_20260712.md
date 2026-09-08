# Havenwild Pass 90 — LPC Terrain Family Foundation

Date: 2026-07-12

## Purpose

Pass 90 replaces the experimental generic LPC coastline mapping with an explicit,
pinned terrain-family contract. Raw LPC cells are classified by authored role and
then baked into normalized Havenwild runtime assets. The source sheet is no longer
treated as a universal cell-index autotile.

This pass keeps the Pass 88 scene scale at **96×64 tiles** and includes the complete
Pass 89 runtime-root, paint-binding, save-root, and F3 input stabilization work.

## Active source contract

- Mapping: `content/assets/intake/lpc_terrain_family_mapping_v0_3.json`
- Lock: `content/assets/intake/lpc_source_lock_v0_1.json`
- Source: `assets/source/licensed/lpc_revised/terrain/terrain_summer.png`
- Source dimensions: 512×832 pixels
- Cell contract: 16×26 cells at 32×32 pixels
- License: OGA-BY 3.0
- Attribution: Lanea Zimmerman (Sharm), Eliza Wyatt (DeathsDarling)

Normal builds consume the pinned local source. They do not silently fetch or remap
against the current GitHub branch.

## Reviewed repeatable fills

The normalized base atlas now promotes reviewed source roles for:

- grass
- dirt
- sand
- shallow water
- deep water
- wet sand and mud-bank support
- river/ocean semantic variants

Shallow water uses the authored center at source cell `[1,21]`. Deep water uses the
authored center at `[1,24]`. Circular pond rings and transparent composition cells
are not repeated as open-water fills.

## Ordered transition families

Seven complete owner-side transition groups are baked, each with masks 0–15:

1. `grass_over_dirt`
2. `grass_over_sand`
3. `grass_bank_over_shallow`
4. `dirt_bank_over_shallow`
5. `sand_bank_over_shallow`
6. `shallow_rim_over_deep`
7. `riverbank_mud`

The generated transition atlas contains 112 variants. Runtime selection uses the
ordered center/neighbor pair rather than selecting from transition material alone.
Only the declared owner cell draws a boundary, preventing both sides of one boundary
from applying competing overlays. The shared `transition_atlas_groups` module is also
used by transition-rule draft diagnostics and auto-fixes, so an editor change to
`grass_over_sand` cannot be incorrectly rewritten to the generic grass material default.
The baker also preserves the authored 3×3 orientation (north=row 0, east=column 2,
south=row 2, west=column 0); the earlier inverted edge roles that produced
staircase and cross-shaped combinations are removed.

## Water-depth preservation

`TerrainFamily` now distinguishes:

- `ShallowWater`
- `Water`
- `DeepWater`

This allows sand banks to resolve against shallow water and shallow-depth rims to
resolve against deep water without collapsing every water tile into one identity.

## Rendering

The game and native editor now preserve the authored LPC RGB and alpha in the baked
transition atlas. The former semantic tint pass is disabled for these cells because
it could recolor grass banks as sand or collapse shallow/deep visual differences.
Procedural transition drawing remains available as a conservative fallback.

## Pond and inner-corner boundary

Every transition family records both:

- an authored 3×3 outer edge/corner block;
- an authored 2×2 inner-corner block.

Outer cardinal masks are active in this pass. The 2×2 inner-corner sources are
mapped, validated, and displayed in the conformance preview, but diagonal intent is
still folded into the existing four-way runtime request. True freeform coves, islands,
holes, narrow channels, and organically painted pond boundaries are the Pass 91 lane.

Pass 87 expandable rectangular pond stamps remain available and are not replaced.

## Build integration

`tools/build/Build.sh tiles` and `tools/build/Build.ps1 tiles` now run:

```text
tools/automation/terrain/Promote-LpcTerrainFamiliesV90.py
```

They no longer run the superseded Pass 86 coastline promoter afterward, so the new
atlas cannot be overwritten by the old three-group bake.

Recommended Windows verification:

```bat
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

## Validation

Added `tools/automation/validation/checks/terrain/Validate-LpcTerrainFamilyFoundationV93.py` and registered it in the
editor validation domain. It verifies:

- pinned source SHA-256 and dimensions;
- reviewed shallow/deep source cells;
- seven unique transition families;
- 3×3 outer and 2×2 inner source blocks;
- 112 complete runtime variants;
- atlas dimensions and alpha behavior;
- transparent mask-zero cells;
- absence of old opaque-white replacement tiles;
- ordered-pair runtime wiring;
- authored-color rendering in game and editor;
- typed `haven_assets` mapping catalog;
- Bash and PowerShell build wiring;
- deterministic rebaking.

Validation completed in the packaging environment:

- architecture: passed, 183 Rust files;
- content: passed, 218 JSON files;
- world preset: passed;
- editor validators V54–V80: passed before the aggregate timeout;
- editor validators V81–V93: passed individually;
- legacy transition validators V13–V15: passed;
- Python syntax checks: passed;
- deterministic Pass 90 bake: passed.

A Rust toolchain was not present in the packaging environment. `cargo fmt`, workspace
check, Clippy with `-D warnings`, tests, and release application builds must be run on
the Windows development machine with `tools/build/Build.cmd all`.

## Expected visual verification

Inspect:

`docs/assets/previews/havenwild_lpc_terrain_family_foundation_pass90.png`

Then verify in the client/editor:

- grass-to-dirt boundaries use grass-authored edges;
- grass-to-sand boundaries do not reuse water banks;
- sand banks draw only on shallow-water owner cells;
- shallow/deep boundaries use the depth-rim family;
- no raw 3×3 pond composition is repeated as open water;
- no white staircase or opaque fallback cells appear;
- scene transitions and existing saves remain functional.

## Next pass

Pass 91 should implement the freeform inner-corner and footprint resolver shared by
ponds, lakes, rivers, coves, islands, holes, and procedural shorelines. It should use
the 2×2 authored inner-corner metadata introduced here rather than inventing or
rotating unrelated source cells.
