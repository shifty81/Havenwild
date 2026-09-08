# Pass 167R — World-to-Pixel Round-Trip Foundation

This pass reserves right-click in Scene Editor for contextual asset actions and adds the first live bridge into Pixel Studio.

## Implemented
- Right-click a Scene Editor terrain cell to open World Asset Actions.
- Edit Source in Pixel Studio for reviewed cliff and mountain-path sources.
- Preserve scene ID, cell selection, and camera while editing.
- Ctrl+S saves and marks affected editor caches for reload.
- Ctrl+Enter saves, returns to Scene Editor, restores the camera/selection, and invalidates the affected autotile cache.
- Generated outputs remain read-only.
- Explicit Erase remains available through the Erase tool rather than destructive right-click.

## Current reviewed bindings
The first live bindings cover grass-top cliff/mountain source and mountain-path ramp source from the approved OGA LPC cliff intake. Additional terrain families should be added through the binding catalog after exact source-cell review.

## Next
- Parse the JSON binding catalog instead of the initial compiled bootstrap mappings.
- Add overlapping layer selection (base terrain, transition, object, structure).
- Create Havenwild-owned overrides automatically for third-party sources.
- Refresh GPU textures in place rather than relying on the existing deferred asset reload request.
- Add test-map asset galleries and semantic cliff-role promotion.
