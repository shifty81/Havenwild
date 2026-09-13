# HW-EMBERWRIGHT-CANVAS-DOCKABLE-TOOLS-15

## Intent

Normalize the native editor toward the Emberwright model: one persistent canvas/document center with every specialized workflow expressed as configurable dockable or floating tools.

## Decision

Assets, Pixel Studio, Animation Studio, Character Studio, Logic Studio, and Sound Studio should no longer be treated as unrelated whole-editor islands. They become document types plus panels:

- **Canvas / Room Canvas** remains the permanent center.
- **Asset Authority**, **Atlas Assembly**, **Tile Palette**, **Inspector**, **Room Manager**, **Layer Stack**, **Console**, and **Validation** become dockable/floating tools.
- **Pixel Studio + Animation Studio** collapse into a Sprite Studio tool group around sprite/atlas documents.
- **Character Studio** becomes a character document plus rig, layer, equipment, and animation-preview panels.
- **Logic** becomes graph/script documents plus node palette, script, binding, and validation panels.
- **Sound** becomes sound graph/timeline documents plus mixer, source, instrument, and procedural-node panels.

## Atlas Assembly remains first-class

The atlas tool is not removed. It becomes a dockable/floating panel group that can load source atlases, show a 32x32 grid, select multi-cell shapes, drag puzzle pieces onto an assembly canvas, snap, rotate, flip, layer, assign sockets/anchors/footprints, preview adjacency, and publish certified semantic definitions.

This is the correct bridge from raw art to runtime/worldgen definitions. Source art remains immutable. Transforms are metadata on authored pieces, not destructive edits to source sheets.

## Room / canvas model

Emberwright should feel closer to a room/canvas authoring system:

- room/scene/map/interior/cave/UI/prefab documents open in the center;
- panels provide palettes, object browsers, inspectors, layers, timelines, nodes, sound tools, validation, and console output;
- a bad tool cache or malformed asset catalog may warn, quarantine, or regenerate, but cannot trap the editor shell.

## Migration rule

Preserve current Havenwild behavior first. Add generic contracts and panel registries beside current code. Route current workflows through adapters. Only then remove or rename old workspace concepts.

## Immediate follow-up implementation

1. Introduce a `ToolPanelRegistry` model.
2. Demote Assets from top-level workspace to Asset Authority panel.
3. Add an always-accessible Room/Game Canvas center.
4. Start collapsing Pixel + Animation into a single Sprite Studio panel group.
5. Prepare Character/Logic/Sound for document-plus-panel operation.
