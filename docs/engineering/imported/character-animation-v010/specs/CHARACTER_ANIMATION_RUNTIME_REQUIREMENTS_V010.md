# Character Animation Runtime Requirements V010

## Runtime systems

```text
AnimationStateSystem
DirectionResolver
FrameClock
CharacterLayerCompositor
EquipmentAttachmentSystem
YSortRootAnchorSystem
AnimationEventSystem
AnimationValidationFallbackSystem
```

## Runtime state

```text
current animation
current direction
current frame
frame timer
active outfit layers
held item
tool action state
root position
socket pose data
```

## Animation events

Frames can emit events:

```text
footstep_left
footstep_right
tool_swing_start
tool_contact
serve_place_item
pickup_item
cast_fishing_line
mine_hit
chop_hit
water_pour
```

These events drive sound, particles, hit checks, and gameplay timing.

## Direction resolver

The runtime should map input vector or facing angle to 8 directions:

```text
N, NE, E, SE, S, SW, W, NW
```

## Anchor rule

Y-sort uses root anchor, not image top-left.
