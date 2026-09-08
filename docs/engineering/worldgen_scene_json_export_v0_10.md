# Worldgen v0.10 Scene JSON Export

This pass adds runtime/editor save-back for generated worldgen scenes.

## What changed

- `crates/haven_core/src/worldgen_exporter.rs` exports the active `GameWorld` to worldgen scene JSON.
- `export_worldgen_pack_to_path(...)` is the public runtime bridge.
- `F11` in dev mode exports the current editor/runtime world to JSON.
- The World tab now has an `Export` button.
- The loader now reads exported `blocksMovement` and `occludesPlayer` object flags, so object footprint edits round-trip more correctly.

## Export output

```text
content/packs/worldgen_home_island_runtime_export_v0_10.json
content/worldgen/exports/home_island_v0_10/*_scene_export_v0_10.json
```

If export files already exist, they are backed up first:

```text
workspace/worldgen_backups/export_v0_10_<unix_seconds>/
```

## Recommended authoring flow

1. Load the v0.10 pack with `F10`.
2. Edit objects, footprints, terrain, zones, and transitions in dev/build mode.
3. Press `F11` or use World tab -> `Export`.
4. Validate the exported pack.
5. Reload the exported pack if you want to test the round trip.

## Current limits

- Exported JSON is normalized runtime JSON, not a byte-for-byte preservation of the original hand-authored v0.3 scene files.
- Object IDs are regenerated from runtime object kind/index/position.
- Exported art references use runtime placeholder asset IDs until production object art is wired.
