# Havenwild Pass 61 Handoff — Generic Multi-Tile Stamp System

## Baseline

Built from `Havenwild_UpdatedSource_ProductionEnvironmentLibraryPass60_20260711.zip`.

## Result

Pass 61 turns the project-owned structure, tree, clutter, interior, town, and cave atlas entries into one runtime/editor stamp system.

Validated registry totals:

- 136 project-owned stamp definitions
- 109 multi-tile definitions
- Six atlas manifests/sheets

## Major source changes

### Core

- Added stable `StampInstanceId`.
- Added `PlacedStamp` with visual, collision, and interaction footprints.
- Added stamp placement, lookup, movement, erasure, collision, and walkability integration to `TavernMap`.
- Added backward-compatible line persistence for stamp instances.

### Assets

- Added `StampRegistry` over six project-owned manifests.
- Added Stamps to the shared asset palette.
- Normalized duplicate generated cave IDs in the environment generator.

### Authoring

- Added stamp selection and hit testing.
- Added typed insert/remove/move operations with atomic undo/redo.
- Added headless place/move/erase services.
- Added stamp clipboard, marquee, bulk move, duplicate, cut, paste, and delete support.

### Native editor

- Added searchable Stamps category and thumbnails.
- Added real atlas placement ghost and validity outline.
- Added stamp rendering, stable selection, outliner rows, inspector metadata, footprint overlays, scene status, and Scene Bank counts.
- Split clipboard helpers and transaction helpers to preserve module-size limits.

### Client runtime

- Loads the same stamp registry and atlas sheets.
- Renders stamps in the actor depth queue.
- Applies stamp collision to walkability.
- Draws an explicit fallback when an atlas entry cannot be loaded.

## Workflow

```text
Scene Editor
  > Objects layer
  > Assets
  > Stamps
  > select/search an entry
  > preview ghost
  > click to place
  > Select to move/duplicate/delete
  > Ctrl+Z / Ctrl+Y
  > Save All
```

## Bash commands

```bash
./tools/build/Build.sh stamps
./tools/build/Build.sh tiles
./tools/build/Build.sh all
```

## Validation completed in packaging environment

- Architecture validation: 152 Rust files
- Content validation: 192 JSON files
- Havenwild open-world preset
- Editor validation chain through Pass 76 before the existing combined-run time ceiling
- Production environment V77 individually
- Generic multi-tile stamp system V78 individually
- Python compilation
- Bash syntax
- Rust source delimiter-balance sweep

Cargo, Rustc, Rustfmt, and Clippy are unavailable in the packaging environment. `./tools/build/Build.sh all` on the Windows Rust workstation is the definitive compilation, formatting, Clippy, unit-test, and application-packaging run.

## Reference-art policy

The user-provided LPC, interior, castle, cave, terrain, and animal sheets remain reference-only. This pass promotes only project-owned Havenwild generated assets.

## Recommended next pass

**Pass 62 — Modular Building, Roof, Fence, Wall, and Cliff Kits**

Use the stamp foundation to add:

- Repeatable middle segments
- Fixed corners and end caps
- Door/window/gate inserts
- Roof and wall layer separation
- Rotation/mirroring rules
- Collision-safe stretch/zoop placement
- Building recipe previews and validation

After that, bind gameplay functions, sounds, animation, storage, crafting, lighting, and transitions to placed stamp instances.
