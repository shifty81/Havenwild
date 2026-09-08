# Havenwild W80 — Tool Rail + Layer Rail Production Completion

Baseline: **W79H2 compiled/validator-clean editor interaction baseline**.

W80 finishes the two permanent authoring rails without restoring any of the duplicate GUI surfaces retired by W78.

## Tool Rail

- The permanent 46 px rail contains the common tools for the active studio/layer.
- Advanced Pixel effects and cross-studio Pixel Edit are retained through one **control-anchored overflow flyout** instead of expanding the permanent rail.
- Brush and symmetry flyouts now anchor directly beside their Tool Rail controls and draw in an overlay pass above Layers.
- Mouse-wheel scrolling remains available when a small window cannot show all primary tools.
- All tools still route through the same `UniversalTool` registry/adapters and shortcuts.

## Layer Rail

- The canonical Layer Rail remains the only Pixel layer lifecycle surface.
- Rows expose visibility, lock state, active state, dirty state, semantic preview badge, and bounded layer names.
- Large stacks are scrollable from header controls or the mouse wheel.
- Editable Pixel layers support drag-to-reorder. Locked/reference layers are structural reorder boundaries.
- The permanent action row is reduced to **Add / Duplicate / Delete / More**.
- **More** and right-click open the same compact menu for Move Up, Move Down, Merge Down, Rename, Duplicate, and Delete.
- Blend mode is visible in the footer and cycles through Normal / Multiply / Screen / Add / Erase.
- Layer opacity is a continuous pointer-captured slider, so the canvas never receives a paint gesture while opacity is being dragged.

## Pixel document support

`haven_pixel::PixelDocument` now provides exact layer reorder, opacity, and blend setters so the UI does not simulate production behavior with repeated button presses or unstable swaps.

## Gate convergence

The Windows Full Quality Gate now explicitly runs the W79 and W80 validators after W78. Rust compilation and the complete workspace test suite remain authoritative.

## Next

**W81** extracts/locks the shared raster-authoring core consumed by Pixel Studio, Animation Studio, World Pixel Mode, and Scene Pixel Mode.
