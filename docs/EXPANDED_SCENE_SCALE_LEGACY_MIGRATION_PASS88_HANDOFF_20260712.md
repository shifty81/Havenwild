# Havenwild Expanded Scene Scale + Legacy Migration — Pass 88

Date: 2026-07-12  
Baseline: `Havenwild_UpdatedSource_LpcExpandablePondFamiliesPass87_20260712.zip`

## Result

Havenwild's active scene dimensions are now **96 × 64 tiles** instead of **48 × 32 tiles**.

- Legacy scene area: 1,536 tiles.
- Active scene area: 6,144 tiles.
- Increase: **2× width, 2× height, 4× total editable/playable area**.
- Recorded future large-scene target: **144 × 96 tiles**.
- Recorded city/district target: **192 × 128 tiles**.

The 144 × 96 profile is not globally activated yet. The current `SceneMap` contract still uses one global width and height, so activating it now would make every interior, cave, connector, and outdoor scene nine times the legacy area. Pass 88 uses 96 × 64 as the safe production standard and records 144 × 96 for the later per-scene-dimension pass.

## Existing save migration

Existing 48 × 32 saves remain supported.

When an old save is loaded, Havenwild:

1. Detects the source map dimensions from the serialized map header.
2. Creates a 96 × 64 runtime scene.
3. Centers the old authored area at offset **+24,+16**.
4. Migrates terrain, heights, zones, objects, stamps, scene spawn, autotile overrides, transition rectangles, and transition target spawns.
5. Uses scene-appropriate fill around the migrated area:
   - exterior: grass
   - interior: wall
   - cave: cave wall
6. Writes the promoted scene as 96 × 64 on the next normal save.

This is a geometry-preserving migration. It does not silently regenerate or replace the player's existing island shape.

## Current source scenes

The nine Home Island source scenes are no longer left at legacy dimensions. They were promoted to 96 × 64 and now match the game/editor runtime contract directly:

- Farmstead
- North Road
- South Field
- East Woods
- Cave Mouth
- Tavern Interior
- Cellar
- Guest Floor
- Cave Depths

The old authored content is centered, while the additional scene area is available for editor expansion and later PCG authoring.

`tools/automation/worldgen/Promote-SceneScaleV88.py` provides a deterministic, repeat-safe promotion path for these source scenes.

## Runtime performance

Moving from 1,536 to 6,144 tiles per scene quadruples the scene grid. To prevent the game client from drawing every tile every frame, Pass 88 adds camera-aware terrain culling with a two-tile safety margin.

Only tiles intersecting the current camera view are submitted by the main runtime terrain pass.

## Contracts and tooling

Added:

- `content/worldgen/scene_scale_profile_v0_9.json`
- `tools/automation/worldgen/Promote-SceneScaleV88.py`
- `tools/automation/validation/checks/worldgen/Validate-ExpandedSceneScaleLegacyMigrationV87.py`
- `crates/haven_core/src/foundation/scene_size_migration.rs`
- `crates/haven_game/src/runtime_view_culling.rs`
- `docs/assets/previews/havenwild_scene_scale_pass88.png`

Updated:

- active `MAP_W` / `MAP_H`
- line-save map loading
- gameplay save world loading
- worldgen JSON loading
- source Home Island scene grids and coordinates
- scene rectangle and camera/editor contracts
- island graph scale descriptions
- worldgen generators that previously restored 48 × 32 assumptions
- web editor scale labels
- validation registry

## Using the pass on Windows

1. Back up `WORKSPACE\saves` before the first migration test.
2. Run:

```bat
tools/build/Build.cmd all
```

3. Launch `HavenwildClient.exe` and open the existing save.
4. Confirm the original authored area appears centered within the larger scene.
5. Press **F5** or use the editor's **Save All** after inspection to write the 96 × 64 format.
6. Open the same gameplay save in `HavenwildEditor.exe` to edit the expanded scene.

Opening an old save promotes its dimensions. It does **not** replace its terrain with a newly generated island. Use the explicit regeneration workflow only when a new PCG shape is desired.

## Validation completed in this environment

Passed:

- architecture validation: 179 Rust files
- content validation: 217 JSON files
- Havenwild open-world preset validation
- editor validators V54 through V79 in the aggregate run
- editor validators V80 through V87 individually
- Pass 88 expanded-scene validator
- JavaScript syntax checks
- Python syntax checks
- JSON parsing and scene-grid dimension checks
- archive integrity checks during packaging

The aggregate editor validation process exceeded the environment time limit after V79. V80–V87 were then run independently and all passed.

## Required local verification

This environment does not contain `cargo`, `rustc`, or `rustfmt`. Therefore these still need to be run on the Windows development machine:

```bat
cargo fmt --all -- --check
cargo check --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Then launch both executables and test:

- an existing 48 × 32 gameplay save
- a newly created 96 × 64 save
- editor loading of the gameplay save
- scene transitions
- object/stamp placement in the expanded margins
- camera movement and runtime tile culling

## Next implementation lane

With scene scale corrected, the next terrain task remains the **freeform LPC pond boundary resolver**:

- paint or PCG-generate an arbitrary pond footprint
- resolve eight-neighbor topology
- use mapped LPC outer edges, corners, and concave inner corners
- support holes, islands, coves, connected ponds, and river-fed pools
- store the semantic footprint instead of freezing raw atlas indices

After that, the scene system can move to per-scene dimensions so large exterior scenes can use 144 × 96 without forcing interiors and caves to the same size.
