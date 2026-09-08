# Havenwild Pass 167T — Client Worldgen Test World

During terrain/world-generation stabilization, the game client now loads the latest editor-generated world export as its default test world. If that export is unavailable, it loads the production worldgen pack. Only when both fail does it load the selected persistent save.

The selected save is not overwritten. Existing world-paint deltas are replayed over the test world so authoring changes remain visible.

Set `HAVENWILD_CLIENT_WORLDGEN_TEST=0` to restore normal selected-save startup.

Load order:

1. `content/packs/worldgen_home_island_runtime_export_v0_10.json`
2. `content/packs/worldgen_home_island_v0_10.json`
3. selected persistent save

This is temporary development behavior and should become an explicit Client Launch Mode once the world-generation lane is certified.
