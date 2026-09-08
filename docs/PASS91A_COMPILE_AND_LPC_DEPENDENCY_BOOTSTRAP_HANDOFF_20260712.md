# Havenwild Pass 91A — Compile and LPC Dependency Bootstrap

## Corrections

- Removed the stale `tile_jitter` import from `haven_game`.
- Moved `tile_rect_intersects_bounds` before the test module to satisfy strict Clippy.
- Added `tools/automation/dependencies/Ensure-LpcDependency.py`.
- `tools/build/Build.cmd all` and `tools/build/Build.cmd tiles` now validate the pinned LPC dependency before continuing.
- Added `tools/build/Build.cmd lpc-sync` for an explicit dependency check/repair.

## Dependency behavior

The build reads `content/assets/intake/lpc_source_lock_v0_1.json`.

1. If every locked project file has the expected SHA-256 and dimensions, the build remains offline and immediately continues.
2. If a locked file is missing or invalid, the script acquires the exact pinned Git commit into `.local/dependencies/lpc/<commit>`.
3. Only files declared by the lock are promoted into the project.
4. Nearby LPC attribution text is copied with promoted files when present.
5. `HAVENWILD_LPC_REPO` may point to an existing local checkout.
6. `HAVENWILD_OFFLINE=1` prevents network repair and fails clearly when the dependency is unavailable.

The normal build never follows the moving `main` branch.

## Commands

```bat
tools/build/Build.cmd lpc-sync
tools/build/Build.cmd tiles
tools/build/Build.cmd all
```

## Terrain boundary

This pass makes Pass 91 buildable and reproducible. It does not claim that the squared wet-sand/dry-sand and diagonal shoreline topology is finished. Those visuals require the next resolver pass: eight-neighbor topology, explicit convex/concave roles, and layered wet-sand ownership rather than cardinal-mask-only selection.
