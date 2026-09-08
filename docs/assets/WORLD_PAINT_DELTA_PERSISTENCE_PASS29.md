# World Paint Delta Persistence Pass 29

This pass makes the world paint backend persist each editor/dev-overlay paint stroke as a deterministic operation delta.

## Purpose

The paint brush can already write canonical 32x32 world tiles while reporting 16x16 / 8x8 / 4x4 subcell coverage. This pass adds the missing persistence contract so those edits can later be saved, replayed, synchronized, migrated, and promoted into the multiplayer host/server operation stream.

## Authoritative state

Paint deltas store:

- sequence number
- scene id
- brush center
- changed bounds
- material family
- target layer
- subcell mode and grid
- strength
- radius
- painted tile count
- affected subcell count
- resolved tile kind
- autotile refresh request/status

## Client-derived state

The delta log does not store raw rendered shoreline pixels, foam overlays, decorative variation, or debris visuals. Clients derive those visuals from deterministic manifests after the authoritative material/tile operation is applied.

## Current file path

```text
WORKSPACE/generated/world_paint/world_paint_deltas_v0_1.json
```

The file is intentionally inside `WORKSPACE/generated` for the prototype. Later save/multiplayer work can migrate these records into `.hhsave` scene deltas or host/server operation logs.

## In-game editor behavior

The `Paint` tab now persists a delta after every successful paint stroke. The panel shows the last delta status and sequence count.
