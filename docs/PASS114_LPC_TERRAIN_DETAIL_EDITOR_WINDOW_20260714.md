# Pass 114 - LPC Terrain Detail and Editor Window

Pass 114 keeps the proven grass/sand/dirt transition contract and addresses the
next visible production gaps without changing saved semantic tile codes.

## Terrain detail and seam correction

- Preserves all authored pure-fill alternates from `terrain-v7.png` instead of
  always selecting the first flat fill.
- Provides 62 reviewed pure-fill variants across the 16 promoted materials,
  including five grass fills, five sand fills, detailed dirt/rock/cave/path/mud
  fills, and animated-looking water/depth still variants.
- Chooses fill detail deterministically by cell coordinate so it never flickers.
- Keeps mixed transition selection exact and unchanged.
- Repacks 5,714 exact tuples plus fill variants from the near-32K source sheet
  into a compact 2,177 x 3,061 runtime atlas.
- Adds one-pixel edge extrusion and a small destination overlap to prevent
  camera/texture seams from exposing the clear background.

## World Editor workflow

- Terrain tools are now large thumbnail cards using the same mapped atlas as
  the client renderer.
- The obsolete visible Blend tab is removed from the tab sequence.
- The Min button and minimized draw path are removed.
- The editor can be dragged directly by its title bar without entering layout
  edit mode.
- The lower-right grip resizes the editor, with the result persisted through
  the existing layout save.

## HUD staging

The existing lower HUD remains anchored to the actual bottom edge and the
gameplay hotbar is now centered. Player portrait/health and configurable
NPC/group/multiplayer chat tabs remain the next HUD-specific pass after terrain
families are visually accepted.

## Validation

`Validate-LpcTerrainDetailEditorWindowV123.py` guards fill variants, compact
atlas packing, terrain thumbnails, editor movement/resizing, Blend-tab removal,
Min-button removal, and hotbar centering.
