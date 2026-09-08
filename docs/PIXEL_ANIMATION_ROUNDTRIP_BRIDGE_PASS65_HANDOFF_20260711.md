# Havenwild Pass 65 Handoff — Pixel Studio ↔ Animation Studio Round-Trip

## Purpose

Pass 65 connects the two native Havenwild editor workspaces without merging their responsibilities. Animation Studio continues to own clips, directions, frame order, timing, events, pivots, shadows, and sockets. Pixel Studio continues to own layered raster editing, source preparation, undo/redo, selection, grid metadata, and reviewed publishing.

Both workspaces remain inside `HavenwildEditor.exe`.

## User workflow

1. Launch the native editor and open **Animation Studio**.
2. Open an animation source and select a clip and frame.
3. Press `E` or click **Edit Selected Frame in Pixel Studio**.
4. Pixel Studio opens the complete source sheet as a layered document, focuses the selected frame, and selects its **Animation** inspector tab.
5. Edit pixels or layers normally.
6. Use the optional previous/next onion-skin overlay and the live pivot, shadow-anchor, and socket guides.
7. Press `Ctrl+Enter` or click **Save Pixels & Return to Animation**.
8. Animation Studio returns to the same clip and frame with the refreshed source texture.

Use **Return Without Saving Pixels** to abandon the bridge session and return to the same timeline location without changing the animation source binding.

## Source and persistence policy

Imported CC0 source sheets are not overwritten. The first bridge save writes or updates a project-owned layered Pixel Studio working copy under:

```text
assets/source/original/pixel_studio/
```

The working copy consists of:

```text
<asset>.png
<asset>.hhasset.json
<asset>.hhpixel/layers/*.png
```

Animation metadata is rebound to the project-owned working-copy PNG after a successful save. Runtime animation publication remains a separate reviewed step.

## Safety rules

- The bridge stores the animation asset ID, clip index, and frame index.
- A save refuses to write if Animation Studio has switched to another animation asset.
- The frame rectangle must still fit inside the Pixel Studio document.
- Canvas crop, transparent trim, and resize are blocked while the bridge is active.
- Pixel edits, layers, opacity, blending, selection, and undo/redo remain available.
- Pivot edits in Pixel Studio are converted back from sheet coordinates to frame-local coordinates.

## Files added

```text
apps/haven_editor_native/src/app/pixel_animation_bridge.rs
content/editor/pixel_editor/pixel_animation_roundtrip_bridge_v0_1.json
tools/automation/validation/checks/characters/Validate-PixelAnimationRoundtripBridgeV82.py
docs/assets/PIXEL_ANIMATION_ROUNDTRIP_BRIDGE_PASS65.md
PIXEL_ANIMATION_ROUNDTRIP_BRIDGE_PASS65_HANDOFF_20260711.md
```

## Key files updated

```text
apps/haven_editor_native/src/app/mod.rs
apps/haven_editor_native/src/app/pixel_studio.rs
apps/haven_editor_native/src/app/pixel_studio_render.rs
apps/haven_editor_native/src/app/pixel_studio_input.rs
apps/haven_editor_native/src/app/pixel_layer_panel.rs
apps/haven_editor_native/src/app/pixel_layer_input.rs
apps/haven_editor_native/src/app/animation_studio.rs
apps/haven_editor_native/src/app/animation_studio_input.rs
apps/haven_editor_native/src/app/animation_studio_render.rs
apps/haven_editor_native/src/app/editor_menu.rs
crates/haven_editor/src/validation_registry.rs
tools/automation/validation/validate.py
tools/build/Build.sh
README.md
```

## Validation commands

```bash
./tools/build/Build.sh pixel-animation-audit
./tools/build/Build.sh pixel-doc-audit
./tools/build/Build.sh animation-audit
./tools/build/Build.sh pixel-audit
./tools/build/Build.sh all
```

The packaging environment did not contain Cargo, Rustc, Rustfmt, or Clippy. Static architecture/content checks and validators V71–V82 passed. The definitive Rust compilation and strict Clippy run must be performed on the Windows workstation with `./tools/build/Build.sh all`.

## Follow-on work

The next Pixel Studio pass should add advanced selection and transform tools: floating selections, freehand and color-range masks, tile-aligned movement, rotation, nearest-neighbor scaling, clipboard transfer, and batch atlas-cell transforms. After that, Palette Studio and full autotile-family authoring should follow.
