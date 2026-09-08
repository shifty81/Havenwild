# Pass 138 — Shore/Water Material Lifecycle

Date: 2026-07-20

## Purpose

Pass 138 replaces duplicated editor-only shoreline cleanup with one bounded Havenworld resolver used by both local world-editor edits and full coastline generation.

## Wet-sand lifecycle

- Cardinal water contact promotes dry sand to generated wet sand.
- Removing the supporting water converts stale wet sand back to dry sand.
- Diagonal-only contact does not create wet sand.

## Foam lifecycle

- Shore foam is generated only on shallow water beside wet sand, pebble shore, or mud bank while another water neighbor keeps the water band connected.
- Foam without supporting shore or connected water normalizes back to shallow water.
- Foam remains a derived water semantic rather than a direct terrain brush.

## River-mouth lifecycle

- River water touching ocean water becomes a generated river-mouth blend.
- A river-mouth blend must retain both river and ocean support.
- Removing either side cleans the stale blend back to river water or shallow ocean.

## Ocean-depth lifecycle

- Deep ocean cannot directly touch land or generated shore cells.
- The immediate boundary becomes shallow ocean, including diagonal corner protection.
- Fully enclosed shallow ocean may return to deep ocean away from land.

## Integration

`normalize_shore_water_lifecycle_region` is exported by `haven_world::autotile`, invoked by the runtime editor's bounded normalization wrapper, and run after full-map coastline cleanup. The report records generated and removed wet sand, foam, river mouths, and depth changes.

## Validation

`tools/automation/validation/checks/terrain/Validate-ShoreWaterLifecycleV138.py` guards the registry paint modes, shared resolver, editor wiring, worldgen wiring, Rust regression tests, documentation, and build registry.
