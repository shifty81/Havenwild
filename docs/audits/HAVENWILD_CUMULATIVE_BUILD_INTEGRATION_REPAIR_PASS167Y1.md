# Havenwild Pass 167Y1 — Cumulative Build Integration Repair

This cumulative overwrite patch supersedes Passes 167O, 167O1, and 167Y for a
Pass 167N complete-source baseline.

## Repaired integration defects

- Registered the existing `character_repository_catalog` module used by the
  character creator compatibility bridge.
- Imported the client worldgen test-world configuration function into runtime
  startup.
- Restored persistent `CharacterVitalsState` ownership on `Game` and loads it
  from the selected character profile, with a validated default fallback.
- Restored optional runtime HUD texture ownership for vitals, hotbar, and
  minimap frames.
- Added normalized procedural HUD fallbacks so absent frame art never removes
  the hotbar, minimap, clock, portrait, health, or stamina presentation.
- Wired Ctrl+Enter for world-asset Pixel Studio round-trip save and return,
  consuming the preserved scene cell, camera, semantic binding, and generated
  output protection fields.

## Build errors addressed

- unresolved `crate::character_repository_catalog`
- missing `client_worldgen_test_world_enabled`
- missing `hud_vitals_frame`
- missing `hud_hotbar_frame`
- missing `hud_minimap_frame`
- missing `character_vitals`
- native-editor dead-code warnings for the world-to-Pixel return path

Local Windows certification remains `tools/build/Build.cmd all`.
