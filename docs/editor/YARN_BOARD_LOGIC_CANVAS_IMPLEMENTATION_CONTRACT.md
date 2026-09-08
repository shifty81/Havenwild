# Havenwild Yarn-Board Logic Canvas Contract

## Status

The Yarn-Board is an editor authoring surface, not a second runtime scripting engine.
The editor stores card placement and connection presentation; the build compiles the
operational graph into a compact runtime trigger table.

## Persistence boundary

Do not insert mutable canvas-only fields directly into the procedural scene rectangle
manifest. Store scene logic in a dedicated sidecar keyed by stable project scene ID:

```text
content/editor/scene_logic/<scene-id>.logic.json
```

The sidecar owns:

- stable node IDs;
- target scene/tile or target authored object ID;
- visual canvas positions;
- collapsed state;
- typed input/output pins;
- links;
- authoring comments and grouping.

The runtime build output owns only:

- trigger type and parameters;
- condition bytecode/data;
- action commands;
- stable target IDs;
- ordered outgoing edges.

Canvas positions, card sizes, selection, colors, and collapse state are stripped from
runtime output.

## Required data separation

```rust
pub struct LogicNodeAuthoring {
    pub id: LogicNodeId,
    pub name: String,
    pub target: LogicTarget,
    pub canvas_position: CanvasPosition,
    pub collapsed: bool,
    pub payload: LogicNodePayload,
    pub outputs: Vec<LogicLink>,
}

pub enum LogicTarget {
    SceneTile { scene_id: ProjectSceneId, x: i32, y: i32 },
    Object { scene_id: ProjectSceneId, object_id: ObjectId },
    Stamp { scene_id: ProjectSceneId, stamp_id: StampInstanceId },
    Scene { scene_id: ProjectSceneId },
    World,
}
```

A logic card's screen/canvas position must never replace its world target.

## Input model

Use pointer edge events rather than a single `is_mouse_down` boolean:

```text
PointerPressed
PointerMoved
PointerReleased
Cancel
```

The interaction state machine is:

```text
Idle
DraggingCard { node_id, grab_offset }
Linking { source_node_id, source_pin }
Panning
BoxSelecting
```

On link release, first resolve the target node ID using an immutable scan. Only after
that scan ends should the graph be mutably borrowed to insert the link. This avoids the
immutable/mutable nested borrow in the original draft.

## Undo and validation

Every completed card move or link change becomes one typed editor transaction.
Validation rejects:

- duplicate node IDs;
- self-links unless the node type explicitly allows loops;
- links to missing nodes or pins;
- invalid target scene/object/stamp IDs;
- action nodes with no executable command;
- cycles in graph families declared acyclic;
- runtime-only commands in client-authorable World Builder mode.

## Rendering order

1. world/scene canvas;
2. optional dim layer;
3. target anchor lines;
4. established yarn links;
5. active link preview;
6. cards and pins;
7. selection, context menus, tooltips.

The renderer must reset Macroquad camera/material state before returning to editor
chrome.

## Delivery sequence

1. typed sidecar schema and graph validator;
2. save/load and scene-ID migration;
3. card drag/pan/select interaction;
4. typed pins and link creation;
5. target-tile/object anchoring;
6. transaction/undo integration;
7. graph compiler and runtime trigger table;
8. World Builder permission filtering.
