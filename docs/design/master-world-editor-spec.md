# Master World And Editor Specification

Date: 2026-05-24

## Product Definition

Havenwild Prototype is a standalone Rust tavern game with:

1. a playable runtime
2. a developer-facing in-game world editor
3. a future player-facing construction mode
4. a standalone native Rust editor for full authoring
5. a browser editor for lightweight content, prefab, and layout authoring

## Core World Model

- world is split into connected scenes
- scenes store tile, object, zone, rule, transition, and height data
- saves are source-like authoring artifacts, not opaque binaries
- scene generation and hand editing must both target the same save format

## Core Visual Model

- gameplay stays on an orthographic grid
- 2.5D look is created by:
  - height bands
  - cliff/front faces
  - y-sorted pivots
  - front occluders
  - backdrop/parallax layers

## Core Authoring Model

- player construction mode handles constrained room/decor workflows
- developer overlay handles quick live scene edits and runtime testing
- standalone Rust editor handles full world, graph, scene, prefab, validation, asset, and animation authoring
- web editor handles lightweight structured authoring and preview tasks

## Canonical Specs

The following files define the target system:

| Area | Canonical Spec |
| --- | --- |
| Repository structure | `docs/design/repository-architecture-spec.md` |
| Runtime GUI layout | `docs/design/gui-layout-grid-spec.md` |
| Runtime editor capabilities | `docs/design/in-game-editor-spec.md` |
| Standalone Rust editor | `docs/design/standalone-rust-editor-spec.md` |
| Non-isometric 2.5D presentation | `docs/design/non-isometric-2d5-spec.md` |
| Reference implementation benchmark | `docs/design/reference-game-benchmark.md` |
| Editor surface workflows | `docs/design/editor-workflows-spec.md` |
| Asset requirements | `docs/design/asset-requirements-spec.md` |
| Cave/dungeon generation | `docs/design/cave-dungeon-generator-spec.md` |
| World scene scope | `docs/design/world-scene-map.md` |

## Immediate Engineering Priorities

1. move shared editor/layout schemas into `haven_core`
2. create the standalone Rust editor app shell
3. add region graph editing from `EditorWorldModel`
4. add rectangle select/copy/paste and fill/replace tools
5. add scene create/delete/duplicate workflows
6. add richer object inspector data and prefab/stamp support
7. extend rendering with cliff fronts, occluders, and backdrop depth

## Asset Production Priorities

1. coast and shoreline family
2. mountain/highland/cliff family
3. cave wall/floor/support family
4. tavern interior object family
5. front-occluder and backdrop family
6. GUI panel skin and icon family

## Generator Priorities

1. stabilize overworld biome + height repaint workflow
2. add cave mouth template generation
3. add seeded cave room/corridor generation
4. add prefab special-room insertion
5. add resource/spawner validation

## Success Criteria

The project is on target when:

- world editing remains fast and grid-based
- layer ownership stays explicit
- GUI layouts save and restore cleanly
- terrain families can scale without enum chaos
- caves and overworld share one coherent authoring pipeline
- the game reads visually as 2.5D without becoming isometric
