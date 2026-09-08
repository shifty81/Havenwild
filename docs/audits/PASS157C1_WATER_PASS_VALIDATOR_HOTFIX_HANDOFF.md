# Havenwild Pass 157C1 — Water Pass Validator Hotfix

## Purpose

Pass 157C removed the legacy per-cell water depth-overlay pass and replaced it with a flat semantic water surface pass. The Pass 153F validator still required the deleted `TransitionOverlayPass::Water` invocation.

## Changes

- Updated `tools/automation/validation/checks/terrain/Validate-WaterPassBatchingPass153F.py` to validate:
  - coherent atlas transition rendering,
  - semantic water surface/span rendering,
  - one shared animation-time sample per frame,
  - absence of the obsolete depth-overlay pass.
- Removed the unused `TransitionOverlayPass` enum.
- Removed obsolete water-only arguments from `draw_tile_transition_overlays`.
- Removed the unused CPU `draw_water_depth_mask` implementation and related imports.
- Preserved V7 transition authority, flat semantic water, shoreline masks, retained execution, and safe fallback behavior.

## Verification performed here

- Pass 153F validator executes successfully.
- Python validator syntax compilation succeeds.
- Static search confirms the obsolete water pass and depth-mask function are absent.

The authoritative Cargo, Clippy, test, and runtime verification remains the Windows full build.
