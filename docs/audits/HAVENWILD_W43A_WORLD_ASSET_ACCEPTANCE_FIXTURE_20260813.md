# Havenwild W43A — World Asset Acceptance Fixture

## Purpose

W43A creates a deterministic diagnostic environment for the first published object/placeable migration. It does not certify artwork automatically. Its job is to put every current LPC-backed candidate under the same editor/runtime inspection conditions so semantic substitutions, scale, anchors, footprints, collision, interaction, sorting and occlusion can be accepted or rejected deliberately.

## Implemented

- added `Build-WorldAssetAcceptanceSceneV1.py`;
- generated `content/worldgen/scenes/world_asset_acceptance/world_asset_acceptance_scene_v1.json`;
- mounted the scene in the development worldgen test pack as `world_asset_acceptance`;
- laid out all 29 W42 LPC-backed authored-scene candidates exactly once;
- excluded all 12 W41/W42 blocker IDs;
- uses authored aliases in `assetId` and canonical W42 identity in `publishedAssetId`;
- derives visual/collision/interaction placement from published footprint metadata;
- embeds exact source path/rect, runtime-cache rect and foot anchor for diagnostics;
- registered `Validate-WorldAssetAcceptanceSceneV1.py` in source/full validation;
- added `asset-acceptance` build command and root command 35.

## Acceptance lanes

The fixture groups trees, berry bushes, boulders, forage mushrooms, herbs, wildflowers, reeds and the current fallen-log candidate into separated lanes on a 64x48 grass scene. This keeps large/tree footprints from hiding smaller object defects and makes variant-to-variant comparisons deterministic.

## Certification policy

Every fixture entry remains `CANDIDATE`. W43B is responsible for actual editor/runtime review. A record may be promoted only after semantic identity and all placement/presentation contracts are accepted. A visually plausible but semantically wrong source is rejected or reclassified rather than certified.

A preliminary generated-cache review already flags `fallen_log` for semantic review: its current LPC source is `assets/source/licensed/lpc_revised/Objects/Small Items/Lumber.png` with source rect `[130,32,53,54]`, which reads as lumber/wood pile artwork rather than an unambiguous fallen tree trunk. It remains candidate and should not be promoted without a deliberate decision or replacement source.

## Validation

`Validate-WorldAssetAcceptanceSceneV1.py` requires:

- 29/29 W42 candidates exactly once;
- all 12 blockers absent;
- candidate state preserved;
- fixture geometry matching the published footprint;
- exact provenance/cache/anchor diagnostic metadata;
- development test-pack mounting under `world_asset_acceptance`.

The registered source validation profile passes. Windows Rust compilation/runtime visual acceptance remains a local toolchain gate.

## Next

W43B: load `world_asset_acceptance` through the development test pack, inspect each lane in native editor and game runtime, correct semantic/anchor/footprint/presentation defects, and selectively promote accepted records to `CERTIFIED`.
