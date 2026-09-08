# Pixel Editor Animation Workflow V010

## Required animation editor panels

```text
Animation Sheet View
Frame Timeline
Direction Row List
Layer Stack
Socket/Anchor Overlay
Onion Skin Preview
Motion Arc Preview
Jitter Report
Conformance Report
Composite Preview
Gameplay Zoom Preview
```

## Editing workflow

```text
1. Open animation sheet.
2. Confirm grid: 64x96 cells.
3. Confirm direction/frame layout.
4. Load master motion template.
5. Show socket overlay.
6. Edit selected layer.
7. Preview against base body.
8. Run conformance validator.
9. Preview all 8 directions.
10. Promote only after validation passes.
```

## Atlas Grid Realignment Mode

Animation sheets also use the protected grid realignment system.

```text
Pixels stay fixed.
Logical grid moves.
Frame cell metadata updates.
Old grid shown faintly.
New grid shown brightly.
Apply requires confirmation.
Undo/redo supported.
```

## Jitter tools

The editor should expose:

```text
root jitter heatmap
head bob graph
hand motion arc
foot contact markers
held item anchor path
previous/next frame ghosting
loop seam checker
```
