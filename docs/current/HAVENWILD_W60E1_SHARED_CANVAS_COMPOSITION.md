# Havenwild W60E1 — Shared Canvas Composition

W60E1 fixes the selected-region Pixel Studio bridge so a selection is a scene presentation scope rather than a terrain-only export.

## Authority

`PreparedCanvasComposition` gathers the selected scene rectangle into pixel-aligned locked reference layers for generated terrain, resolved terrain transitions, existing authored visual overrides, intersecting BuildingInstances, and intersecting objects/stamps. Pixel Studio receives those same layers before its editable authored layers are created.

The starter-cottage acceptance case is explicit: selecting a rectangle that visibly contains the cottage in Scene Editor must open a Pixel Studio document that contains the cottage at the same coordinates.

## Non-destructive rule

Reference layers remain locked. Painting continues on authored/derived layers. W60E1 does not flatten a BuildingInstance into terrain authority or rewrite semantic terrain when opening a selection.
