# Havenwild W56IJ2 — Published Shrub Loader Authority

**Pass:** `167Z109W56IJ2`  
**Date:** 2026-08-19  
**Status:** Source-ready; local Full quality gate pending.

## Finding

The W56 integrated acceptance board correctly authored 18 natural objects, but the real worldgen loader produced only 14. The four missing objects were `shrub_berry_01..04`. The same adapter gap affected production Home Island scenes and silently skipped 36 published shrubs: 8 Estate, 8 North Road, 8 South Field, and 12 East Woods.

## Repair

`worldgen_loader::object_kind_from_ids()` now recognizes the published `shrub_berry` family as `ObjectKind::Bush`, while retaining legacy `berry_bush` compatibility. The acceptance test now requires exactly 18 loaded natural objects and verifies all four exact shrub asset identities survive loading.

No art, terrain, structural level, or authored population coordinates changed. This pass repairs only semantic runtime adaptation of already-published assets.

## Source-side gates

- W56I/J integrated visual acceptance — PASS
- W56 scene population authority — PASS
- W56 editor/runtime object parity — PASS
- Integrated Visual Checkpoint — PASS
- World Visual Certification — PASS
- Published Home Island + W56 acceptance asset mapping sweep — 0 published unmapped assets

## Local acceptance

Run **Build & Verify → Full quality gate**. The critical result is:

`integrated_visual_acceptance::tests::w56_integrated_visual_pack_loads_through_the_real_worldgen_loader ... ok`

Then launch **Run → Run W56 integrated visual acceptance** for screenshot review.
