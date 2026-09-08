# Tile Extraction Workbench Pass 45

This contract keeps tile-sheet intake explicit before source pixels are promoted into Havenwild runtime assets.

Required workbench modes:

- `grid_realignment`
- `tile_record_authoring`
- `license_gate`
- `promote_to_project_asset`

The workbench must retain source-sheet provenance, license state, tile rectangles, and promotion intent. Reference-only pixels cannot be promoted into runtime assets without a project-owned catalog entry.
