# Havenwild Pass 62 Handoff — Native Pixel Studio Workflow

## Baseline

Built from `Havenwild_UpdatedSource_GenericMultitileStampSystemPass61_20260711.zip`.

## Result

Pass 62 adds the first functional native Pixel Studio vertical slice and imports the current user-provided CC0 PNG library as traceable source material.

The native editor now has five workspaces:

1. World Routes
2. Overworld Layout
3. Scene Bank
4. Scene Editor
5. Pixel Studio

Pixel Studio can open large source sheets, edit pixels non-destructively, correct atlas alignment, select slices, inspect tile repetition, assign pivots/footprints, save project working copies, and publish explicit Asset Intake drafts.

## Imported CC0 source library

- 19 PNG source sheets
- Stored under `assets/source/cc0/user_uploads/pass62`
- Manifested in `content/assets/intake/cc0_user_upload_manifest_v0_1.json`
- SHA-256, dimensions, original filename, license basis, and promotion state recorded
- Source files remain unchanged
- Runtime promotion remains explicit
- Contact-sheet review preview: `docs/assets/previews/havenwild_cc0_pixel_studio_library_pass62.png`

## New crate

`crates/haven_pixel`

Modules:

- `document` — RGBA document, metadata, tools, selection, history, save
- `library` — project/CC0/intake/generated PNG discovery
- `publish` — deterministic selected-slice publication into Asset Intake

## Native editor implementation

New modules:

- `apps/haven_editor_native/src/app/pixel_studio.rs`
- `apps/haven_editor_native/src/app/pixel_studio_input.rs`

Implemented controls:

- Pencil, Eraser, Fill, Eyedropper, Selection, Line, Rectangle
- Cursor-centered stepped zoom
- Middle-mouse and Space-drag pan
- Nearest-neighbor texture display
- Transparency checkerboard
- Pixel grid
- Atlas grid
- 3x3 repeat/seam preview
- Rectangular selection
- Shift+click atlas-cell selection
- Alt+click pivot placement
- Horizontal/vertical flip
- Bottom-center pivot
- Visual-footprint fitting
- 64-snapshot pixel undo/redo
- Working-copy save
- Draft publication to tile/object targets

## Atlas Grid Realignment Mode

The required protected grid-correction workflow is implemented:

1. First click arms the mode.
2. Second click confirms it.
3. Drag moves only `offsetX` and `offsetY` metadata.
4. Source pixels do not move.
5. Escape exits/cancels the mode.

## Bash workflow

```bash
./tools/build/Build.sh pixel-studio
./tools/build/Build.sh pixel-audit
./tools/build/Build.sh all
```

- `pixel-studio` launches the native editor directly in Pixel Studio.
- `pixel-audit` runs the dedicated V79 validator.
- `all` remains the definitive Rust build, lint, test, validation, and packaging command.

## Validation completed in packaging environment

- Architecture validation
- Content JSON validation
- Native Pixel Studio V79
- Imported CC0 dimensions and SHA-256 verification
- Python compilation
- Bash syntax
- Rust delimiter/static source sweep
- ZIP integrity

Cargo, Rustc, Rustfmt, and Clippy are unavailable in the packaging environment. The Windows workstation must run `./tools/build/Build.sh all` for definitive Rust compilation and strict lint verification.

## Important boundary

Pass 62 makes the assets genuinely authorable but does not automatically promote every uploaded sheet into runtime content. Each asset still needs a correct crop, grid, pivot, footprint, runtime target, and explicit approval. This prevents a full atlas or animation sheet from being incorrectly treated as one object or tile.

## Next recommended pass

**Pass 63 — Pixel Studio Animation and Advanced Editing**

Priority work:

- Animation clip/timeline authoring for animal and character sheets
- Direction rows and frame-range mapping
- Playback, frame durations, looping, and events
- Socket/hitbox/shadow tracks
- Copy/paste/rotate/mirror selection transforms
- Replace color, dither, brush shapes, palette extraction, indexed palettes
- Tile seam compare and 47-case autotile authoring
- Bulk sheet segmentation with review rather than automatic promotion
