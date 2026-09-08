# Shared Command / Undo / Redo Spec

## Purpose

Main editor, in-game overlay, and future web tools should use the same command model.

## Command lifecycle

```text
Create command
Preview command
Validate command
Apply command
Record undo patch
Mark dirty
Emit events
Update runtime/editor views
```

## Command examples

```text
PaintTerrain
SetHeight
SetMoisture
PlaceObject
MoveObject
RotateObject
DeleteObject
AssignRoom
BuyParcel
ExpandSceneBoundary
AddWaterTile
PushWallOut
CreateTransition
EditCollisionMask
EditInteractionSocket
ImportAsset
EditPixelAsset
ValidateScene
SaveScene
```

## Undo model

Use reversible patches:

```text
before state
after state
affected document path
affected scene id
affected cells/objects
timestamp
tool source
```

## Command source

```text
MainEditor
InGameOverlay
WebEditor
RuntimeScript
Importer
ValidatorAutoFix
```

## Validation result

```text
valid
valid_with_warning
invalid
requires_confirmation
requires_rebuild
```
