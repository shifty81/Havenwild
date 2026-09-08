# Pass 149A — Testable Foundation Gate

Pass 149A changes the project from feature-expansion mode to stabilization mode.

## Automated gate

`./tools/build/Build.sh all` now runs the deterministic runtime foundation smoke after Rust formatting, checking, strict Clippy, tests, and workspace build. The smoke tool is a non-graphical executable under `haven_tools` so it can verify persistence and asset contracts without opening a window.

The smoke test creates an isolated scratch root under `WORKSPACE/smoke_test/pass149a`, never the player's save directory. It verifies:

1. production asset-pack discovery;
2. stable source-cache creation;
3. semantic resolution for terrain, player, and object providers;
4. persistent character profile save/load;
5. dynamic unlimited-world discovery and metadata save/load;
6. character-world scene, position, reputation, relationship, and quest-state save/load.

The default scratch directory is removed after the run. `--keep-scratch` may be used for debugging.

## Commands

```bash
./tools/build/Build.sh smoke-runtime
./tools/build/Build.sh all
```

The smoke report is written to:

```text
logs/smoke/runtime-smoke-latest.json
```

## Manual launch certificate

After the automated build is green, the current build is considered testable only after a human verifies:

- frontend boot;
- character-first New Game and Load routes;
- profile persistence;
- dynamic world creation and launch;
- movement and camera;
- terrain/water/path/object/player rendering;
- F3 editor entry;
- terrain/object placement;
- save, exit, reload, and restored edits.

This pass does not claim graphical smoke automation or completed multiplayer transport.
