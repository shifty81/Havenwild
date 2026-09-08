# Animation Validation Rules V010

## Grid validation

```text
image dimensions match expected sheet size
cell size is 64x96 unless overridden
all frames fit inside image bounds
grid origin/padding/spacing valid
```

## Frame validation

```text
8 directions present
8 walk frames per direction present
no missing/blank frames unless intentionally tagged
no unexpected pixel spill into neighboring cells
transparent background valid
```

## Anchor validation

```text
root anchor exists
root anchor matches template
foot anchors exist
hand anchors exist
held item anchor exists for tool actions
shadow anchor exists
```

## Motion validation

```text
root jitter
foot sliding
head pop
torso pop
arm pop
leg length inconsistency
tool snap/jump
loop seam mismatch
```

## Layer validation

```text
layer matches target animation
layer matches target direction/frame count
layer does not redefine body proportions
layer follows correct sockets
layer has correct draw order/depth flags
```

## Promotion gates

```text
Draft
Grid Validated
Socket Validated
Motion Validated
Composite Validated
Gameplay Preview Approved
Production Ready
```
