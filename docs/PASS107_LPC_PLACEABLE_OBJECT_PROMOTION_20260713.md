# Havenwild Pass 107 - LPC Placeable Object Promotion Plan

Pass 107 continues the asset placement lane without changing terrain or
renderer placement behavior.

## Current State

The project already has most of the infrastructure needed for placeable assets:

- `ObjectKind` semantic object identities;
- `PALETTE_OBJECTS` with 26 editor object entries;
- generated object atlas binding through `object_asset_entry`;
- `AssetPaletteCatalog` runtime-ready checks;
- `PlacedStamp`, stamp transactions, stamp rendering, selection, save/load,
  outliner, inspector, and footprint validation;
- object footprint registries and runtime collision integration.

The missing piece is promotion metadata. Raw asset dumps need to be turned into
approved records with source, license, atlas, rect, footprint, collision,
interaction, and palette metadata.

## Added

- `content/assets/lpc/lpc_placeable_object_promotion_plan_v0_1.json`
- `tools/automation/validation/checks/assets/Validate-LpcPlaceableObjectPromotionV119.py`

## First Promotion Groups

Pass 107 groups the current object palette into:

- Nature / Foraging: trees, bushes, boulders, ore nodes, mushrooms, herbs,
  stumps, logs.
- Town Props: crates, barrels, wells, scarecrows, fences, lamps, benches, signs.
- Tavern / Interior: tables, chairs, bars, kegs, beds, fireplaces.
- Buildings / Transitions: greenhouse marker, doors, stairs, cave entrance.

## Important Blocker

`cave_entrance` is intentionally marked `stamp_required`. The current object
atlas binding path covers 25 object kinds, but cave entrances need a multi-tile
stamp definition with visual, collision, interaction, transition, and cave
entry metadata. It should not be faked as a single 32x64 object.

## Source Pack Rules

Allowed-with-attribution sources such as ElizaWy LPC, LPC atlas packs, plant
repack, Hyptosis packs, and farm animals can feed promotion after their exact
source files and credits are retained.

Unknown-review packs stay quarantined until their license/source is resolved.
They can remain in the asset dump, but they should not become production
palette entries.

## Next Implementation Pass

The next practical implementation pass should:

1. Generate or select the canonical runtime object atlas manifest for the 25
   currently bound object kinds.
2. Add source-pack and source-rect provenance for each object.
3. Create a first stamp manifest for `cave_entrance`.
4. Split the editor object palette into the Pass107 groups.
5. Validate place, save, load, select, move, erase, collision, and interaction
   for every visible production object.
