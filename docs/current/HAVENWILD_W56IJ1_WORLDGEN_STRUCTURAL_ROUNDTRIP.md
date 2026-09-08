# Havenwild W56IJ1 — Worldgen Structural-Level Round-Trip Repair

Pass: `167Z109W56IJ1`  
Baseline: `167Z59` cumulative overwrite patch  
Date: `2026-08-18`

## Trigger

The W56I/J integrated visual acceptance pack compiled successfully, but its real worldgen-loader test observed only structural Level `0` even though the authored acceptance scene contains Levels `0,1,2,3,4`.

## Root cause

`crates/haven_core/src/worldgen_loader_structural.rs` already contained a range-checked parser for `layers.structuralLevels`, but the active `worldgen_loader.rs` neither registered that module nor invoked it while materializing a `TavernMap`.

The inverse path had the same authority gap: `worldgen_exporter.rs` exported terrain/zones/objects but omitted `structuralLevels`, so an export/reload cycle could erase authored platform/cliff levels even after loading was fixed.

## Repair

- Wire `worldgen_loader_structural.rs` into the canonical worldgen loader.
- Parse `layers.structuralLevels` after terrain materialization using the same logical scene offset.
- Preserve explicit Level `0..=4`; preserve `null` / `"auto"` as automatic structural authority.
- Reject malformed dimensions and authored levels above `MAX_STRUCTURAL_LEVEL`.
- Export the full `structuralLevels` layer from `TavernMap`.
- Preserve automatic cells as JSON `null` rather than coercing them to Level 0.
- Extend the existing worldgen export/reload test to compare every structural cell.
- Add a direct loader test proving explicit Levels 0–4 and automatic cells survive JSON materialization.
- Harden W56I/J and worldgen-export validators so this wiring cannot disappear silently.

## Scope

No terrain artwork, cliff recipe, acceptance-board geometry, worldgen composition, or production-world data was changed. The W56I/J board remains the same authored 96x64 scene; only its structural layer now reaches runtime/editor storage correctly and survives export.

## Source-side validation

- W56I/J integrated visual acceptance validator: PASS
- Discrete structural-level authoring validator: PASS
- Worldgen Scene Export v0.10 validator: PASS
- Integrated Visual Checkpoint: PASS
- Python compile checks: PASS

## Local Rust gate still required

Run **Build & Verify → Full quality gate**. The important expected tests are:

- `haven_core::worldgen_loader::tests::authored_scene_loader_preserves_explicit_structural_levels`
- `haven_core::worldgen_exporter::tests::export_round_trips_worldgen_scenes`
- `haven_tools::integrated_visual_acceptance::tests::w56_integrated_visual_pack_loads_through_the_real_worldgen_loader`

The final integrated-acceptance assertion should now observe `[0, 1, 2, 3, 4]` rather than `[0]`.
