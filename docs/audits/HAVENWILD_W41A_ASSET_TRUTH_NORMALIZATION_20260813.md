# Havenwild W41A — Asset Truth Normalization Foundation

**Baseline:** `Havenwild_CompleteSourceRollup_Pass167Z109W40_20260813.zip`  
**Baseline SHA-256:** `1f3258e9b59d1b4908486db4087379bda27062c42daf03df2e033d01048cb72e`  
**Milestone:** `Pass167Z109W41A`

## Purpose

W41A is the first content-normalization milestone after the W40 world/editor/runtime authority work. It does **not** redesign terrain, world authority, F3, scene persistence, or rendering. It inventories the currently competing world-visible asset identities and makes known quarantines/placeholders explicit before W42 introduces canonical PublishedWorldAsset identity.

## Concrete normalization corrections

- The active `ObjectKind` authority is `crates/haven_core/src/foundation/tile_object_catalog.rs`.
- Removed the dead, unreferenced duplicate `crates/haven_core/src/foundation/placeable_object_catalog.rs`.
- `Well` remains intentionally quarantined because the previous `well_pump` source is `Water Cooler.png`; W41 does not re-expose incorrect art.
- `GreenhouseMarker` remains a development-only placeholder backed by `construction_tape`; production greenhouse content is intended to migrate to `BuildingRecipe`.
- `CaveEntrance` remains outside the object-atlas binding and is tracked for structural connector/stamp authority.
- Known semantic substitutions are explicitly rejected: ladder-as-stairs, ottoman-as-bench, standing-screen-as-sign, and water-cooler-as-well.
- The historical V119 26-item promotion validator is unregistered historical reference and does not override later quarantine decisions.

## Normalization closure repairs discovered on the fresh W40 rollup

The current rollup exposed several small but real closure residues. W41A fixes them without reopening broad architecture work:

- split `crates/haven_world/src/continuous_surface.rs` tests into `continuous_surface_tests.rs`, reducing the production module below its architecture budget without changing runtime logic;
- split object-inspector geometry helpers into `object_inspector_geometry.rs`, reducing the inspector module below its architecture budget without changing editor behavior;
- align `tools/build/Build.ps1` Universal LPC runtime-cache revision with the already-current Bash wrapper/generator revision;
- update the W14 cliff validator to follow the shared cliff recipe after ownership moved to `haven_render`;
- update the W40 checkpoint validator to follow the Farmstead/PCG regression test after the continuous-surface test extraction;
- remove stale root package transport files `PATCH_MANIFEST.txt` and `SHA256SUMS.txt` from source authority.

The registered `source` validation profile passes after these repairs. W40, W40H1, W40H2, W40H3, and W41A targeted checkpoint validators also pass. Rust/Cargo and PowerShell are not installed in the packaging environment, so Windows compile/editor acceptance remains the local build gate.

## Inventory result

- Discovered asset identities: **130**
- Authored-scene asset IDs: **41**
- Canonical placeable IDs: **6**
- Generated LPC object IDs: **48**
- Legacy worldgen object IDs: **78**
- Cross-authority conflicts: **59**
- Authored-scene LPC candidates: **29**
- Authored-scene blockers: **12**
- Unexpected ObjectKind exposure issues: **0**

## Current authored-scene blockers

- `aging_barrel_row` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `bar_counter_stage_01` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `cave_mouth_entrance` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `greenhouse_stub` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `guest_bed` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `home_birch_tree_mature` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `home_tavern_mountain_entrance` — **MISSING** — Authored scene resolves only through missing legacy artwork: assets/generated/worldgen_v0_1/structures/home_island_structures_32.png
- `large_table_six_seat` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `old_growth_landmark_tree` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `ore_node_copper` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `stone_signpost` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.
- `stove_oven_2x3` — **PLACEHOLDER** — Legacy worldgen lookup explicitly declares source=scene_placeholder.

## Generated evidence

Run:

```bat
tools\automation\assets\Build-PublishedWorldAssetInventoryV1.cmd
```

or:

```bat
tools\build\Build.cmd asset-truth
```

The root project menu also exposes **Build world asset truth inventory**.

Generated evidence is written to `WORKSPACE/generated/world_assets/` and remains excluded from complete-source packaging by the established generated-data ownership policy.

## Acceptance

W41A is accepted when:

- the scanner deterministically discovers the current authorities;
- the active ObjectKind catalog is unambiguous;
- intentional quarantines are explicit rather than treated as drift;
- the four known incorrect visual substitutions remain rejected;
- the migration queue is finite and reproducible;
- the W40/H1/H2/H3 authority validators remain passing.

W41A does **not** require the 12 authored-scene blockers to be fixed. Those are the first migration targets for W42/W43.

## Next

**Pass167Z109W42 — PublishedWorldAsset registry + compatibility adapters**, built by evolving the existing `PlaceableAssetRegistry` rather than creating a competing second placeable registry.
