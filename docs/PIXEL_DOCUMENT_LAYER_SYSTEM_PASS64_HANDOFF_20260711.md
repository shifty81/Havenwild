# Havenwild Pass 64 Handoff — Pixel Document & Layer System

## Baseline

Built from `Havenwild_UpdatedSource_NativeAnimationStudioPass63_20260711.zip`.

## Completed

- Added `havenwild.pixel_document.v0_2` layered document schema.
- Added named raster layers with visibility, lock, opacity, and five blend modes.
- Added non-destructive compositing and merge-down behavior.
- Expanded undo/redo to snapshot pixels, layer structure, and document metadata together.
- Added layer creation, duplication, deletion, reorder, rename, merge, visibility, lock, opacity, and blend controls.
- Added canvas resize, crop-to-selection, and transparent-padding trim.
- Added `.hhpixel/layers` persistence alongside flattened PNG and `.hhasset.json` sidecar.
- Added v0.1 single-image sidecar migration.
- Added 10-second recovery autosave and automatic recovery loading.
- Added recent-document tracking and excluded internal layer packages from image-library scans.
- Added a tabbed Pixel Studio inspector: **Layers & Document** and **Grid & Publish**.
- Added dirty and recovered-document status.
- Preserved explicit source-working-copy-runtime publishing boundaries.
- Added Pass 81 contract, validation registry entry, validator, and Bash command.

## Primary files

```text
crates/haven_pixel/src/document.rs
crates/haven_pixel/src/document_operations.rs
crates/haven_pixel/src/layers.rs
crates/haven_pixel/src/persistence.rs
crates/haven_pixel/src/library.rs
apps/haven_editor_native/src/app/pixel_studio.rs
apps/haven_editor_native/src/app/pixel_studio_render.rs
apps/haven_editor_native/src/app/pixel_studio_input.rs
apps/haven_editor_native/src/app/pixel_layer_panel.rs
apps/haven_editor_native/src/app/pixel_layer_input.rs
content/editor/pixel_editor/pixel_document_layer_system_v0_2.json
tools/automation/validation/checks/editor/Validate-PixelDocumentLayerSystemV81.py
```

## Verification completed in the packaging environment

Passed:

- Architecture validation: 171 Rust files
- Content validation: 198 JSON files
- Native Pixel Studio V79
- Native Animation Studio V80
- Pixel Document Layer System V81
- Island/client/environment validators V70–V81 individually
- Bash syntax
- Python compilation
- JSON parsing

The combined editor registry reached the existing slow validation tail and timed out after V69; V70–V81 were then run individually and passed.

Cargo, Rustc, Rustfmt, and Clippy were unavailable in the packaging environment. Run the definitive build on the Windows Rust workstation:

```bash
cd /c/Users/Shifty/Desktop/havenw
./tools/build/Build.sh pixel-doc-audit
./tools/build/Build.sh all
./tools/build/Build.sh pixel-studio
```

## Expected workflow

1. Open the native editor in Pixel Studio.
2. Select a CC0 image or create a blank document.
3. Open **Layers & Document**.
4. Build the asset with separate raster layers.
5. Save the working document.
6. Switch to **Grid & Publish** for grid, crop, pivot, footprint, and runtime target setup.
7. Publish a draft and approve it through Asset Intake.

## Explicit follow-on work

Pass 65 should add advanced selections and transforms: freehand/contiguous/color-range selection, floating selection layers, tile-aligned move, 90-degree rotation, nearest-neighbor scaling, clipboard transfer, and batch transforms across atlas cells.
