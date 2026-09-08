# Havenwild Seeded Archipelago Spacing Pass 56

## Purpose

Pass 55 assembled the 43 exterior scene cells into ten structural islands, but the
archipelago preview still inherited hand-authored positions that could overlap. Pass 56
moves island placement into deterministic PCG so the World Routes map is readable and a
shareable world seed can produce a different archipelago for each future save slot.

## Locked structural counts

- 43 generated exterior scene cells
- 10 island landmasses
- 9 existing authored/interior scenes
- 52 expected scenes after full structural generation

## Seeded layout contract

The scene rectangle manifest now persists:

- `seed`
- `reroll_index`
- `layout_version`
- `canvas_size_px`: 1800 x 1200
- `outer_margin_px`: 70
- `minimum_island_gap_px`: 120
- `placement_mode`: `seeded_collision_safe_ring`

The mainland is centered. The nine surrounding islands are placed with deterministic
seeded candidates, bounding-box collision checks, a guaranteed ocean gap, canvas-margin
checks, and a deterministic fallback scan. The same seed produces the same positions;
different seeds reposition the surrounding islands.

The same world seed now feeds structural island generation, so coastline silhouettes
also change when the archipelago is rerolled.

## Native editor workflow

World Routes inspector and File menu now expose:

- **Regenerate Current Seed**: reproduce the saved seed and structural islands.
- **Reroll Archipelago Seed**: derive a new shareable seed, reposition all islands,
  regenerate their coastlines, rebuild harbor nodes, and keep custom route records.
- **Save All**: persist seed, reroll index, layout, assignments, routes, world, and PNGs.

The inspector displays the active world seed and configured minimum island spacing.

## Bash workflow

```bash
./tools/build/Build.sh island-previews
./tools/build/Build.sh island-previews 8675309
./tools/build/Build.sh island-reroll
```

`island-previews` now writes the collision-safe layout to the manifest and regenerates
the ten island PNGs plus `archipelago.png`. Supplying a number uses that explicit
shareable seed. `island-reroll` derives and persists the next deterministic seed.

## Preview rendering correction

Harbor route lines are drawn before island imagery. Island pixels therefore cover route
segments that pass underneath land instead of route lines visibly painting across the
islands.

## Main implementation files

- `crates/haven_world/src/archipelago_layout.rs`
- `crates/haven_world/src/scene_rectangles.rs`
- `crates/haven_world/src/island_pcg.rs`
- `apps/haven_editor_native/src/app/island_authoring.rs`
- `apps/haven_editor_native/src/app/island_workspace.rs`
- `apps/haven_editor_native/src/app/editor_menu.rs`
- `tools/automation/worldgen/Generate-StructuralArchipelagoPreviews.py`
- `tools/automation/validation/checks/worldgen/Validate-SeededArchipelagoSpacingV73.py`
- `content/worldgen/scene_rectangle_manifest_v0_8.json`
- `content/editor/world_canvas/structural_archipelago_workspace_contract_v0_1.json`
- `tools/build/Build.sh`
- `README.md`

## Validation completed in the packaging environment

- Architecture validation: 138 Rust files passed
- Content validation: 186 JSON files passed
- Havenwild open-world preset passed
- Pass 71 structural archipelago workspace passed
- Pass 72 island assembly / Save All / harbor routes passed
- Pass 73 seeded spacing / reroll passed
- Python syntax compilation passed
- All content JSON parsed successfully
- `./tools/build/Build.sh island-previews 1337` passed
- `./tools/build/Build.sh island-reroll` passed in a restore-safe test

The combined editor validation registry passed through Pass 69 before reaching the
existing slow asset-validation tail timeout. Passes 70 through 73 were then run and
passed individually.

Cargo and Rustc are not installed in the packaging environment. Run the definitive
Windows compile and Clippy gate with:

```bash
./tools/build/Build.sh all
```

## Current limitation / next integration point

The seed-driven layout and island generation APIs are ready for per-save use, but the
player-facing New Game / three-slot menu is not yet implemented. When that menu is added,
each new slot should create or accept a seed and call the same archipelago layout and
island generation APIs. Until then, reroll through World Routes or the Bash command and
Save All to create a different test playthrough.
