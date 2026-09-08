# Havenwild egui Lite Pixel Editor Host Panel v0.1

This panel is the planned lightweight pixel editor surface for world-tile authoring. It should be hosted by egui in the full editor and optionally exposed in the in-game dev overlay for controlled live editing.

## Goal

Author and refine canonical Havenwild world tiles without treating donor/reference packs as final runtime art by default. The panel edits strict `32x32` tile records and can show nested `16x16`, `8x8`, and `4x4` subcell masks for paint weights, shoreline detail, foam, debris, and autotile previews.

## Monolith boundary

- `haven_game`: runtime shell, hotkeys, preview/panel wiring only.
- `haven_editor`: editor commands, undo/redo, inspectors, validation, tool model state.
- `haven_assets`: tile records, generated atlases, donor/reference catalog, source/intake metadata.
- `haven_world`: deterministic paint, mirror, autotile, subcell mask logic.
- `haven_render`: preview composition, grid rendering, atlas draw helpers.

The pixel editor must not become a single giant runtime file.

## MVP tools

- pencil
- eraser
- fill
- line
- rectangle
- selection
- eyedropper
- horizontal mirror
- vertical mirror
- grid realignment preview

## Required panels

- 32x32 tile canvas
- subcell mask view
- layer stack
- tile record metadata
- palette swatches
- donor/reference browser
- 3x3 autotile preview
- validation messages

## Output policy

The editor should emit:

- individual tile PNGs
- `.hhasset.json` tile records
- optional baked atlas PNGs
- optional atlas manifests
- autotile rule draft JSON

Blocked or non-commercial donor/reference assets may be displayed as reference-only catalog entries, but they must not be baked into runtime outputs.
