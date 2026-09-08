# Editor Asset Reference Browser

The in-game developer editor now includes an **Assets** tab that reads the donor/reference asset catalog and shows uploaded third-party sources as learning/reference material for Havenwild.

This browser is intentionally policy-aware. It is not a raw asset importer and it does not make restricted files available to the commercial runtime by default.

## Purpose

The browser exists so the editor and future Lite Pixel Editor can study and compare donor sources while Havenwild builds its own original tile sets. It supports tile-size adaptation work for 16x16, 32x32, 40x40, and 48x48 source packs.

## Filters

The in-game Assets tab supports:

- tile size / grid profile filter
- source family filter, such as terrain, water, objects, foliage, characters, icons, and Tiled fixtures
- policy filter, separating prototype-ingest candidates from reference-only and blocked sources

## Runtime Safety

A record being visible in the browser does not mean it is approved for shipping. Runtime use still requires:

1. license/source approval,
2. metadata-backed prototype import adapter,
3. local/user-supplied source files or quarantine path,
4. bake approval,
5. no raw third-party redistribution,
6. final validation before release packaging.

Non-commercial or unverified packs remain reference-only/blocked in runtime builds.

## Lite Pixel Editor Direction

The future Lite Pixel Editor panel should use this browser as a reference workbench. Allowed usage includes studying category coverage, tile dimensions, animation organization, palette behavior, and autotile layout. Blocked usage includes tracing restricted pixels, copying restricted palettes directly, or converting non-commercial free packs into Havenwild production assets.
