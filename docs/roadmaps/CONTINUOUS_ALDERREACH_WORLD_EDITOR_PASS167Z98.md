# Continuous Alderreach World Editor Roadmap — Updated through Pass167Z102

## Completed in Z98 — Continuous canvas foundation

- One stitched global-tile Alderreach canvas.
- True 96×64 storage-partition dimensions.
- Partition borders hidden by default.
- Global tile cursor and semantic Inspector context.
- Optional partition, object, zone, and elevation overlays.
- Enter opens the selected partition in Scene Editor.

## Completed in Z99–Z102 — Global authoring milestone

- Cross-partition terrain paint gestures.
- Global zone/lot and elevation authoring.
- Rectangle, fill, replace, eyedropper, erase, and brush tools.
- Global object and stamp anchor placement with complete-footprint preflight.
- Global selection, copy, and paste across partition boundaries.
- One atomic typed undo/redo entry per gesture regardless of partition count.
- Atomic rollback when any target cannot be resolved.
- Correct save ownership through the affected partition scenes.

## Next milestone — Roads, structures, and production navigation

- Road spline/path authoring with shoulders and junction preview.
- Height-derived cliff preview and elevation sculpting refinements.
- Ramp, ladder, stair, cave, bridge, and waterfall sockets.
- Traversability and collision overlays.
- World Tree entries for Willowmere districts, harbor, properties, caves, ruins, and interiors.
- Named bookmarks, minimap navigation, selection history, and Play From Here.

## Acceptance rule

No editor operation may expose a storage-partition transition as a gameplay scene boundary. Partition identity may appear only in diagnostics, persistence inspection, streaming inspection, targeted repair workflows, and complete-footprint placement warnings.
