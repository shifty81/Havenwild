# Pass 149G — Operational Pixel Studio

Pass 149G replaces the single hard-coded `New 32x32` action with a metadata-backed new-document workflow and removes the manual-rescan requirement that made existing project assets appear unavailable.

## Implemented workflow

- Pixel Studio indexes project-owned, intake, CC0 upload, and generated image roots when the workspace becomes active.
- `New Asset` opens a modal rather than silently creating one fixed tile.
- Presets cover single tiles, tilesheets, sprite sheets, animation sheets, UI textures, object sprites, character layers, and free canvases.
- Canvas size, cell size, spacing, padding, and grid offsets are editable before creation.
- New files are project-owned and use the existing layered `.hhpixel` package plus `.hhasset.json` sidecar on save.
- Existing library entries open through the left Pixel Assets browser.
- `Ctrl+N`, `Ctrl+O`, and `Ctrl+S` are wired for the active Pixel Studio workflow.
- Existing autosave, layered editing, publishing, rulers, and the 6.25%–7200% zoom range remain active.

## Current boundary

The native shell still does not expose an operating-system file picker or arbitrary drag-and-drop path intake. `Ctrl+O` opens and refreshes the project asset library rather than bypassing project asset governance. Save As remains a later document-identity pass; normal Save writes the project-owned output path generated from the asset name.
