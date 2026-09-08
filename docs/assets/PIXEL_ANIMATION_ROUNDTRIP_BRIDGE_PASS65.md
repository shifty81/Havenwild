# Havenwild Pixel Studio ↔ Animation Studio Round-Trip Bridge

## Access

Both tools remain workspaces inside `HavenwildEditor.exe`.

- `./tools/build/Build.sh pixel-studio` opens Pixel Studio.
- `./tools/build/Build.sh animation-studio` opens Animation Studio.

## Editing an animation frame

1. Open **Animation Studio**.
2. Open a character or animal source sheet.
3. Select a clip and timeline frame.
4. Click **Edit Selected Frame in Pixel Studio** or press `E`.
5. Pixel Studio opens the complete layered sheet, focuses the selected frame, and activates the **Animation** inspector tab.
6. Edit pixels and layers normally.
7. Click **Save Pixels & Return to Animation** or press `Ctrl+Enter`.
8. Animation Studio reopens at the same clip and frame with its preview texture refreshed.

## Animation context in Pixel Studio

The active frame receives a green outline. Optional onion skin draws the preceding frame in blue and the following frame in red over the active frame position. Pivot, shadow anchor, and sockets remain animation metadata and are rendered as overlays.

The Animation inspector tab shows the source rectangle, clip direction, frame index, pivot, socket count, and the source path used before the edit.

## Non-destructive source handling

Imported CC0 sheets are never overwritten. Pixel Studio creates or reuses a layered project working copy under:

```text
assets/source/original/pixel_studio/
```

When saving through the bridge, the animation document is rebound to that working-copy PNG. The layered `.hhpixel` package and `.hhasset.json` sidecar remain the editable source of truth. Runtime publishing stays separate.

## Safety rules

Canvas crop, transparent trim, and resize are disabled while an animation-frame bridge is active because they would invalidate frame source rectangles. Pixel painting, selection, layers, opacity, blend modes, and undo/redo remain available.

**Return Without Saving Pixels** restores the same Animation Studio clip and frame without changing the animation source binding.
