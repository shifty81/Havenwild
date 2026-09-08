# Pass 164A Pixel Studio Grid and Selection Audit

## Corrected

- A 64x64 character grid can no longer open with a 32x32 active selection.
- Frame selection resolves from grid width, height, origin, and spacing.
- Pixel selection remains available for free rectangular edits.
- Pixel and frame grids are independently visible.
- Character and object assets no longer receive terrain repeat previews.

## Not yet corrected

- Irregular atlas-entry rectangles are not yet represented.
- Object source-versus-generated atlas parity has not yet been certified.
- Asset roles still use a compatibility inference until sidecar metadata is expanded.
