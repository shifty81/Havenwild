# Havenwild Atlas Mapper Lite

A lightweight native atlas handoff tool for assembling immutable 32x32 atlas cells into engine-readable asset definitions.

## Purpose

The tool is intentionally separate from the full Havenwild editor so asset shape mapping can stay fast and focused:

1. Load a source PNG atlas.
2. Browse the atlas as 32x32 selectable cells.
3. Drag cells onto an assembly canvas like puzzle pieces.
4. Rotate, flip, layer, and categorize pieces.
5. Export a JSON handoff that tells the engine how the asset should be assembled.

The source atlas is never modified.

## Run

```powershell
.\HavenwildAtlasMapperLite.cmd
```

or:

```powershell
cargo run -p haven_atlas_mapper_lite -- "path\to\atlas.png"
```

## Handoff output

The exported JSON uses `havenwild.atlas_assembly_handoff.v0_1` and records source rectangles, canvas grid positions, rotation, flips, layer order, category, and import notes. Runtime promotion still requires semantic role review, sockets, footprints, collision, traversal, animation metadata, license/attribution, and validation.
