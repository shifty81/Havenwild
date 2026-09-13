# Ember Handoff: Native Editor Asset Workspace

This handoff tells Ember to ingest the Havenwild asset mapping/editor work as a generic editor capability, not as Havenwild-only code.

## Ember target

```text
Ember
├─ Project Manager / Landing
├─ Workbench / Infinite Canvas
├─ Asset Mapping Workspace
├─ World Canvas Editor
├─ Pixel + Animation tools
├─ Node/Logic tools
├─ UI tools
├─ Forge/PCC provider layer
└─ Cortex intelligence/automation bridge
```

Havenwild loads as a game project/profile inside Ember. Its terrain, cliffs, structures, objects, UI, gameplay metadata, and asset-family semantics become profile data over generic editor systems.

## Ingest first

- Dockable panel model
- Source atlas/tile sheet stack
- Per-tile mapping badges
- World canvas replacement/paint tools
- Layer rail and tool rail
- Pixel collision and socket editors
- Asset Authority handoff/export model
- Forge GUI portable widget contracts
- Internal PCC / Forge provider parity contracts

## Preserve

- Havenwild main branch remains the stable green lane.
- Experimental branch hosts the larger workspace conversion.
- Source assets remain immutable; metadata owns mapping and promotion.
