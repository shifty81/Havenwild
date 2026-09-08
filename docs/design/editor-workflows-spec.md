# Editor Workflow Specification

Date: 2026-05-24

## Goal

Define the exact editing surfaces, edit-session flow, and per-tool responsibilities for the runtime overlay, standalone Rust editor, and future web editor.

## Editing Surfaces

### 1. Player Construction Mode

Purpose:

- build and remove floors
- place walls and doors
- assign room intent
- place decor/furniture within allowed rules

Rules:

- entered from an in-world trigger or future build menu
- edits are staged before accept/revert
- unavailable actions explain why they are blocked
- simulation pauses or soft-pauses while the mode is active

### 2. Developer Overlay

Purpose:

- full scene authoring
- tile/object/zone/rule painting
- scene generation and repaint
- transitions and spawn editing
- validation and world graph review
- GUI layout editing

Rules:

- toggled with `F3`
- all major actions must be reachable by UI, not only by hotkey
- panels block painting underneath
- destructive edits push undo history
- keep this surface focused on live runtime iteration; broad authoring moves to the standalone Rust editor

### 3. Standalone Rust Editor

Purpose:

- full island/region graph authoring
- full scene authoring with large panels and inspectors
- scene create/delete/duplicate
- prefab/stamp authoring
- object metadata editing
- generator profile tuning
- validation report review
- asset and animation catalog review

Rules:

- owns dense editor workflows that do not fit inside the game overlay
- consumes `haven_core` and `haven_editor` APIs directly
- saves runtime-compatible world and graph data
- exposes structured validation sections from Rust

### 4. Web Editor

Purpose:

- prefab authoring
- content and asset metadata entry
- GUI layout preview
- rules, templates, and pack editing

Rules:

- should edit structured data, not replace the runtime scene painter
- should consume the same schema vocabulary as the runtime
- lower priority while the standalone Rust editor is being built

## Runtime Overlay Panel Contract

### Required Panels

1. HUD summary
2. Editor overlay
3. Inspector
4. Validation panel
5. World graph

### Layout Rules

- panel positions are anchor-relative
- panel drag uses snapped 16px grid coordinates
- panel layout persists beside the world save
- layout editing is a separate mode from content painting

## Authoring Layer Contract

Each scene is edited as independent layers:

1. base terrain
2. terrain mask / autotile variant layer
3. object layer
4. zone layer
5. transition layer
6. rule/spawner layer
7. front-occluder and effect markers

The editor must never treat these as a single merged paint target.

## Tool Workflows

### Tiles Tab

Actions:

- single paint
- brush paint
- erase
- eyedropper
- flood fill
- replace-by-selection
- rectangle copy/paste

Inspector fields:

- tile id
- family
- biome tags
- autotile group
- height compatibility
- rule binding

### Objects Tab

Actions:

- place object
- rotate object when supported
- move object
- erase object
- duplicate object

Inspector fields:

- object id
- footprint
- collision
- comfort/utility values
- sort pivot
- front-occluder flag
- placement restrictions

### Zones Tab

Actions:

- paint zone
- erase zone
- rectangle zone fill

Inspector fields:

- zone id
- room/region name
- validation state
- required furniture checklist

### Rules Tab

Actions:

- assign rule preset
- clear rule
- preview trigger bindings

Inspector fields:

- trigger set
- script/event name
- interactability
- traversal impact

### Map Tab

Actions:

- seed generation
- biome preset selection
- water level tuning
- cliff level tuning
- height raise/lower/smooth
- repaint from saved height field
- bridge stamp

Inspector fields:

- cell height
- terrain band
- shoreline/cliff status
- generator tags

### World Tab

Actions:

- scene switch
- scene create/delete/duplicate
- transition place/edit/delete
- spawn set
- validate world graph
- save/load

Inspector fields:

- scene id
- biome preset
- transition target
- spawn destination
- graph errors

## Edit Session Lifecycle

### Runtime Authoring

1. open relevant editor surface
2. choose tool and target layer
3. preview placement or brush result
4. apply edit
5. immediate validation feedback appears
6. undo/redo remains available
7. save writes world plus layout data

### Player Construction Session

1. enter construction mode
2. choose category and brush/item
3. preview valid/invalid placement
4. stage edits into a pending transaction
5. accept or revert entire transaction

## Required Validation Feedback

- unreachable transition
- missing scene spawn
- blocked guest room
- invalid furniture placement
- disconnected room zone
- impossible bridge or shoreline state
- orphaned rule/spawner markers

## Immediate Feature Additions Required

1. rectangle select/copy/paste
2. fill and replace tools
3. scene create/delete/duplicate
4. transition inspector editing
5. object property inspector
6. prefab/stamp placement
7. spawner/event marker editing
