# Havenwild Generated Project-Wide Normalization Audit

Generated: 2026-08-20T15:55:41.3873166-04:00

**Status: NEEDS WORK**

## Current authority checks

- Repository files scanned: 479993
- Root files: 6
- docs/current files: 15 / expected 8
- Retired live paths present: 0
- Architecture gate: FAIL
- Source validators: 46 / expected 10
- Build validators: 2 / expected 2
- Python bytecode/cache files: 1
- Loose temporary/log files in source: 1
- Native-editor direct rectangle calls (migration metric only): 105

## Scope rule

- Normalization must replace or retire parallel ownership; it must not add a second framework beside working code.
- Keep the seven project foundations: World, Terrain, Runtime, Assets, Simulation, Authoring, Persistence.
- F3 remains a lightweight adapter to shared world/authoring services; it is not a second native editor.

## Findings

- Unexpected docs/current files: HAVENWILD_W55R9_BUILD_POINT.md, HAVENWILD_W55_NORMALIZATION_CLOSURE.md, HAVENWILD_W56IJ1_WORLDGEN_STRUCTURAL_ROUNDTRIP.md, HAVENWILD_W56IJ2_SHRUB_LOADER_AUTHORITY.md, HAVENWILD_W56IJ3_EDITOR_CLIENT_VISUAL_PARITY.md, HAVENWILD_W56_PREBUILD_HANDOFF.md, HAVENWILD_W56_VISUAL_TRUTH_PREFLIGHT.md
- Rust architecture/file-size validation failed
- Source validator count is 46; expected 10
- Python bytecode/cache files found: 1

## Next

1. Run `9. Validate current source` and resolve the first current-authority failure.
2. Run `2. Build development (fast)` after source changes.
3. Do not increase Rust file-size exceptions to hide coordinator growth.
4. Keep expensive PCG/debug derivation out of draw loops and use retained visible-region caches.
