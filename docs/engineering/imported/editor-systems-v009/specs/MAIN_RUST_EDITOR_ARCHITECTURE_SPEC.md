# Main Rust Editor Architecture Spec

## Role

The main Rust editor is the full production tool. It should be the place where the entire game can be authored, previewed, validated, and exported.

## Primary panels

```text
Top Toolbar
World/Scene Viewport
Scene Graph / Outliner
Asset Browser
Inspector
Tool Shelf
Validation Console
Timeline / Animation Panel
Command History
Status Bar
```

## Core editor apps/tools

Keep the tool set focused:

```text
1. World Layout Tool
2. Scene Rectangle Tool
3. Terrain + Worldgen Tool
4. Pixel Art Editor
5. Object / Build Placement Tool
6. Collision + Interaction Tool
7. Character / Animation Tool
8. UI Skin Tool
9. Database Link / Content Browser
10. Validation / Export Tool
```

## Viewport requirements

```text
fixed orthographic 2.5D preview
tile grid
scene rectangle bounds
camera bounds preview
ownership overlay
collision overlay
interaction overlay
water/fishing overlay
height/slope/moisture/biome preview modes
V005 final terrain render preview
V006 Y-sort/object preview
```

## Project document model

The editor should open a project file that references:

```text
world layout
scene registry
asset registry
database registry
validation registry
save/export config
runtime launch config
```

## Docking and layout

The editor should support:

```text
dockable panels
tabbed panels
split panes
saved workspace layout
reset layout
fullscreen viewport
overlay preview mode
```

## Editor preview modes

```text
Final Render
Semantic Terrain
Height
Slope
Moisture
Temperature
Biome
Water Depth
Shore Profile
Ownership
Collision
Interaction
Pathfinding
Object Anchors
Scene Seams
Validation
```

## Play-in-editor

PIE should allow:

```text
launch current scene
launch from player start
reload changed assets
toggle editor overlay
pause/resume simulation
inspect runtime entities
return changes to editor document if allowed
```
