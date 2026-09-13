# HW-EDITOR-ASSET-WORLD-MAPPING-PARITY-25

This pass locks the corrected direction for the Atlas Mapper and Havenwild native editor.

The standalone mapper should not remain a separate debug utility. It is the proving surface for the native editor's Asset World Mapping Workspace and the later Ember editor module.

## Target workspace

```text
Havenwild Native Editor
└─ Asset World Mapping Workspace
   ├─ Left: Source Atlas / Tile Sheet Stack
   ├─ Center: Real Game World Canvas
   ├─ Right: Asset Intake / Inspector
   ├─ Tool Rail: select, paint, replace, collision, sockets, layers, erase, sample, validate
   ├─ Layer Rail: terrain base, transition, overlay, detail, cliffs, structures, objects, collision, occlusion
   └─ Bottom: Problems, output, coverage, handoff/publish receipts
```

## Left panel

The left panel becomes the authoritative source sheet stack for the loaded project. It should load from the Havenwild asset lane instead of requiring manual one-PNG browsing.

Inputs:

- `content/assets/lpc/lpc_slice_catalog_v0_1.json`
- `content/assets/donor_reference/donor_reference_asset_catalog_v0_1.json`
- `content/assets/intake/external_asset_pack_contract_v0_1.json`
- `content/assets/intake/external_asset_roots_v0_1.json`
- `.local/havenwild_external_asset_roots.json`
- runtime/published metadata
- mapper project/handoff records

Each sheet card shows family, source path/hash, mapped coverage, issue count, and publish state.

## Center canvas

The center canvas must become a real Havenwild world canvas, not just a blank assembly board. It uses the same worldgen/layer/tile rules as the actual game/editor so corrections happen in the context where the tiles will render.

Required behavior:

- pan/zoom
- generated world preview
- editable tile replacement
- multi-layer drawing
- selection and sample tools
- undo/redo
- validation overlays
- actor/player-scale preview overlays

## Mapping state

A source cell can progress independently from the sheet:

```text
unmapped -> draft -> mapped -> validated -> published
```

A green tile check means source-cell metadata exists. A sheet-level green check means family coverage rules pass. Published/star means runtime authority accepted it.

## Why this belongs in the native editor now

The standalone tool can continue proving small features, but the real value comes when mapping is done against an actual generated Havenwild world. That is the same surface Ember needs later: a GameMaker-style workspace where project assets, world canvases, dockable tools, and inspectors are all one system.
