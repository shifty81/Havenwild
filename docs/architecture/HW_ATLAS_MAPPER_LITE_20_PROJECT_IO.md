# HW-ATLAS-MAPPER-LITE-PROJECT-IO-20

This pass continues the lightweight Atlas Mapper direction without touching the full Havenwild editor surface.

## Goal

Create a simple, fast standalone GUI that lets a source atlas be treated like a box of 32x32 puzzle pieces. The tool keeps the source sheet immutable and writes mapper project data plus engine handoff JSON that can later be imported into Asset Authority.

## Added in this pass

- Registers `apps/haven_atlas_mapper_lite` as a Cargo workspace member.
- Adds/overwrites the standalone Macroquad mapper app.
- Adds repo-root-safe launcher at `tools/launch/HavenwildAtlasMapperLite.cmd`.
- Adds mapper project save/load support.
- Keeps engine handoff export separate from editable mapper project state.

## User workflow

1. Launch `tools/launch/HavenwildAtlasMapperLite.cmd`.
2. Load a PNG atlas.
3. Select 32x32 cells on the left.
4. Drag cells to the assembly canvas on the right.
5. Rotate, flip, delete, and reorder pieces.
6. Pick the current asset category.
7. Save a mapper project as `.hw-atlas-map.json`.
8. Export a handoff JSON for later engine import.

## Controls

- `Ctrl+O`: load PNG atlas.
- `Ctrl+Shift+O`: load mapper project.
- `Ctrl+S`: save mapper project.
- `Ctrl+E`: export engine handoff.
- `R`: rotate selected piece by 90 degrees.
- `H`: flip selected piece horizontally.
- `V`: flip selected piece vertically.
- `Delete` / `Backspace`: delete selected piece.
- `[` / `]`: move selected piece down/up in layer order.
- Mouse wheel: zoom hovered panel.
- Hold `Space` and drag: pan hovered panel.

## Output distinction

Mapper project files use:

```text
havenwild.atlas_mapper_project.v0_1
```

Engine handoff files use:

```text
havenwild.atlas_assembly_handoff.v0_2
```

The mapper project is editable tool state. The handoff is a candidate recipe for Asset Authority import. Neither modifies the source atlas.

## Still intentionally missing

The tool does not yet author sockets, footprints, collision, walkability, occlusion, traversal, animation frames, variants, provenance, or final published registry IDs. Those should come next as separate, gated passes.
