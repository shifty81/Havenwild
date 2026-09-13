# HW-ATLAS-MAPPER-LITE-UX-PCC-21

## Purpose

This pass keeps Atlas Mapper Lite lightweight while fixing the first usability issues found during live testing.

## Changes

- Adds the mapper to the internal Havenwild PCC Run menu through `run.atlas-mapper-lite`.
- Adds `tools/control/LaunchAtlasMapperLite.ps1` so the PCC can launch the tool without requiring a loose root script.
- Keeps the command launcher under `tools/launch/HavenwildAtlasMapperLite.cmd`.
- Raises the assembly canvas default zoom to readable 2x scale.
- Clamps canvas zoom so mouse-wheel zoom cannot become unusably tiny.
- Adds panel zoom status plus `2x` and `Fit` canvas view buttons.
- Prevents source-tile drops outside the assembly canvas from creating far-away pieces.
- Reverts existing-piece drags when released outside the canvas instead of letting accidental releases move assets off-canvas.
- Begins applying the Forge-style dark panel treatment to the mapper panels: stronger panel boundaries, header bands, and clear active/status surfaces.

## Rules preserved

- Source atlases remain immutable.
- The mapper writes recipe metadata only.
- Handoff JSON is still evidence for Asset Authority, not direct runtime publication.
- The full editor GUI treatment remains project-wide work, but the mapper is now the first focused certification surface.

## Next recommended pass

`HW-ATLAS-MAPPER-LIBRARY-BROWSER-22`

That pass should add a proper asset library tree that loads Havenwild's existing LPC/donor/external roots metadata without eagerly loading every image into memory.
