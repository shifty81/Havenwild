# Havenwild Native Pixel Studio Workflow — Pass 62

## Purpose

Pass 62 adds a first-class native Pixel Studio to Havenwild so project-owned and properly licensed source sheets can be inspected, sliced, corrected, edited, and published without rebuilding production atlases by hand.

The workflow is deliberately non-destructive:

- Source PNGs remain unchanged.
- Editing creates a project working copy.
- Atlas-grid correction changes metadata rather than moving pixels.
- Runtime promotion remains an explicit review and bake step.
- Every imported CC0 sheet remains tied to a source manifest and checksum.

This is the replacement for relying on rudimentary procedural art when better source assets are already available.

## Current source library

Pixel Studio scans these roots:

```text
assets/source/intake
assets/source/original
assets/source/cc0/user_uploads
assets/generated
```

Pass 62 imports 19 user-provided CC0 sheets into:

```text
assets/source/cc0/user_uploads/pass62
```

Their provenance, dimensions, checksum, license declaration, and promotion state are recorded in:

```text
content/assets/intake/cc0_user_upload_manifest_v0_1.json
```

These sources include interiors, castle/town pieces, cave kits, terrain, base characters, chickens, cats, horses, llamas, pigs, and environmental sheets. They are available for authoring immediately but remain `pixel_studio_source_only` until an explicit crop or slice is published.

A generated contact sheet is available at:

```text
docs/assets/previews/havenwild_cc0_pixel_studio_library_pass62.png
```

## Launching Pixel Studio

From Git Bash in the repository root:

```bash
./tools/build/Build.sh pixel-studio
```

This opens the native editor directly in the **Pixel Studio** workspace.

The usual editor launch also works:

```bash
./tools/build/Build.sh editor
```

Then choose **View > Pixel Studio** or use the workspace tab.

Validate the workflow and imported source library without compiling Rust:

```bash
./tools/build/Build.sh pixel-audit
```

## Workspace layout

### Left: CC0 / Project Images

The source library lists PNG files from the four supported roots.

- **Rescan** refreshes the library after adding files.
- **New 32x32** creates a blank project-owned tile.
- Click a row to open it.
- Up/down changes the selected source.
- Enter opens the highlighted source when no document is active.

Opening a source does not overwrite it. Pixel Studio assigns a working-copy output path under:

```text
assets/source/original/pixel_studio
```

### Center: permanent pixel canvas

The canvas provides:

- Nearest-neighbor rendering
- Transparency checkerboard
- Smooth stepped zoom
- Cursor-centered mouse-wheel zoom
- Middle-mouse pan
- Space + left-drag pan
- Pixel grid at useful zoom levels
- Configurable atlas grid
- Selection and pivot overlays
- A 3x3 repeat preview for seam inspection
- Clipping so oversized sheets do not draw over editor chrome

Keyboard controls:

```text
F                 Frame active document
[ / ]             Zoom out / in
Ctrl+Z / Ctrl+Y   Pixel undo / redo
Escape            Cancel gesture or leave Grid Realignment Mode
Shift+click        Select the atlas cell under the pointer
Alt+click          Set the pivot
```

### Top toolbar

Available tools:

- Pencil
- Eraser
- Fill
- Eyedropper
- Selection
- Line
- Rectangle

The toolbar also controls zoom, framing, pixel-grid visibility, and the 3x3 repeat preview.

### Right: slice and publishing inspector

The inspector contains:

- Image dimensions
- Active zoom/tool/license/dirty state
- Atlas cell width and height
- Logical grid X/Y offsets
- Selected crop rectangle
- Pivot
- Horizontal and vertical flip
- Bottom-center pivot shortcut
- Visual-footprint fitting
- Runtime draft target selection
- Save Working Copy
- Publish Slice Draft
- Havenwild working palette

## Recommended terrain-tile workflow

1. Open a CC0 terrain sheet.
2. Set **Cell W** and **Cell H** to the sheet’s real tile size, normally 32×32 for Havenwild world tiles.
3. Toggle **Grid Visible**.
4. When the source atlas is offset, activate **Grid Realignment Mode**:
   - Click once to arm it.
   - Click again to confirm.
   - Drag the logical grid into alignment.
   - Pixels are never moved.
5. Use Shift+click to select one grid cell, or drag with Selection for a larger crop.
6. Use the 3x3 repeat preview to inspect seams.
7. Correct pixels using Pencil, Eraser, Fill, Line, or Rectangle.
8. Set the pivot with Alt+click when needed.
9. Click **Save Working Copy**.
10. Choose a tile runtime target.
11. Click **Publish Slice Draft**.
12. In Scene Editor, review the draft through Asset Intake, approve it, then Bake + Reload.

## Recommended multi-tile object/stamp workflow

1. Open the source interior, town, cave, or environmental sheet.
2. Align the atlas grid to the source sheet.
3. Drag a selection around the complete object rather than one tile.
4. Use **Pivot Bottom** for a bottom-center anchor.
5. Use **Fit Visual** to derive the visual footprint from the selection and current grid size.
6. Adjust collision and interaction footprints in the published intake recipe when the visual area differs from the blocking/interactive area.
7. Save the working copy.
8. Select an object runtime target and publish the slice as a draft.
9. Approve and bake it through the existing Asset Intake workflow.
10. Use the resulting object/stamp in Scene Editor.

## Recommended character and animal workflow

The character frame contract remains:

```text
64x96 frame cells
bottom-center foot anchor
```

Animal and character sheets can already be opened, aligned, edited, sliced, and saved through Pixel Studio. Pass 62 does not yet provide the dedicated animation clip/timeline authoring workflow. Until that pass lands, animation sheets should remain source documents or individual draft slices rather than being incorrectly promoted as static terrain/object assets.

The planned animation extension should add:

- Named clips
- Direction rows
- Frame ranges
- Per-frame duration
- Loop and one-shot modes
- Frame preview/playback
- Event markers
- Foot/body/tool sockets
- Shadow pairing
- Collision and interaction tracks
- Publish to animation metadata rather than static Asset Intake targets

## Working-copy and publication rules

### Save Working Copy

Writes:

```text
assets/source/original/pixel_studio/<asset>.png
assets/source/original/pixel_studio/<asset>.hhasset.json
```

The sidecar stores:

- Source and output paths
- Dimensions
- Atlas-grid size and offsets
- Current selection
- Pivot
- Visual/collision/interaction footprints
- Tags
- License declaration

### Publish Slice Draft

Creates or updates a deterministic recipe in:

```text
content/assets/intake/asset_intake_catalog_v0_1.json
```

The stable ID contains the selected crop coordinates and dimensions, allowing many independent assets to be published from one source sheet.

Publication is intentionally a draft. It does not silently overwrite production atlases or make unreviewed assets live.

## Licensing boundary

The Pass 62 source manifest records the user’s CC0 declaration and a hash for each imported file. This enables direct project use under the declared license while preserving traceability.

The editor does not assume every file elsewhere in intake/generated/reference folders is CC0. Files outside the manifest continue to follow their existing project-owned, quarantined, or unverified status.

## Validation

Run:

```bash
./tools/build/Build.sh pixel-audit
./tools/build/Build.sh all
```

The dedicated validator checks:

- Native workspace and menu wiring
- `haven_pixel` crate structure
- Core tools and undo/redo
- Nearest-neighbor canvas behavior
- 3x3 repeat preview
- Non-destructive two-step grid realignment
- Working-copy and draft-publishing boundaries
- Active validation-registry status
- All imported CC0 file dimensions and SHA-256 hashes
- Bash entrypoints

`./tools/build/Build.sh all` remains the definitive Rust formatting, Clippy, tests, and packaged-app verification on the Windows workstation.

## Deliberately deferred

The following are not falsely claimed complete in Pass 62:

- Layer stack and blend modes
- Copy/paste and transform handles inside the pixel canvas
- Palette extraction and indexed-palette locking
- Dither, smudge, blend, shape brushes, and replace-color
- Tile-set 47-case/terrain-rule authoring
- Animation timeline and clip publishing
- Socket, hitbox, and frame-event authoring
- Bulk automatic segmentation of arbitrary sheets
- Native file-picker import from arbitrary external folders
- Direct multi-atlas repacking from Pixel Studio

Those should be built as follow-on passes on top of this non-destructive document, grid, slice, license, and publish foundation.
