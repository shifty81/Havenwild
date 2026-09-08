# Havenwild — V009 Editor Systems Master Spec

## Purpose

V009 turns the project from worldgen-only planning into a usable authoring/runtime toolchain.

It defines:

```text
main Rust editor
in-game overlay editor
web editor split
pixel art editor
runtime editing bridge
shared command system
asset metadata registry
validation registry
save/export pipeline
```

## Core rule

There should not be three separate editors writing incompatible data.

```text
Main Rust Editor
In-Game Overlay
Web Editors
        ↓
Shared Command + Data Spine
        ↓
Project / Scene / Asset Data
        ↓
Runtime + Validation + Save/Export
```

## Prior versions this builds on

```text
V005 = Terrain compositor
V006 = 2.5D runtime/object/collision concepts
V007 = Macro worldgen: mainland + 9 islands
V008 = Scene rectangles, streaming, seams, no-void borders
V009 = Editor systems and runtime authoring spine
```

## Editor split

### Main Rust Editor

The main Rust editor is the full authoring environment.

It owns:

```text
world layout
scene rectangles
terrain editing
pixel art editing
asset registry
object placement
collision/interaction editing
V005 compositor preview
V007/V008 preview modes
validation console
play-in-editor
export/build tools
```

### In-Game Overlay

The overlay is the game-safe, runtime-safe editor surface.

It owns:

```text
build mode
owned land / parcel preview
object placement
terrain edits on owned land
water placement on owned land
collision/path preview
inspect selected tile/object/NPC
construction queue preview
confirm/cancel workflow
```

### Web Editors

Web editors handle data-heavy tables and content databases.

They own:

```text
items
recipes
NPCs
dialogue
quests
staff traits
crop/fish tables
economy/pricing
localization
content audit dashboards
```

## Immediate implementation priority

```text
1. Project/scene data model
2. Shared EditorCommand bus
3. Main editor shell with docked panels
4. Pixel art editor vertical slice
5. In-game overlay shell
6. Runtime bridge for hot reload/scene edit preview
7. Validation console
```
