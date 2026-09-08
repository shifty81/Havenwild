# Standalone Rust Editor Specification

Date: 2026-05-25

## Goal

Build a dedicated native Rust editor for Havenwild world authoring. This is separate from the in-game overlay and should become the primary tool for large-scale editing, validation, generation, and asset/world review.

The in-game overlay remains useful for quick live edits and testing inside the running game. It should not carry every editor workflow in a cramped viewport panel.

## Why This Exists

The current runtime overlay is cumbersome for broad authoring:

- not all controls fit comfortably in the panel
- world graph, scene properties, validation, and map tools compete for the same space
- dense workflows need tables, sidebars, inspectors, tabs, lists, and dockable panels
- island/region graph editing is too large for an overlay
- object, prefab, animation, and asset metadata editing need more room than the game HUD can give

## Editor Surfaces

### 1. Standalone Rust Editor

Primary use:

- island/region graph authoring
- scene creation, duplication, deletion, and metadata editing
- scene tile/object/zone/transition editing
- validation report review
- generator profile tuning
- prefab/stamp authoring
- object metadata editing
- character animation catalog review
- asset reference/catalog review
- save/load/export workflows

### 2. In-Game Overlay

Primary use:

- live scene touch-ups
- quick tile/object/zone paint
- transition testing
- in-context validation
- layout/panel testing
- runtime construction-mode prototyping

### 3. Browser Editor

Put on hold for now.

Future use:

- content pack forms
- asset catalog viewing
- lightweight previews
- mod/content metadata editing

## Recommended Stack

Use a native Rust app with shared editor/game crates.

Recommended UI candidates:

| Option | Notes |
|---|---|
| `egui` / `eframe` | Best fit for dense editor UI, dockable panels, inspectors, tables, and fast iteration. |
| `bevy_editor_pls` / Bevy tooling | Useful only if the runtime moves toward Bevy. Not the shortest path from current Macroquad. |
| Macroquad custom UI | Already in use, but poor fit for full desktop editor chrome. Keep for in-game overlay only. |

Preferred path:

```text
crates/haven_editor    native desktop editor shell
crates/haven_editor        shared editor model, validation, tools
crates/haven_core          world, scene, asset, graph, generation data
crates/haven_game          playable runtime and lightweight overlay
```

## System Ownership Rule

Every game system should follow the same ownership shape:

```text
haven_core data/rules -> haven_editor inspection/edit commands -> haven_game presentation/runtime
```

No major system should live only in the renderer, only in the web editor, or only in a debug overlay. If the player can see it, the Rust editor should be able to inspect it. If the Rust editor can mutate it, the mutation should go through shared core/editor APIs.

Current examples:

- region graph: shared core graph plus editor validation
- scene tilemap: shared core map plus editor inspection
- autotiling: shared core mask/neighborhood logic plus editor diagnostics and game presentation
- asset registry: shared lookup exists, editor review is still partial
- animation catalog: needs Rust-owned metadata and native preview
- world generation: seeded scene generation exists, profile editing is still partial
- collision/navigation: walkability exists, collision overlays and generated collider audits remain

## Initial Native Editor Layout

Use a desktop layout that is not constrained by the game viewport:

```text
Top menu / command bar
├─ File: New, Open, Save, Save As, Export
├─ Edit: Undo, Redo, Copy, Paste, Fill, Replace
├─ View: Region, Scene, Validation, Assets, Animation
└─ Generate: Regenerate Scene, Repaint Height, Validate All

Left sidebar
├─ Region graph tree
├─ Scene list
├─ Layer list
└─ Tool palette

Center viewport
├─ Island/region graph view
├─ Scene tilemap view
├─ Prefab/stamp preview
└─ Animation preview

Right inspector
├─ Selected region node
├─ Selected scene
├─ Selected tile/object/zone/transition
├─ Generator profile
└─ Validation details

Bottom panel
├─ Validation report
├─ Log/event stream
├─ Asset issues
└─ Save/export status
```

## Required MVP Capabilities

### World Model

- Load `EditorWorldModel::starter()`.
- Load/save world files from `WORKSPACE/saves/world.tworld`.
- Load/save island region graph data from `content/worldgen/island_region_graph.json` once serialization is added.
- Show combined validation from `EditorWorldModel::validation_report()`.

### Region Graph View

- Draw starter island landmass.
- Draw region nodes and links.
- Select nodes and links.
- Edit node label, kind, biome, scene binding, and normalized position.
- Edit link endpoints and link kind.
- Validate that graph links match world transitions.

### Scene View

- Show selected `SceneMap`.
- Pan/zoom.
- Toggle layers:
  - base terrain
  - height
  - objects
  - zones
  - transitions
  - validation overlays
- Paint tile/object/zone/transition layers.
- Use brush size, rectangle fill, replace, and erase.

### Inspector

- Show selected cell report from `inspect_scene_cell`.
- Show selected region report from `inspect_region_graph`.
- Show validation messages scoped to the selected graph node, scene, transition, or object.

### Validation

Use structured Rust validation sections:

- world scenes
- island region graph
- world/region alignment
- asset/catalog readiness
- animation/catalog readiness

Validation must be visible during authoring, not only on save.

## Near-Term Implementation Plan

### Phase 1: Rust Editor Model

Already started:

- `EditorWorldModel`
- `IslandRegionGraph`
- region graph validation
- graph/world alignment validation
- structured `EditorValidationReport`

Next:

- add serialization/deserialization for `IslandRegionGraph`
- add graph mutation commands
- add undoable edit commands
- add selection model
- add editor document model

### Phase 2: Native App Shell

Create:

```text
crates/haven_editor
```

Responsibilities:

- window/app lifecycle
- panels, menus, view state
- drawing region/scene previews
- invoking `haven_editor` operations
- reading/writing workspace files

### Phase 3: Region Graph Editor

First visual screen:

- island region graph canvas
- node list
- selected node inspector
- validation panel

This should come before full tilemap editing because it resolves the scale problem that the overlay cannot handle well.

### Phase 4: Scene Tilemap Editor

Move broad map authoring out of the in-game overlay:

- tiles
- objects
- zones
- transitions
- height overlays
- validation overlays

### Phase 5: Asset And Animation Review

Add reference/asset panels for:

- generated tile/object atlases
- imported top-down reference pack notes
- Universal Animation Library clip list
- future character animation schema

## What The In-Game Overlay Should Become

The overlay should be narrowed to:

- inspect current scene/cell
- quick paint with active tool
- quick transition/spawn testing
- validate current world
- save/load
- jump to scenes
- runtime construction-mode testing

Large panels such as world graph editing, object metadata, prefab authoring, and asset animation catalogs should move to the standalone Rust editor.

## Open Technical Decisions

- UI framework: likely `egui/eframe`.
- Serialization format: current line-based `.tworld` should remain readable; region graph can begin as JSON-like data but should eventually have Rust-owned read/write helpers.
- Asset loading: native editor should read from project-relative paths, not web HTTP endpoints.
- Preview renderer: standalone editor can share drawing logic concepts with `haven_game`, but should not depend on game loop state.
- Undo system: command-based edits should live in `haven_editor`, not only the app shell.

## Success Criteria

The standalone Rust editor is on target when:

- island graph editing is comfortable without game HUD constraints
- validation is structured, visible, and actionable
- scene authoring uses real Rust world data
- saves are compatible with the runtime
- the in-game overlay can shrink back to quick live editing
- the browser editor can remain a secondary structured-data viewer instead of the primary tool
