# Forge GUI Portable Docking Stack

Havenwild should use the Forge GUI work as a portable editor/game UI layer instead of copying the visual style by hand.

## Required toolkit pieces

```text
ThemeTokens
PanelChrome
DockHost
DockPanel
FloatingPanel
TabWell
Splitter
ScrollArea
TreeView
SheetQueue
TileGrid
PropertyGrid
CommandBar
ToolRail
LayerRail
StatusPill
BadgeOverlay
ProblemList
CanvasViewport
CanvasOverlay
```

## Why it matters

The asset mapper, Havenwild native editor, ForgePY/Rust Forge, Cortex, and Ember all need the same panel grammar. A portable layer prevents every project from growing different debug-looking UI.

## Immediate Havenwild use

- Source atlas sheet stack
- right inspector
- layer rail
- tool rail
- problems/output dock
- coverage/checkmark badges
- floating canvas-hosted tool panels

## Later Ember use

The same contracts become EmberGuiCore and drive GameMaker-style infinite canvas panels.
