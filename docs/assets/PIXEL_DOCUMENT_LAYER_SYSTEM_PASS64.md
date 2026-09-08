# Havenwild Pixel Document & Layer System — Pass 64

## Purpose

Pass 64 turns Pixel Studio from a single flattened-image editor into a non-destructive, layered asset-authoring workspace. It is designed for adapting the project’s CC0 source sheets, creating original Havenwild art, and publishing reviewed slices without modifying generated runtime atlases directly.

## Document model

Pixel documents use schema `havenwild.pixel_document.v0_2` and contain:

- document identity, source provenance, output path, license, tags, grid, selection, pivot, and footprints;
- one or more named raster layers;
- per-layer visibility, lock state, opacity, blend mode, and image path;
- an active layer identifier;
- a flattened composite generated from the layer stack.

Supported blend modes are Normal, Multiply, Screen, Add, and Erase.

## Layer workflow

Open **Pixel Studio**, then select **Layers & Document** in the inspector.

Available layer operations:

- Add Layer
- Duplicate
- Delete
- Move Up / Move Down
- Merge Down
- Rename
- Show / Hide
- Lock / Unlock
- Adjust opacity
- Cycle blend mode

All pixel, layer, canvas, grid, selection, pivot, and footprint edits participate in the same document-level undo/redo history. The history stores complete metadata and layer snapshots with a 64-step limit.

## Canvas operations

The document panel supports:

- canvas resize up to 8192×8192;
- crop to the active selection;
- trim transparent padding;
- horizontal and vertical selection flips;
- non-destructive atlas-grid realignment;
- dirty-state indication beside the document name.

Canvas resize preserves the upper-left origin and clips content outside a smaller target canvas. Crop and trim adjust the pivot and atlas-grid offsets to remain local to the resulting canvas.

## Persistence layout

Saving a working document writes three related outputs:

```text
assets/source/original/pixel_studio/<asset>.png
assets/source/original/pixel_studio/<asset>.hhasset.json
assets/source/original/pixel_studio/<asset>.hhpixel/layers/*.png
```

The PNG is the flattened preview used by the existing image library. The JSON sidecar stores the document and layer metadata. The `.hhpixel` directory stores each editable layer separately.

Existing `havenwild.pixel_document.v0_1` sidecars remain readable. They migrate in memory to a single Base layer and are written as v0.2 on the next normal save.

## Autosave and recovery

Dirty documents autosave every 10 seconds to:

```text
WORKSPACE/recovery/pixel_studio/<asset-id>/document.json
WORKSPACE/recovery/pixel_studio/<asset-id>/layers/*.png
```

Opening an asset automatically restores a valid recovery package. The inspector shows that recovery occurred and asks the user to save normally to keep it. A successful normal save removes the recovery package.

Switching to another source image first attempts a recovery autosave for the dirty document being left behind.

## Recent documents

The library records the 16 most recently opened or saved documents in:

```text
WORKSPACE/pixel_studio/recent_documents.json
```

Recent working copies sort above the rest of the source library. Internal `.hhpixel` layer images are excluded from library scans.

## Source and publish boundary

CC0 uploads, intake images, and generated atlases remain source inputs. Pixel Studio saves project-owned working copies under `assets/source/original/pixel_studio` and publishes reviewed slices through the existing draft intake gate. Runtime atlas baking remains a separate explicit approval step.

The workflow is:

1. Open a CC0 or project source image.
2. Save a project-owned working copy.
3. Separate outlines, base colors, shadows, highlights, and guides into layers.
4. Adjust the atlas grid, crop, pivot, and footprints.
5. Save the layered document.
6. Select the runtime tile or object target.
7. Publish a draft slice.
8. Review and approve it in Scene Editor > Asset Intake.
9. Bake and reload the runtime atlas.

## Build and validation

```bash
./tools/build/Build.sh pixel-doc-audit
./tools/build/Build.sh pixel-audit
./tools/build/Build.sh all
./tools/build/Build.sh pixel-studio
```

The Pass 64 validator is `tools/automation/validation/checks/editor/Validate-PixelDocumentLayerSystemV81.py`.
