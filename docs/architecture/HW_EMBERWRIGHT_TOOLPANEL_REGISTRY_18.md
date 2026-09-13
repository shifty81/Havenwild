# HW-EMBERWRIGHT-TOOLPANEL-REGISTRY-18

## Goal

This pass adds the first concrete ToolPanelRegistry seam for the Emberwright GUI conversion.

The permanent editor center remains:

```text
Canvas / Room Canvas / Game Canvas
```

Tools are normalized into stable panel identities that can later be docked, floated, hidden, or rendered as opaque canvas overlays without replacing the center canvas.

## Why this pass is intentionally small

The previous large cumulative GUI packages proved that broad full-file GUI rewrites are unsafe without local compile/runtime gates. This pass only adds a pure data/model seam and one module registration. It gives future passes a stable vocabulary before moving live panels.

## Registry groups

```text
Resource
  Resource Tree

Asset Lane
  Asset Browser
  Source Library
  Asset Authority
  Catalog Health
  Family Completeness
  Where Used
  License / Attribution
  Quarantine
  Atlas Assembly

Canvas Overlay
  Tool Rail
  Layer Rail
  Tile Palette
  PIE Control Strip

Inspector
  Inspector
  Properties
  Tool Properties

Sprite / Raster
  Sprite Tools
  Raster Layers
  Animation Timeline

Character
  Character Rig
  Paper Doll

Logic
  Logic Graph
  Node Palette

Sound
  Sound Timeline

Diagnostics / Cortex
  Output
  Problems
  Build
  Git
  Activity
  Cortex Chat
```

## Normalization rules

1. Canvas is not a ToolPanel.
2. Assets is not a replacement workspace long-term; it becomes an asset-lane panel group.
3. Pixel and Animation share the future RasterAuthoringCore instead of duplicating raster tools.
4. Tool Rail, Layer Rail, and Tile Palette are opaque canvas overlays.
5. PIE hides ordinary authoring panels and keeps only the PIE Control Strip visible.
6. Every panel has a stable key suitable for persisted layouts and future validation.

## Next pass

`HW-EMBERWRIGHT-PANEL-LAYOUT-19` should wire this registry into the current `workspace_shell` layout state without changing visual behavior yet.
