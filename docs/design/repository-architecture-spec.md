# Repository Architecture Spec

## Goal

Keep the repository focused on a single active product:

- the **Rust game runtime**
- the **in-game debug/build overlay**
- the **web editor foundation**
- the **shared data and spec layer** that connects both editors to the game

Older side projects, plugin/mod-kit experiments, generated site output, and one-off root assets should not live in the active source layout.

## Active Top-Level Layout

```text
assets/                  art sources and generated prototype assets
content/                 shared game/editor content definitions
crates/
  haven_core/           world, tile, scene, serialization, metadata
  haven_game/           playable runtime, camera, render stack, live overlay
  haven_editor/         editor palette, inspection, validation, shared editor helpers
docs/
  design/                product and system specs
  engineering/           implementation notes
  docs/                  retained research notes that still inform the game
  sdk/                   only retained roadmap/reference material still relevant
tools/automation/                 active utility scripts only
web/
  editor/                browser editor foundation
WORKSPACE/               local save/export/temp files outside source
tools/build/Build.ps1                root run/build menu
Cargo.toml               Rust workspace entrypoint
README.md                current repo overview
```

## Ownership By Area

### `crates/haven_core`

- shared source of truth for:
  - tile taxonomy
  - scene structure
  - zone data
  - transitions
  - interaction rules
  - height/elevation storage
  - future GUI layout serialization types

### `crates/haven_game`

- owns the playable runtime
- owns rendering, camera behavior, faux-depth rules, and y-sorting
- owns the in-game overlay and live scene editing
- should consume data from `haven_core` rather than duplicating gameplay/editor rules

### `crates/haven_editor`

- owns editor-facing helpers only
- should not become a second runtime
- should stay focused on:
  - palette categories
  - inspector formatting
  - validation/reporting
  - future shared editor tools usable by both runtime and web surfaces

### `web/editor`

- owns browser-based authoring workflows
- should evolve into:
  - scene inspector/reference viewer
  - content/prefab editor
  - GUI layout preview/editor
  - data-entry surface for stamps, templates, and content packs

### `docs/design`

- canonical target behavior
- if code and docs disagree, this folder should be updated as part of the same task

## What Was Removed

The following categories were intentionally removed because they did not match the active product:

- old side-scroller/runtime experiments
- standalone Travellers Rest plugin/mod-kit source trees
- plugin build/install docs for deleted trees
- generated site/build folders
- stale snapshot archives and root-level throwaway visual artifacts

## Near-Term Structural Work

1. Move more editor-facing shared types from `haven_game` into `haven_core` where appropriate.
2. Define a shared schema for:
   - GUI layouts
   - scene templates
   - stamps/prefabs
   - content packs used by both the game and web editor
3. Replace remaining legacy naming in the web editor with Havenwild Prototype-specific concepts.
4. Keep generated content out of source folders unless it is intentionally committed as a lightweight prototype artifact.

## Reference Implementation Targets

This structure is meant to support:

- a **Stardew/Travellers Rest-style** scene-based world
- a **non-isometric 2.5D** render illusion built from orthographic tiles, height bands, occluders, and y-sorting
- a **live in-game editor** for scene shaping and layout tuning
- a **web editor** for slower authoring workflows that benefit from forms, previews, and broader data editing
