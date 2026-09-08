# Havenwild Terrain Contact Import Surface Audit — Pass 167Z71

## Finding

The Z70 exact-paint refactor correctly removed direct shoreline-lifecycle use from ordinary F3 terrain painting, but it also removed the parent-module import for `normalize_lpc_authored_material_contacts_region`. Two unrelated and still-valid systems continued to call that shared function:

1. Startup migration and generated-scene cleanup.
2. The dedicated World Paint system after broad paint strokes.

Because both implementation files use `use super::*;`, the missing import in `crates/haven_game/src/main.rs` made the function unavailable and caused Rust error E0425 at both call sites.

## Repair

The import is restored once at the `haven_game` parent-module surface. No function body, call arguments, paint policy, hydrology radius, terrain material, atlas reference, or visual behavior changed.

## Scope distinction

This repair does not reintroduce the reported one-tile shallow-water halo regression:

- Exact F3/native Scene Editor painting routes through `TerrainPaintMode::Exact` and remains neighbor-neutral.
- Startup migration is a load-time compatibility path.
- World Paint is a separate broad authoring system whose changed region is intentionally normalized.

## Regression contract

The Z71 validator requires:

- Both existing call sites to remain present.
- The shared parent-module import to remain present exactly once.
- The function to remain publicly exported from `haven_assets::authored_terrain_contacts`.
- Ordinary runtime editor code to remain free of direct broad shoreline lifecycle calls.
