# Havenwild Runtime Path, Paint Binding, and Input Stabilization — Pass 89

## Purpose

This pass addresses the repeated runtime message:

```text
paint render binding skipped (The system cannot find the path specified. (os error 3))
```

It also consolidates save/layout/worldgen paths and prevents repeated F3/Shift+F3 actions while the key is held.

## Root cause

The game texture loader already had a development fallback based on `CARGO_MANIFEST_DIR`, while the world-paint transition resolver still passed `"."` as the repository root. Launching the executable from `target/release`, a packaged folder, or another working directory could therefore load the PNG atlas successfully but fail to find its companion JSON manifest.

Save slots, editor layout, worldgen load/export, paint material state, and render-cache paths were also resolved through several independent relative-path rules.

## Changes

### Unified runtime root

`crates/haven_game/src/runtime_config.rs` now resolves one cached runtime root in this order:

1. `HAVENWILD_ROOT`, when it points to a directory containing both `assets` and `content`.
2. Current working directory and its ancestors.
3. Executable directory and its ancestors.
4. Compile-time repository root as a development fallback.

The client logs the selected runtime root at startup.

### Save-root compatibility

The save root is resolved once and shared by the save-slot frontend and running game.

- `HAVENWILD_SAVE_ROOT` can override it.
- Existing saves under the current working directory are retained automatically.
- Otherwise saves use `<runtime-root>/WORKSPACE/saves`.

This avoids making existing slot saves appear missing after the path correction.

### Paint binding repair

All transition and render-binding calls now pass the resolved runtime root rather than `"."`.

The failure message now includes:

- resolved runtime root;
- material-state path;
- render-cache path;
- underlying filesystem error.

The scene resolver no longer loads the atlas manifest when the active scene has no paint material cells. A `0/0` paint-delta save therefore produces a valid empty binding cache instead of failing on an asset it does not need.

### Save directory preparation

`ClientSavePaths::ensure_directories()` now explicitly prepares parents for:

- metadata;
- world save;
- scene manifest;
- paint deltas;
- paint material state;
- paint render cache;
- previews.

### F3 input latch

F3 now uses a release-to-rearm latch. One physical key hold can only:

- open dev mode once; or
- close/save dev mode once with Shift+F3.

Keyboard repeat events can no longer generate several toggles and saves from the same hold.

### Startup module extraction

Startup world loading, coastline cleanup, and editor-layout loading moved from `main.rs` into `runtime_startup.rs` to keep the game entry point below its architecture line limit.

## Expected runtime log

A save with no paint deltas should now produce a line similar to:

```text
Startup paint render binding refresh: 0 atlas-backed paint tile(s) bound for <scene>; cache persisted
```

It should not repeatedly emit `os error 3` while crossing scene boundaries.

The first lines also report:

```text
Runtime root: C:\...\havenw
Runtime save root: C:\...\havenw\WORKSPACE\saves
```

## Windows verification

Run from the repository root:

```bat
tools/build/Build.cmd all
```

Then test both launch paths:

```bat
target\release\haven_game.exe
```

and from another current directory:

```bat
cd /d C:\
C:\Users\Shifty\Desktop\havenw\target\release\haven_game.exe
```

Verify:

1. The selected runtime root is the actual repository/package root.
2. Existing slots still appear.
3. No paint-binding path error repeats during scene transitions.
4. `world_paint_render_cache.json` appears under the active slot's `world_paint` folder.
5. Holding F3 does not repeatedly toggle dev mode.
6. Holding Shift+F3 performs only one save/close action.

## Validation completed in packaging environment

Passed:

- architecture validation across 180 Rust files;
- content validation across 217 JSON files;
- expanded scene scale and legacy migration V87;
- Pass 88 compile hotfix V88;
- Pass 88 Clippy hotfix V89;
- stamp inspector Clippy hotfix V90;
- native `StampUpdateRequest` import V91;
- runtime path/paint binding/input stabilization V92;
- ZIP integrity and diff whitespace checks.

The packaging environment does not contain Rust. Final `cargo fmt`, workspace check, strict Clippy, tests, and release builds must run on Windows through `tools/build/Build.cmd all`.

## Next implementation lane

After runtime paths are confirmed clean, proceed with the LPC Complete Water + Ground Transition Mapping pass:

- repeatable grass, dirt, sand, shallow-water, and deep-water fills;
- grass-to-dirt and grass-to-sand families;
- grass/dirt/sand-to-shallow-water banks;
- shallow-to-deep-water rings;
- outer and inner pond corners;
- river strips, bends, caps, and junctions;
- layered foam/depth overlays;
- generated visual conformance board before PCG promotion.
