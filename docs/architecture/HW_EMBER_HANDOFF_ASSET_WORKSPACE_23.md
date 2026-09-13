# Ember Handoff: Havenwild Asset Mapping Workspace

Havenwild should remain the proving project, but the editor architecture should be generalized into Ember/Emberwright.

## Desired target

```text
Ember / Emberwright
├─ Generic editor shell
├─ Infinite canvas workspace
├─ Portable Forge GUI stack
├─ Dockable/floating/locked tool panels
├─ Asset Mapping Workspace
├─ Pixel/Animation/Tileset authoring
├─ Runtime project loading / PIE
└─ Havenwild as hosted game profile
```

## What to ingest from Havenwild

- Asset Authority / intake-stage rules.
- LPC/source-library provenance model.
- Atlas Mapper Lite source-to-handoff workflow.
- Tile-sheet mapped/unmapped status model.
- Pixel collision and layer-role authoring requirements.
- PCC-style gated branch/update workflow.

## What not to hard-code into Ember

- Havenwild-only asset family names as global engine concepts.
- Havenwild-only paths as core editor paths.
- Mapped-sheet green checks as runtime-published status.

## Experimental branch recommendation

Use:

```text
experiment/asset-mapper-workspace
```

Main remains the stable GREEN lane. The experiment branch carries mapper workspace, dockable panel, and portable Forge GUI extraction work until it is ready to merge back.
