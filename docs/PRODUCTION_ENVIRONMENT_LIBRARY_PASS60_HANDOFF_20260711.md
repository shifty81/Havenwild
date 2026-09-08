# Havenwild Pass 60 Handoff — Production Environment Library

## Baseline

Built from `Havenwild_UpdatedSource_ProductionTerrainTilesPass59_20260711.zip`.

## Completed

- Promoted all 32 generated semantic terrain entries into the live `TileKind` catalog.
- Added four deterministic visual variants per semantic tile.
- Shared tile variant selection between client and native editor.
- Expanded the searchable live object palette from 12 to 26 object kinds.
- Rebuilt the project-owned 32×64 object atlas.
- Corrected generated object drawing to use bottom/foot anchors in client and editor.
- Added project-owned interior, capital/town, and cave authoring stamp atlases.
- Added reference-coverage metadata for the uploaded examples without packaging their pixels.
- Split tile/object catalog definitions from `foundation.rs`.
- Split editor palette defaults from `haven_editor/src/lib.rs`.
- Split runtime object rendering from `runtime_draw.rs`.
- Added Bash generation wiring and V77 validation.

## Live now

- 32 searchable/paintable terrain tiles.
- 4 stable variants per terrain tile.
- 26 searchable/placeable object kinds.
- Client and editor use the same generated atlas bindings.

## Authoring-ready but not generic-runtime-bound

- 24 interior stamps.
- 24 capital/town stamps.
- 24 cave stamps.

These require the next generic multi-tile stamp workflow before promotion.

## Reference-only

All user-uploaded mixed-provenance sheets and animal sprites remain reference-only. No source pixels or palettes were copied.

## Build

```bash
cd /c/Users/Shifty/Desktop/havenw
./tools/build/Build.sh tiles
./tools/build/Build.sh all
```

## Packaging environment verification

Passed:

- Architecture validation across 146 Rust files.
- Content validation across 191 JSON files.
- Open-world, editor, asset-palette, asset-intake, camera, world-canvas, Scene Bank, island assembly, seeded archipelago, client save, and Pass 76 validators.
- Pass 77 production environment validation.
- Python compilation.
- Bash syntax validation.
- Full JSON parsing.

Cargo/Rustc are not installed in the packaging environment. Run `./tools/build/Build.sh all` on the Windows Rust workstation for definitive formatting, Clippy, tests, and packaged executables.
