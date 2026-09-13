# HW-ATLAS-MAPPER-SCENE-DRAFT-FORGEGUI-24

This pass corrects the Atlas Mapper Lite direction after testing showed that Auto Map created a scrambled pile of unrelated pieces.

## Behavioral correction

`Build Scene Draft` now means: find a coherent source-window or source-row sample from the loaded sheet, preserve sheet adjacency, skip mostly empty cells, and create a reviewable correction scene. Generated pieces are not final art and are not runtime-published assets. They are source-linked draft cells that the user corrects, deletes, layers, saves, and exports as mapper evidence.

## Forge GUI correction

The standalone app now presents itself as `Havenwild Asset Mapping Workspace`, with a Forge-style shell, workspace rail, dock-tab treatment, scene canvas naming, and inspector text that explains what generated pieces are for. This is still Macroquad-rendered and not the final generic dock manager, but the surface now points toward the same panel model intended for Ember.

## Asset lane intent

The mapper remains Havenwild-specific for now, but its contracts are shaped for later Ember ingestion. The expected production path is:

1. Load Havenwild asset families from the asset lane.
2. Show mapped/unmapped status per source sheet.
3. Build source-linked scene drafts.
4. Correct semantics, layers, sockets, and collision.
5. Export handoff evidence.
6. Promote only validated candidates into runtime metadata.

## Why generated pieces exist

They are correction handles. A generated draft gives the mapper an initial scene to edit. The user should not have to arrange random scraps; the tool should create useful source-linked starting points that become better as semantic/collision/layer metadata is added.
