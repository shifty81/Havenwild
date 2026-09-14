# HW-ASSET-MAPPING-CORRECTION-BRAIN-29

This pass keeps Havenwild standalone and GREEN-gated while making the Atlas Mapper more useful as a correction-learning tool.

## What changed

The mapper now distinguishes between ordinary draft source-cell use and learned correction-scene evidence.

New user-visible commands:

- **Learn Scene** / **Learn from corrected scene**
- **Next Missing** / **Generate next missing draft**
- selected-piece semantic role preset buttons in the inspector

Keyboard additions:

- `Ctrl+M` generates the next missing draft
- `Ctrl+Shift+Enter` learns from the corrected scene

## Why this matters

The previous generator could repeatedly place the same sampled cells. This pass lets the mapper read saved mapped-sheet records and skip already-mapped source cells when generating the next missing draft. The result is not final AI learning yet, but it is the first persistent correction-memory layer.

## Record upgrade

Mapped-sheet records now use:

```text
havenwild.atlas_mapper_mapped_sheet.v0_4
```

Each mapped tile still stores exact source identity:

```text
source_tile_x
source_tile_y
source_rect
semantic_role
layer
status
```

The sheet record now also stores:

```text
correction_scene_count
learned_from_scene
terrain_lane_role_binding
```

## Status meaning

```text
draft_mapped       = source cell appears in draft/layout metadata
learned_mapping    = source cell was accepted through Learn From Scene
validated_mapping  = source cell was included in an exported handoff
```

Runtime publication is still separate. Collision, sockets, terrain topology, layer authority, seasonal compatibility, and provider export are still future gates.

## Standalone / Ember mirror rule

Havenwild remains the standalone implementation lane. Ember should ingest the generic contracts and proven behavior from the GitHub-mirrored Havenwild repository after each GREEN checkpoint, not replace the Havenwild PCC authority during this phase.
